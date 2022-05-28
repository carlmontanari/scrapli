"""scrapli.transport.plugins.telnet.transport"""
from dataclasses import dataclass
from typing import Optional

from scrapli.decorators import timeout_wrapper
from scrapli.exceptions import ScrapliConnectionError, ScrapliConnectionNotOpened
from scrapli.transport.base import BasePluginTransportArgs, BaseTransportArgs, Transport
from scrapli.transport.base.base_socket import Socket
from scrapli.transport.base.telnet_common import DO, DONT, IAC, SUPPRESS_GO_AHEAD, WILL, WONT


@dataclass()
class PluginTransportArgs(BasePluginTransportArgs):
    pass


class TelnetTransport(Transport):
    def __init__(
        self, base_transport_args: BaseTransportArgs, plugin_transport_args: PluginTransportArgs
    ) -> None:
        super().__init__(base_transport_args=base_transport_args)
        self.plugin_transport_args = plugin_transport_args

        self.socket: Optional[Socket] = None
        self._initial_buf = b""

    def _set_socket_timeout(self, timeout: float) -> None:
        """
        Set underlying socket timeout

        Mostly this exists just to assert that socket and socket.sock are not None to appease mypy!

        Args:
            timeout: float value to set as the timeout

        Returns:
            N/A

        Raises:
            ScrapliConnectionNotOpened: if either socket or socket.sock are None
        """
        if self.socket is None:
            raise ScrapliConnectionNotOpened
        if self.socket.sock is None:
            raise ScrapliConnectionNotOpened
        self.socket.sock.settimeout(timeout)

    def _handle_control_chars_response(self, control_buf: bytes, c: bytes) -> bytes:
        """
        Handle the actual response to control characters

        Broken up to be easier to test as well as to appease mr. mccabe

        NOTE: see the asynctelnet transport for additional comments inline about what is going on
        here.

        Args:
            control_buf: current control_buf to work with
            c: currently read control char to process

        Returns:
            bytes: updated control_buf

        Raises:
            ScrapliConnectionNotOpened: if connection is not opened for some reason

        """
        if not self.socket:
            raise ScrapliConnectionNotOpened

        if not control_buf:
            if c != IAC:
                self._initial_buf += c
            else:
                control_buf += c

        elif len(control_buf) == 1 and c in (DO, DONT, WILL, WONT):
            control_buf += c

        elif len(control_buf) == 2:
            cmd = control_buf[1:2]
            control_buf = b""

            if (cmd == DO) and (c == SUPPRESS_GO_AHEAD):
                self.write(IAC + WILL + c)
            elif cmd in (DO, DONT):
                self.write(IAC + WONT + c)
            elif cmd == WILL:
                self.write(IAC + DO + c)
            elif cmd == WONT:
                self.write(IAC + DONT + c)

        return control_buf

    def _handle_control_chars(self) -> None:
        """
        Handle control characters -- nearly identical to CPython (removed in 3.11) telnetlib

        Basically we want to read and "decline" any and all control options that the server proposes
        to us -- so if they say "DO" XYZ directive, we say "DONT", if they say "WILL" we say "WONT".

        NOTE: see the asynctelnet transport for additional comments inline about what is going on
        here.

        Args:
            N/A

        Returns:
            None

        Raises:
            ScrapliConnectionNotOpened: if connection is not opened for some reason
            ScrapliConnectionNotOpened: if we read an empty byte string from the reader -- this
                indicates the server sent an EOF -- see #142

        """
        if not self.socket:
            raise ScrapliConnectionNotOpened

        control_buf = b""

        original_socket_timeout = self._base_transport_args.timeout_socket
        self._set_socket_timeout(self._base_transport_args.timeout_socket / 4)

        while True:
            try:
                c = self._read(1)
                if not c:
                    raise ScrapliConnectionNotOpened("server returned EOF, connection not opened")
            except TimeoutError:
                # shouldn't really matter/need to be reset back to "normal", but don't really want
                # to leave it modified as that would be confusing!
                self._base_transport_args.timeout_socket = original_socket_timeout
                return

            self._set_socket_timeout(self._base_transport_args.timeout_socket / 10)
            control_buf = self._handle_control_chars_response(control_buf=control_buf, c=c)

    def open(self) -> None:
        self._pre_open_closing_log(closing=False)

        if not self.socket:
            self.socket = Socket(
                host=self._base_transport_args.host,
                port=self._base_transport_args.port,
                timeout=self._base_transport_args.timeout_socket,
            )

        if not self.socket.isalive():
            self.socket.open()

        self._handle_control_chars()

        self._post_open_closing_log(closing=False)

    def close(self) -> None:
        self._pre_open_closing_log(closing=True)

        if self.socket:
            self.socket.close()

        self.socket = None

        self._post_open_closing_log(closing=True)

    def isalive(self) -> bool:
        if not self.socket:
            return False
        if not self.socket.isalive():
            return False
        return True

    def _read(self, n: int = 65535) -> bytes:
        """
        Read n bytes from the socket

        Mostly this exists just to assert that socket and socket.sock are not None to appease mypy!

        Args:
            n: optional amount of bytes to try to recv from the underlying socket

        Returns:
            N/A

        Raises:
            ScrapliConnectionNotOpened: if either socket or socket.sock are None
        """
        if self.socket is None:
            raise ScrapliConnectionNotOpened
        if self.socket.sock is None:
            raise ScrapliConnectionNotOpened
        return self.socket.sock.recv(n)

    @timeout_wrapper
    def read(self) -> bytes:
        if not self.socket:
            raise ScrapliConnectionNotOpened

        if self._initial_buf:
            buf = self._initial_buf
            self._initial_buf = b""
            return buf

        try:
            buf = self._read()
            buf = buf.replace(b"\x00", b"")
        except Exception as exc:
            raise ScrapliConnectionError(
                "encountered EOF reading from transport; typically means the device closed the "
                "connection"
            ) from exc
        return buf

    def write(self, channel_input: bytes) -> None:
        if self.socket is None:
            raise ScrapliConnectionNotOpened
        if self.socket.sock is None:
            raise ScrapliConnectionNotOpened
        self.socket.sock.send(channel_input)
