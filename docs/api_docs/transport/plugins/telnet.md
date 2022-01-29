<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/sanitize.min.css" integrity="sha256-PK9q560IAAa6WVRRh76LtCaI8pjTJ2z11v0miyNNjrs=" crossorigin>
<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/typography.min.css" integrity="sha256-7l/o7C8jubJiy74VsKTidCy1yBkRtiUGbVkYBylBqUg=" crossorigin>
<link rel="stylesheet preload" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/styles/github.min.css" crossorigin>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/highlight.min.js" integrity="sha256-Uv3H6lx7dJmRfRvH8TH6kJD1TSK1aFcwgx+mdg3epi8=" crossorigin></script>
<script>window.addEventListener('DOMContentLoaded', () => hljs.initHighlighting())</script>















#Module scrapli.transport.plugins.telnet.transport

scrapli.transport.plugins.telnet.transport

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
"""scrapli.transport.plugins.telnet.transport"""
from dataclasses import dataclass
from telnetlib import Telnet
from typing import Optional

from scrapli.decorators import TransportTimeout
from scrapli.exceptions import ScrapliConnectionError, ScrapliConnectionNotOpened
from scrapli.transport.base import BasePluginTransportArgs, BaseTransportArgs, Transport


@dataclass()
class PluginTransportArgs(BasePluginTransportArgs):
    pass


class ScrapliTelnet(Telnet):
    def __init__(self, host: str, port: int, timeout: float) -> None:
        """
        ScrapliTelnet class for typing purposes

        Args:
            host: string of host
            port: integer port to connect to
            timeout: timeout value in seconds

        Returns:
            None

        Raises:
            N/A

        """
        self.eof: bool
        self.timeout: float

        super().__init__(host, port, int(timeout))


class TelnetTransport(Transport):
    def __init__(
        self, base_transport_args: BaseTransportArgs, plugin_transport_args: PluginTransportArgs
    ) -> None:
        super().__init__(base_transport_args=base_transport_args)
        self.plugin_transport_args = plugin_transport_args

        self.session: Optional[ScrapliTelnet] = None

    def open(self) -> None:
        self._pre_open_closing_log(closing=False)

        # establish session with "socket" timeout, then reset timeout to "transport" timeout
        try:
            self.session = ScrapliTelnet(
                host=self._base_transport_args.host,
                port=self._base_transport_args.port,
                timeout=self._base_transport_args.timeout_socket,
            )
            self.session.timeout = self._base_transport_args.timeout_transport
        except ConnectionError as exc:
            msg = f"Failed to open telnet session to host {self._base_transport_args.host}"
            if "connection refused" in str(exc).lower():
                msg = (
                    f"Failed to open telnet session to host {self._base_transport_args.host}, "
                    "connection refused"
                )
            raise ScrapliConnectionError(msg) from exc

        self._post_open_closing_log(closing=False)

    def close(self) -> None:
        self._pre_open_closing_log(closing=True)

        if self.session:
            self.session.close()

        self.session = None

        self._post_open_closing_log(closing=True)

    def isalive(self) -> bool:
        if not self.session:
            return False
        return not self.session.eof

    @TransportTimeout("timed out reading from transport")
    def read(self) -> bytes:
        if not self.session:
            raise ScrapliConnectionNotOpened
        try:
            buf = self.session.read_eager()
        except Exception as exc:
            raise ScrapliConnectionError(
                "encountered EOF reading from transport; typically means the device closed the "
                "connection"
            ) from exc
        return buf

    def write(self, channel_input: bytes) -> None:
        if not self.session:
            raise ScrapliConnectionNotOpened
        self.session.write(channel_input)
        </code>
    </pre>
</details>




## Classes

### PluginTransportArgs


```text
PluginTransportArgs()
```

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
@dataclass()
class PluginTransportArgs(BasePluginTransportArgs):
    pass
        </code>
    </pre>
</details>


#### Ancestors (in MRO)
- scrapli.transport.base.base_transport.BasePluginTransportArgs



### ScrapliTelnet


```text
Telnet interface class.

An instance of this class represents a connection to a telnet
server.  The instance is initially not connected; the open()
method must be used to establish a connection.  Alternatively, the
host name and optional port number can be passed to the
constructor, too.

Don't try to reopen an already connected instance.

This class has many read_*() methods.  Note that some of them
raise EOFError when the end of the connection is read, because
they can return an empty string for other reasons.  See the
individual doc strings.

read_until(expected, [timeout])
    Read until the expected string has been seen, or a timeout is
    hit (default is no timeout); may block.

read_all()
    Read all data until EOF; may block.

read_some()
    Read at least one byte or EOF; may block.

read_very_eager()
    Read all data available already queued or on the socket,
    without blocking.

read_eager()
    Read either data already queued or some data available on the
    socket, without blocking.

read_lazy()
    Read all data in the raw queue (processing it first), without
    doing any socket I/O.

read_very_lazy()
    Reads all data in the cooked queue, without doing any socket
    I/O.

read_sb_data()
    Reads available data between SB ... SE sequence. Don't block.

set_option_negotiation_callback(callback)
    Each time a telnet option is read on the input flow, this callback
    (if set) is called with the following parameters :
    callback(telnet socket, command, option)
        option will be chr(0) when there is no option.
    No other action is done afterwards by telnetlib.

ScrapliTelnet class for typing purposes

Args:
    host: string of host
    port: integer port to connect to
    timeout: timeout value in seconds

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
class ScrapliTelnet(Telnet):
    def __init__(self, host: str, port: int, timeout: float) -> None:
        """
        ScrapliTelnet class for typing purposes

        Args:
            host: string of host
            port: integer port to connect to
            timeout: timeout value in seconds

        Returns:
            None

        Raises:
            N/A

        """
        self.eof: bool
        self.timeout: float

        super().__init__(host, port, int(timeout))
        </code>
    </pre>
</details>


#### Ancestors (in MRO)
- telnetlib.Telnet



### TelnetTransport


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
class TelnetTransport(Transport):
    def __init__(
        self, base_transport_args: BaseTransportArgs, plugin_transport_args: PluginTransportArgs
    ) -> None:
        super().__init__(base_transport_args=base_transport_args)
        self.plugin_transport_args = plugin_transport_args

        self.session: Optional[ScrapliTelnet] = None

    def open(self) -> None:
        self._pre_open_closing_log(closing=False)

        # establish session with "socket" timeout, then reset timeout to "transport" timeout
        try:
            self.session = ScrapliTelnet(
                host=self._base_transport_args.host,
                port=self._base_transport_args.port,
                timeout=self._base_transport_args.timeout_socket,
            )
            self.session.timeout = self._base_transport_args.timeout_transport
        except ConnectionError as exc:
            msg = f"Failed to open telnet session to host {self._base_transport_args.host}"
            if "connection refused" in str(exc).lower():
                msg = (
                    f"Failed to open telnet session to host {self._base_transport_args.host}, "
                    "connection refused"
                )
            raise ScrapliConnectionError(msg) from exc

        self._post_open_closing_log(closing=False)

    def close(self) -> None:
        self._pre_open_closing_log(closing=True)

        if self.session:
            self.session.close()

        self.session = None

        self._post_open_closing_log(closing=True)

    def isalive(self) -> bool:
        if not self.session:
            return False
        return not self.session.eof

    @TransportTimeout("timed out reading from transport")
    def read(self) -> bytes:
        if not self.session:
            raise ScrapliConnectionNotOpened
        try:
            buf = self.session.read_eager()
        except Exception as exc:
            raise ScrapliConnectionError(
                "encountered EOF reading from transport; typically means the device closed the "
                "connection"
            ) from exc
        return buf

    def write(self, channel_input: bytes) -> None:
        if not self.session:
            raise ScrapliConnectionNotOpened
        self.session.write(channel_input)
        </code>
    </pre>
</details>


#### Ancestors (in MRO)
- scrapli.transport.base.sync_transport.Transport
- scrapli.transport.base.base_transport.BaseTransport
- abc.ABC