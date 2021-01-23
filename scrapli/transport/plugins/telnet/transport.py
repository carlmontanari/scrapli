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

        self.username_prompt: str = "username:"
        self.password_prompt: str = "password:"

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
