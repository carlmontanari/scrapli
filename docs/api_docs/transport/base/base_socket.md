<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/sanitize.min.css" integrity="sha256-PK9q560IAAa6WVRRh76LtCaI8pjTJ2z11v0miyNNjrs=" crossorigin>
<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/typography.min.css" integrity="sha256-7l/o7C8jubJiy74VsKTidCy1yBkRtiUGbVkYBylBqUg=" crossorigin>
<link rel="stylesheet preload" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/styles/github.min.css" crossorigin>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/highlight.min.js" integrity="sha256-Uv3H6lx7dJmRfRvH8TH6kJD1TSK1aFcwgx+mdg3epi8=" crossorigin></script>
<script>window.addEventListener('DOMContentLoaded', () => hljs.initHighlighting())</script>















#Module scrapli.transport.base.base_socket

scrapli.transport.base.base_socket

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
"""scrapli.transport.base.base_socket"""
import socket
from typing import Optional, Set

from scrapli.exceptions import ScrapliConnectionNotOpened
from scrapli.logging import get_instance_logger


class Socket:
    def __init__(self, host: str, port: int, timeout: float):
        """
        Socket object

        Args:
            host: host to connect to
            port: port to connect to
            timeout: timeout in seconds

        Returns:
            None

        Raises:
            N/A

        """
        self.logger = get_instance_logger(instance_name="scrapli.socket", host=host, port=port)

        self.host = host
        self.port = port
        self.timeout = timeout

        self.sock: Optional[socket.socket] = None

    def __bool__(self) -> bool:
        """
        Magic bool method for Socket

        Args:
            N/A

        Returns:
            bool: True/False if socket is alive or not

        Raises:
            N/A

        """
        return self.isalive()

    def _connect(self, socket_address_families: Set["socket.AddressFamily"]) -> None:
        """
        Try to open socket to host using all possible address families

        It seems that very occasionally when resolving a hostname (i.e. localhost during functional
        tests against vrouter devices), a v6 address family will be the first af the socket
        getaddrinfo returns, in this case, because the qemu hostfwd is not listening on ::1, instead
        only listening on 127.0.0.1 the connection will fail. Presumably this is something that can
        happen in real life too... something gets resolved with a v6 address but is denying
        connections or just not listening on that ipv6 address. This little connect wrapper is
        intended to deal with these weird scenarios.

        Args:
            socket_address_families: set of address families available for the provided host
                really only should ever be v4 AND v6 if providing a hostname that resolves with
                both addresses, otherwise if you just provide a v4/v6 address it will just be a
                single address family for that type of address

        Returns:
            None

        Raises:
            ScrapliConnectionNotOpened: if socket refuses connection on all address families
            ScrapliConnectionNotOpened: if socket connection times out on all address families

        """
        for address_family_index, address_family in enumerate(socket_address_families, start=1):
            self.sock = socket.socket(address_family, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)

            try:
                self.sock.connect((self.host, self.port))
            except ConnectionRefusedError as exc:
                msg = (
                    f"connection refused trying to open socket to {self.host} on port {self.port} "
                    f"for address family {address_family.name}"
                )
                self.logger.warning(msg)
                if address_family_index == len(socket_address_families):
                    raise ScrapliConnectionNotOpened(msg) from exc
            except socket.timeout as exc:
                msg = (
                    f"timed out trying to open socket to {self.host} on port {self.port} for "
                    f"address family {address_family.name}"
                )
                self.logger.warning(msg)
                if address_family_index == len(socket_address_families):
                    raise ScrapliConnectionNotOpened(msg) from exc
            else:
                return

    def open(self) -> None:
        """
        Open underlying socket

        Args:
            N/A

        Returns:
            None

        Raises:
            ScrapliConnectionNotOpened: if cant fetch socket addr info

        """
        self.logger.debug(f"opening socket connection to '{self.host}' on port '{self.port}'")

        socket_address_families = None
        try:
            sock_info = socket.getaddrinfo(self.host, self.port)
            if sock_info:
                # get all possible address families for the provided host/port
                # should only ever be two... one for v4 and one for v6... i think/hope?! :)?
                socket_address_families = {sock[0] for sock in sock_info}
        except socket.gaierror:
            pass

        if not socket_address_families:
            # this will likely need to be clearer just dont know what failure scenarios exist for
            # this yet...
            raise ScrapliConnectionNotOpened("failed to determine socket address family for host")

        if not self.isalive():
            self._connect(socket_address_families=socket_address_families)

        self.logger.debug(
            f"opened socket connection to '{self.host}' on port '{self.port}' successfully"
        )

    def close(self) -> None:
        """
        Close socket

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        self.logger.debug(f"closing socket connection to '{self.host}' on port '{self.port}'")

        if self.isalive() and isinstance(self.sock, socket.socket):
            self.sock.close()

        self.logger.debug(
            f"closed socket connection to '{self.host}' on port '{self.port}' successfully"
        )

    def isalive(self) -> bool:
        """
        Check if socket is alive

        Args:
            N/A

        Returns:
            bool True/False if socket is alive

        Raises:
            N/A

        """
        try:
            if isinstance(self.sock, socket.socket):
                self.sock.send(b"")
                return True
        except OSError:
            self.logger.debug(f"Socket to host {self.host} is not alive")
            return False
        return False
        </code>
    </pre>
</details>




## Classes

### Socket


```text
Socket object

Args:
    host: host to connect to
    port: port to connect to
    timeout: timeout in seconds

Returns:
    None

Raises:
    N/A
```

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
class Socket:
    def __init__(self, host: str, port: int, timeout: float):
        """
        Socket object

        Args:
            host: host to connect to
            port: port to connect to
            timeout: timeout in seconds

        Returns:
            None

        Raises:
            N/A

        """
        self.logger = get_instance_logger(instance_name="scrapli.socket", host=host, port=port)

        self.host = host
        self.port = port
        self.timeout = timeout

        self.sock: Optional[socket.socket] = None

    def __bool__(self) -> bool:
        """
        Magic bool method for Socket

        Args:
            N/A

        Returns:
            bool: True/False if socket is alive or not

        Raises:
            N/A

        """
        return self.isalive()

    def _connect(self, socket_address_families: Set["socket.AddressFamily"]) -> None:
        """
        Try to open socket to host using all possible address families

        It seems that very occasionally when resolving a hostname (i.e. localhost during functional
        tests against vrouter devices), a v6 address family will be the first af the socket
        getaddrinfo returns, in this case, because the qemu hostfwd is not listening on ::1, instead
        only listening on 127.0.0.1 the connection will fail. Presumably this is something that can
        happen in real life too... something gets resolved with a v6 address but is denying
        connections or just not listening on that ipv6 address. This little connect wrapper is
        intended to deal with these weird scenarios.

        Args:
            socket_address_families: set of address families available for the provided host
                really only should ever be v4 AND v6 if providing a hostname that resolves with
                both addresses, otherwise if you just provide a v4/v6 address it will just be a
                single address family for that type of address

        Returns:
            None

        Raises:
            ScrapliConnectionNotOpened: if socket refuses connection on all address families
            ScrapliConnectionNotOpened: if socket connection times out on all address families

        """
        for address_family_index, address_family in enumerate(socket_address_families, start=1):
            self.sock = socket.socket(address_family, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)

            try:
                self.sock.connect((self.host, self.port))
            except ConnectionRefusedError as exc:
                msg = (
                    f"connection refused trying to open socket to {self.host} on port {self.port} "
                    f"for address family {address_family.name}"
                )
                self.logger.warning(msg)
                if address_family_index == len(socket_address_families):
                    raise ScrapliConnectionNotOpened(msg) from exc
            except socket.timeout as exc:
                msg = (
                    f"timed out trying to open socket to {self.host} on port {self.port} for "
                    f"address family {address_family.name}"
                )
                self.logger.warning(msg)
                if address_family_index == len(socket_address_families):
                    raise ScrapliConnectionNotOpened(msg) from exc
            else:
                return

    def open(self) -> None:
        """
        Open underlying socket

        Args:
            N/A

        Returns:
            None

        Raises:
            ScrapliConnectionNotOpened: if cant fetch socket addr info

        """
        self.logger.debug(f"opening socket connection to '{self.host}' on port '{self.port}'")

        socket_address_families = None
        try:
            sock_info = socket.getaddrinfo(self.host, self.port)
            if sock_info:
                # get all possible address families for the provided host/port
                # should only ever be two... one for v4 and one for v6... i think/hope?! :)?
                socket_address_families = {sock[0] for sock in sock_info}
        except socket.gaierror:
            pass

        if not socket_address_families:
            # this will likely need to be clearer just dont know what failure scenarios exist for
            # this yet...
            raise ScrapliConnectionNotOpened("failed to determine socket address family for host")

        if not self.isalive():
            self._connect(socket_address_families=socket_address_families)

        self.logger.debug(
            f"opened socket connection to '{self.host}' on port '{self.port}' successfully"
        )

    def close(self) -> None:
        """
        Close socket

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        self.logger.debug(f"closing socket connection to '{self.host}' on port '{self.port}'")

        if self.isalive() and isinstance(self.sock, socket.socket):
            self.sock.close()

        self.logger.debug(
            f"closed socket connection to '{self.host}' on port '{self.port}' successfully"
        )

    def isalive(self) -> bool:
        """
        Check if socket is alive

        Args:
            N/A

        Returns:
            bool True/False if socket is alive

        Raises:
            N/A

        """
        try:
            if isinstance(self.sock, socket.socket):
                self.sock.send(b"")
                return True
        except OSError:
            self.logger.debug(f"Socket to host {self.host} is not alive")
            return False
        return False
        </code>
    </pre>
</details>


#### Methods

    

##### close
`close(self) ‑> None`

```text
Close socket

Args:
    N/A

Returns:
    None

Raises:
    N/A
```



    

##### isalive
`isalive(self) ‑> bool`

```text
Check if socket is alive

Args:
    N/A

Returns:
    bool True/False if socket is alive

Raises:
    N/A
```



    

##### open
`open(self) ‑> None`

```text
Open underlying socket

Args:
    N/A

Returns:
    None

Raises:
    ScrapliConnectionNotOpened: if cant fetch socket addr info
```