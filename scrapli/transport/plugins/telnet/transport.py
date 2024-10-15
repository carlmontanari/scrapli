"""scrapli.transport.plugins.telnet.transport"""

from dataclasses import dataclass
from typing import Optional

from scrapli.decorators import timeout_wrapper
from scrapli.exceptions import ScrapliConnectionError, ScrapliConnectionNotOpened
from scrapli.transport.base import BasePluginTransportArgs, BaseTransportArgs, Transport
from scrapli.transport.base.base_socket import Socket
from scrapli.transport.base.telnet_common import DO, DONT, IAC, NULL, SUPPRESS_GO_AHEAD, WILL, WONT


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
        self._eof = False
        self._raw_buf = b""
        self._cooked_buf = b""

        self._control_char_sent_counter = 0
        self._control_char_sent_limit = 10

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

    def _handle_control_chars_socket_timeout_update(self) -> None:
        """
        Handle updating (if necessary) the socket timeout

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        self._control_char_sent_counter += 1

        if self._control_char_sent_counter > self._control_char_sent_limit:
            # connection is opened, effectively ignore socket timeout at this point as we want
            # the timeout socket to be "just" for opening the connection basically
            # the number 8 is fairly arbitrary -- it looks like *most* platforms send around
            # 8 - 12 control char/instructions on session opening, so we'll go with 8!
            self._set_socket_timeout(600)

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
                self._cooked_buf += c
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

            self._handle_control_chars_socket_timeout_update()

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

        """
        if not self.socket:
            raise ScrapliConnectionNotOpened

        index = self._raw_buf.find(IAC)
        if index == -1:
            self._cooked_buf = self._raw_buf
            self._raw_buf = b""
            return

        self._cooked_buf = self._raw_buf[:index]
        self._raw_buf = self._raw_buf[index:]
        control_buf = b""

        while self._raw_buf:
            c, self._raw_buf = self._raw_buf[:1], self._raw_buf[1:]
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

    def _read(self, n: int = 65535) -> None:
        """
        Read n bytes from the socket and fill raw buffer

        Mostly this exists just to assert that socket and socket.sock are not None to appease mypy!

        Args:
            n: optional amount of bytes to try to recv from the underlying socket

        Returns:
            N/A

        Raises:
            ScrapliConnectionNotOpened: if either socket or socket.sock are None
            ScrapliConnectionError: if we fail to recv from the underlying socket

        """
        if self.socket is None:
            raise ScrapliConnectionNotOpened
        if self.socket.sock is None:
            raise ScrapliConnectionNotOpened
        if not self._raw_buf:
            try:
                buf = self.socket.sock.recv(n)
                self._eof = not buf
                if self._control_char_sent_counter < self._control_char_sent_limit:
                    self._raw_buf += buf
                else:
                    self._cooked_buf += buf
            except EOFError as exc:
                raise ScrapliConnectionError(
                    "encountered EOF reading from transport; typically means the device closed the "
                    "connection"
                ) from exc

    @timeout_wrapper
    def read(self) -> bytes:
        if not self.socket:
            raise ScrapliConnectionNotOpened

        while not self._cooked_buf and not self._eof:
            self._read()
            if self._control_char_sent_counter < self._control_char_sent_limit:
                self._handle_control_chars()

        buf = self._cooked_buf
        self._cooked_buf = b""

        # possible to still have null bytes in the buf, replace them with nothing
        return buf.replace(NULL, b"")

    def write(self, channel_input: bytes) -> None:
        if self.socket is None:
            raise ScrapliConnectionNotOpened
        if self.socket.sock is None:
            raise ScrapliConnectionNotOpened
        self.socket.sock.send(channel_input)
