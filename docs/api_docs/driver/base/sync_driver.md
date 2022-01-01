<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/sanitize.min.css" integrity="sha256-PK9q560IAAa6WVRRh76LtCaI8pjTJ2z11v0miyNNjrs=" crossorigin>
<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/typography.min.css" integrity="sha256-7l/o7C8jubJiy74VsKTidCy1yBkRtiUGbVkYBylBqUg=" crossorigin>
<link rel="stylesheet preload" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/styles/github.min.css" crossorigin>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/highlight.min.js" integrity="sha256-Uv3H6lx7dJmRfRvH8TH6kJD1TSK1aFcwgx+mdg3epi8=" crossorigin></script>
<script>window.addEventListener('DOMContentLoaded', () => hljs.initHighlighting())</script>















#Module scrapli.driver.base.sync_driver

scrapli.driver.base.sync_driver

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
"""scrapli.driver.base.sync_driver"""
from types import TracebackType
from typing import Any, Optional, Type

from scrapli.channel import Channel
from scrapli.driver.base.base_driver import BaseDriver
from scrapli.exceptions import ScrapliValueError
from scrapli.transport import ASYNCIO_TRANSPORTS


class Driver(BaseDriver):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

        if self.transport_name in ASYNCIO_TRANSPORTS:
            raise ScrapliValueError(
                "provided transport is *not* an sync transport, must use an sync transport with"
                " the (sync)Driver(s)"
            )

        self.channel = Channel(
            transport=self.transport,
            base_channel_args=self._base_channel_args,
        )

    def __enter__(self) -> "Driver":
        """
        Enter method for context manager

        Args:
            N/A

        Returns:
            Driver: opened Driver object

        Raises:
            N/A

        """
        self.open()
        return self

    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """
        Exit method to cleanup for context manager

        Args:
            exception_type: exception type being raised
            exception_value: message from exception being raised
            traceback: traceback from exception being raised

        Returns:
            None

        Raises:
            N/A

        """
        self.close()

    def open(self) -> None:
        """
        Open the scrapli connection

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        self._pre_open_closing_log(closing=False)

        self.transport.open()
        self.channel.open()

        if self.transport_name in ("system",) and not self.auth_bypass:
            self.channel.channel_authenticate_ssh(
                auth_password=self.auth_password,
                auth_private_key_passphrase=self.auth_private_key_passphrase,
            )
        if (
            self.transport_name
            in (
                "telnet",
                "asynctelnet",
            )
            and not self.auth_bypass
        ):
            self.channel.channel_authenticate_telnet(
                auth_username=self.auth_username, auth_password=self.auth_password
            )

        if self.on_open:
            self.on_open(self)

        self._post_open_closing_log(closing=False)

    def close(self) -> None:
        """
        Close the scrapli connection

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        self._pre_open_closing_log(closing=True)

        if self.on_close:
            self.on_close(self)

        self.transport.close()
        self.channel.close()

        self._post_open_closing_log(closing=True)

    def commandeer(self, conn: "Driver", execute_on_open: bool = True) -> None:
        """
        Commandeer an existing connection

        Used to "take over" or "commandeer" a connection. This method accepts a second scrapli conn
        object and "steals" the transport from this connection and uses it for the current instance.
        The primary reason you would want this is to use a `GenericDriver` to connect to a console
        server and then to "commandeer" that connection and convert it to a "normal" network driver
        connection type (i.e. Junos, EOS, etc.) once connected to the network device (via the
        console server).

        Right now closing the connection that "commandeers" the initial connection will *also close
        the original connection* -- this is because we are re-using the transport in this new conn.
        In the future perhaps this will change to *not* close the original connection so users can
        handle any type of cleanup operations that need to happen on the original connection.
        Alternatively, you can simply continue using the "original" connection to close things for
        yourself or do any type of clean up work (just dont close the commandeering connection!).

        Args:
            conn: connection to commandeer
            execute_on_open: execute the `on_open` function of the current object once the existing
                connection has been commandeered

        Returns:
            None

        Raises:
            N/A

        """
        original_logger = conn.logger
        original_transport = conn.transport
        original_transport_logger = conn.transport.logger
        original_channel_logger = conn.channel.logger
        original_channel_channel_log = conn.channel.channel_log

        self.logger = original_logger
        self.channel.logger = original_channel_logger
        self.channel.transport = original_transport
        self.transport = original_transport
        self.transport.logger = original_transport_logger

        if original_channel_channel_log is not None:
            # if the original connection had a channel log we also commandeer that; note that when
            # the new connection is closed this will also close the channel log; see docstring.
            self.channel.channel_log = original_channel_channel_log

        if execute_on_open and self.on_open is not None:
            self.on_open(self)
        </code>
    </pre>
</details>




## Classes

### Driver


```text
BaseDriver Object

BaseDriver is the root for all Scrapli driver classes. The synchronous and asyncio driver
base driver classes can be used to provide a semi-pexpect like experience over top of
whatever transport a user prefers. Generally, however, the base driver classes should not be
used directly. It is best to use the GenericDriver (or AsyncGenericDriver) or NetworkDriver
(or AsyncNetworkDriver) sub-classes of the base drivers.

Args:
    host: host ip/name to connect to
    port: port to connect to
    auth_username: username for authentication
    auth_private_key: path to private key for authentication
    auth_private_key_passphrase: passphrase for decrypting ssh key if necessary
    auth_password: password for authentication
    auth_strict_key: strict host checking or not
    auth_bypass: bypass "in channel" authentication -- only supported with telnet,
        asynctelnet, and system transport plugins
    timeout_socket: timeout for establishing socket/initial connection in seconds
    timeout_transport: timeout for ssh|telnet transport in seconds
    timeout_ops: timeout for ssh channel operations
    comms_prompt_pattern: raw string regex pattern -- preferably use `^` and `$` anchors!
        this is the single most important attribute here! if this does not match a prompt,
        scrapli will not work!
        IMPORTANT: regex search uses multi-line + case insensitive flags. multi-line allows
        for highly reliably matching for prompts however we do NOT strip trailing whitespace
        for each line, so be sure to add '\\s?' or similar if your device needs that. This
        should be mostly sorted for you if using network drivers (i.e. `IOSXEDriver`).
        Lastly, the case insensitive is just a convenience factor so i can be lazy.
    comms_return_char: character to use to send returns to host
    ssh_config_file: string to path for ssh config file, True to use default ssh config file
        or False to ignore default ssh config file
    ssh_known_hosts_file: string to path for ssh known hosts file, True to use default known
        file locations. Only applicable/needed if `auth_strict_key` is set to True
    on_init: callable that accepts the class instance as its only argument. this callable,
        if provided, is executed as the last step of object instantiation -- its purpose is
        primarily to provide a mechanism for scrapli community platforms to have an easy way
        to modify initialization arguments/object attributes without needing to create a
        class that extends the driver, instead allowing the community platforms to simply
        build from the GenericDriver or NetworkDriver classes, and pass this callable to do
        things such as appending to a username (looking at you RouterOS!!). Note that this
        is *always* a synchronous function (even for asyncio drivers)!
    on_open: callable that accepts the class instance as its only argument. this callable,
        if provided, is executed immediately after authentication is completed. Common use
        cases for this callable would be to disable paging or accept any kind of banner
        message that prompts a user upon connection
    on_close: callable that accepts the class instance as its only argument. this callable,
        if provided, is executed immediately prior to closing the underlying transport.
        Common use cases for this callable would be to save configurations prior to exiting,
        or to logout properly to free up vtys or similar
    transport: name of the transport plugin to use for the actual telnet/ssh/netconf
        connection. Available "core" transports are:
            - system
            - telnet
            - asynctelnet
            - ssh2
            - paramiko
            - asyncssh
        Please see relevant transport plugin section for details. Additionally third party
        transport plugins may be available.
    transport_options: dictionary of options to pass to selected transport class; see
        docs for given transport class for details of what to pass here
    channel_lock: True/False to lock the channel (threading.Lock/asyncio.Lock) during
        any channel operations, defaults to False
    channel_log: True/False or a string path to a file of where to write out channel logs --
        these are not "logs" in the normal logging module sense, but only the output that is
        read from the channel. In other words, the output of the channel log should look
        similar to what you would see as a human connecting to a device
    channel_log_mode: "write"|"append", all other values will raise ValueError,
        does what it sounds like it should by setting the channel log to the provided mode
    logging_uid: unique identifier (string) to associate to log messages; useful if you have
        multiple connections to the same device (i.e. one console, one ssh, or one to each
        supervisor module, etc.)

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
class Driver(BaseDriver):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

        if self.transport_name in ASYNCIO_TRANSPORTS:
            raise ScrapliValueError(
                "provided transport is *not* an sync transport, must use an sync transport with"
                " the (sync)Driver(s)"
            )

        self.channel = Channel(
            transport=self.transport,
            base_channel_args=self._base_channel_args,
        )

    def __enter__(self) -> "Driver":
        """
        Enter method for context manager

        Args:
            N/A

        Returns:
            Driver: opened Driver object

        Raises:
            N/A

        """
        self.open()
        return self

    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """
        Exit method to cleanup for context manager

        Args:
            exception_type: exception type being raised
            exception_value: message from exception being raised
            traceback: traceback from exception being raised

        Returns:
            None

        Raises:
            N/A

        """
        self.close()

    def open(self) -> None:
        """
        Open the scrapli connection

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        self._pre_open_closing_log(closing=False)

        self.transport.open()
        self.channel.open()

        if self.transport_name in ("system",) and not self.auth_bypass:
            self.channel.channel_authenticate_ssh(
                auth_password=self.auth_password,
                auth_private_key_passphrase=self.auth_private_key_passphrase,
            )
        if (
            self.transport_name
            in (
                "telnet",
                "asynctelnet",
            )
            and not self.auth_bypass
        ):
            self.channel.channel_authenticate_telnet(
                auth_username=self.auth_username, auth_password=self.auth_password
            )

        if self.on_open:
            self.on_open(self)

        self._post_open_closing_log(closing=False)

    def close(self) -> None:
        """
        Close the scrapli connection

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        self._pre_open_closing_log(closing=True)

        if self.on_close:
            self.on_close(self)

        self.transport.close()
        self.channel.close()

        self._post_open_closing_log(closing=True)

    def commandeer(self, conn: "Driver", execute_on_open: bool = True) -> None:
        """
        Commandeer an existing connection

        Used to "take over" or "commandeer" a connection. This method accepts a second scrapli conn
        object and "steals" the transport from this connection and uses it for the current instance.
        The primary reason you would want this is to use a `GenericDriver` to connect to a console
        server and then to "commandeer" that connection and convert it to a "normal" network driver
        connection type (i.e. Junos, EOS, etc.) once connected to the network device (via the
        console server).

        Right now closing the connection that "commandeers" the initial connection will *also close
        the original connection* -- this is because we are re-using the transport in this new conn.
        In the future perhaps this will change to *not* close the original connection so users can
        handle any type of cleanup operations that need to happen on the original connection.
        Alternatively, you can simply continue using the "original" connection to close things for
        yourself or do any type of clean up work (just dont close the commandeering connection!).

        Args:
            conn: connection to commandeer
            execute_on_open: execute the `on_open` function of the current object once the existing
                connection has been commandeered

        Returns:
            None

        Raises:
            N/A

        """
        original_logger = conn.logger
        original_transport = conn.transport
        original_transport_logger = conn.transport.logger
        original_channel_logger = conn.channel.logger
        original_channel_channel_log = conn.channel.channel_log

        self.logger = original_logger
        self.channel.logger = original_channel_logger
        self.channel.transport = original_transport
        self.transport = original_transport
        self.transport.logger = original_transport_logger

        if original_channel_channel_log is not None:
            # if the original connection had a channel log we also commandeer that; note that when
            # the new connection is closed this will also close the channel log; see docstring.
            self.channel.channel_log = original_channel_channel_log

        if execute_on_open and self.on_open is not None:
            self.on_open(self)
        </code>
    </pre>
</details>


#### Ancestors (in MRO)
- scrapli.driver.base.base_driver.BaseDriver
#### Descendants
- scrapli.driver.generic.sync_driver.GenericDriver
#### Methods

    

##### close
`close(self) ‑> None`

```text
Close the scrapli connection

Args:
    N/A

Returns:
    None

Raises:
    N/A
```



    

##### commandeer
`commandeer(self, conn: Driver, execute_on_open: bool = True) ‑> None`

```text
Commandeer an existing connection

Used to "take over" or "commandeer" a connection. This method accepts a second scrapli conn
object and "steals" the transport from this connection and uses it for the current instance.
The primary reason you would want this is to use a `GenericDriver` to connect to a console
server and then to "commandeer" that connection and convert it to a "normal" network driver
connection type (i.e. Junos, EOS, etc.) once connected to the network device (via the
console server).

Right now closing the connection that "commandeers" the initial connection will *also close
the original connection* -- this is because we are re-using the transport in this new conn.
In the future perhaps this will change to *not* close the original connection so users can
handle any type of cleanup operations that need to happen on the original connection.
Alternatively, you can simply continue using the "original" connection to close things for
yourself or do any type of clean up work (just dont close the commandeering connection!).

Args:
    conn: connection to commandeer
    execute_on_open: execute the `on_open` function of the current object once the existing
        connection has been commandeered

Returns:
    None

Raises:
    N/A
```



    

##### open
`open(self) ‑> None`

```text
Open the scrapli connection

Args:
    N/A

Returns:
    None

Raises:
    N/A
```