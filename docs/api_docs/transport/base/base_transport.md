<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/sanitize.min.css" integrity="sha256-PK9q560IAAa6WVRRh76LtCaI8pjTJ2z11v0miyNNjrs=" crossorigin>
<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/typography.min.css" integrity="sha256-7l/o7C8jubJiy74VsKTidCy1yBkRtiUGbVkYBylBqUg=" crossorigin>
<link rel="stylesheet preload" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/styles/github.min.css" crossorigin>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/highlight.min.js" integrity="sha256-Uv3H6lx7dJmRfRvH8TH6kJD1TSK1aFcwgx+mdg3epi8=" crossorigin></script>
<script>window.addEventListener('DOMContentLoaded', () => hljs.initHighlighting())</script>















#Module scrapli.transport.base.base_transport

scrapli.transport.base_transport

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
"""scrapli.transport.base_transport"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict

from scrapli.logging import get_instance_logger


@dataclass()
class BaseTransportArgs:
    transport_options: Dict[str, Any]
    host: str
    port: int = 22
    timeout_socket: float = 10.0
    timeout_transport: float = 30.0
    logging_uid: str = ""


@dataclass()
class BasePluginTransportArgs:
    pass


class BaseTransport(ABC):
    def __init__(self, base_transport_args: BaseTransportArgs) -> None:
        """
        Scrapli's transport base class

        Args:
            base_transport_args: base transport args dataclass

        Returns:
            None

        Raises:
            N/A

        """
        self._base_transport_args = base_transport_args

        self.logger = get_instance_logger(
            instance_name="scrapli.transport",
            host=self._base_transport_args.host,
            port=self._base_transport_args.port,
            uid=self._base_transport_args.logging_uid,
        )

    @abstractmethod
    def close(self) -> None:
        """
        Close the transport session

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """

    @abstractmethod
    def write(self, channel_input: bytes) -> None:
        """
        Write bytes into the transport session

        Args:
            channel_input: bytes to write to transport session

        Returns:
            None

        Raises:
            N/A

        """

    @abstractmethod
    def isalive(self) -> bool:
        """
        Check if transport is alive

        Args:
            N/A

        Returns:
            bool: True/False if transport is alive

        Raises:
            N/A

        """

    def _pre_open_closing_log(self, closing: bool = False) -> None:
        """
        Emit "pre open" log message for consistency between transports

        Args:
            closing: bool indicating if message is for closing not opening

        Returns:
            None

        Raises:
            N/A

        """
        operation = "closing" if closing else "opening"

        self.logger.debug(
            f"{operation} transport connection to '{self._base_transport_args.host}' on port "
            f"'{self._base_transport_args.port}'"
        )

    def _post_open_closing_log(self, closing: bool = False) -> None:
        """
        Emit "post open" log message for consistency between transports

        Args:
            closing: bool indicating if message is for closing not opening

        Returns:
            None

        Raises:
            N/A

        """
        operation = "closed" if closing else "opened"

        self.logger.debug(
            f"transport connection to '{self._base_transport_args.host}' on port "
            f"'{self._base_transport_args.port}' {operation} successfully"
        )
        </code>
    </pre>
</details>




## Classes

### BasePluginTransportArgs


```text
BasePluginTransportArgs()
```

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
@dataclass()
class BasePluginTransportArgs:
    pass
        </code>
    </pre>
</details>


#### Descendants
- scrapli.transport.plugins.asyncssh.transport.PluginTransportArgs
- scrapli.transport.plugins.asynctelnet.transport.PluginTransportArgs
- scrapli.transport.plugins.paramiko.transport.PluginTransportArgs
- scrapli.transport.plugins.ssh2.transport.PluginTransportArgs
- scrapli.transport.plugins.system.transport.PluginTransportArgs
- scrapli.transport.plugins.telnet.transport.PluginTransportArgs



### BaseTransport


```text
Helper class that provides a standard way to create an ABC using
inheritance.

Scrapli's transport base class

Args:
    base_transport_args: base transport args dataclass

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
class BaseTransport(ABC):
    def __init__(self, base_transport_args: BaseTransportArgs) -> None:
        """
        Scrapli's transport base class

        Args:
            base_transport_args: base transport args dataclass

        Returns:
            None

        Raises:
            N/A

        """
        self._base_transport_args = base_transport_args

        self.logger = get_instance_logger(
            instance_name="scrapli.transport",
            host=self._base_transport_args.host,
            port=self._base_transport_args.port,
            uid=self._base_transport_args.logging_uid,
        )

    @abstractmethod
    def close(self) -> None:
        """
        Close the transport session

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """

    @abstractmethod
    def write(self, channel_input: bytes) -> None:
        """
        Write bytes into the transport session

        Args:
            channel_input: bytes to write to transport session

        Returns:
            None

        Raises:
            N/A

        """

    @abstractmethod
    def isalive(self) -> bool:
        """
        Check if transport is alive

        Args:
            N/A

        Returns:
            bool: True/False if transport is alive

        Raises:
            N/A

        """

    def _pre_open_closing_log(self, closing: bool = False) -> None:
        """
        Emit "pre open" log message for consistency between transports

        Args:
            closing: bool indicating if message is for closing not opening

        Returns:
            None

        Raises:
            N/A

        """
        operation = "closing" if closing else "opening"

        self.logger.debug(
            f"{operation} transport connection to '{self._base_transport_args.host}' on port "
            f"'{self._base_transport_args.port}'"
        )

    def _post_open_closing_log(self, closing: bool = False) -> None:
        """
        Emit "post open" log message for consistency between transports

        Args:
            closing: bool indicating if message is for closing not opening

        Returns:
            None

        Raises:
            N/A

        """
        operation = "closed" if closing else "opened"

        self.logger.debug(
            f"transport connection to '{self._base_transport_args.host}' on port "
            f"'{self._base_transport_args.port}' {operation} successfully"
        )
        </code>
    </pre>
</details>


#### Ancestors (in MRO)
- abc.ABC
#### Descendants
- scrapli.transport.base.async_transport.AsyncTransport
- scrapli.transport.base.sync_transport.Transport
#### Methods

    

##### close
`close(self) ‑> None`

```text
Close the transport session

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
Check if transport is alive

Args:
    N/A

Returns:
    bool: True/False if transport is alive

Raises:
    N/A
```



    

##### write
`write(self, channel_input: bytes) ‑> None`

```text
Write bytes into the transport session

Args:
    channel_input: bytes to write to transport session

Returns:
    None

Raises:
    N/A
```





### BaseTransportArgs


```text
BaseTransportArgs(transport_options: Dict[str, Any], host: str, port: int = 22, timeout_socket: float = 10.0, timeout_transport: float = 30.0, logging_uid: str = '')
```

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
@dataclass()
class BaseTransportArgs:
    transport_options: Dict[str, Any]
    host: str
    port: int = 22
    timeout_socket: float = 10.0
    timeout_transport: float = 30.0
    logging_uid: str = ""
        </code>
    </pre>
</details>


#### Class variables

    
`host: str`




    
`logging_uid: str`




    
`port: int`




    
`timeout_socket: float`




    
`timeout_transport: float`




    
`transport_options: Dict[str, Any]`