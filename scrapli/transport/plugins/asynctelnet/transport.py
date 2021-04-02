"""scrapli.transport.plugins.asynctelnet.transport"""
import asyncio
import socket
from dataclasses import dataclass
from typing import Optional

from scrapli.decorators import TransportTimeout
from scrapli.exceptions import (
    ScrapliAuthenticationFailed,
    ScrapliConnectionError,
    ScrapliConnectionNotOpened,
)
from scrapli.transport.base import AsyncTransport, BasePluginTransportArgs, BaseTransportArgs

# telnet control characters we care about
IAC = bytes([255])
DONT = bytes([254])
DO = bytes([253])
WONT = bytes([252])
WILL = bytes([251])


@dataclass()
class PluginTransportArgs(BasePluginTransportArgs):
    pass


class AsynctelnetTransport(AsyncTransport):
    def __init__(
        self, base_transport_args: BaseTransportArgs, plugin_transport_args: PluginTransportArgs
    ) -> None:
        super().__init__(base_transport_args=base_transport_args)
        self.plugin_transport_args = plugin_transport_args

        self.username_prompt: str = "sername:"
        self.password_prompt: str = "assword:"

        self.stdout: Optional[asyncio.StreamReader] = None
        self.stdin: Optional[asyncio.StreamWriter] = None

        self._initial_buf = b""
        self._stdout_binary_transmission = False

    def _handle_control_chars_response(self, control_buf: bytes, c: bytes) -> bytes:
        """ "
        Handle the actual response to control characters

        Broken up to be easier to test as well as to appease mr. mccabe

        Args:
            control_buf: current control_buf to work with
            c: currently read control char to process

        Returns:
            bytes: updated control_buf

        Raises:
            ScrapliConnectionNotOpened: if connection is not opened for some reason

        """
        if not self.stdin:
            raise ScrapliConnectionNotOpened

        # control_buf is empty, lets see if we got a control character
        if not control_buf:
            if c != IAC:
                # add whatever character we read to the "normal" output buf so it gets sent off
                # to the auth method later (username/show prompts may show up here)
                self._initial_buf += c
            else:
                # we got a control character, put it into the control_buf
                control_buf += c

        elif len(control_buf) == 1 and c in (DO, DONT, WILL, WONT):
            # control buf already has the IAC byte loaded, if the next char is DO/DONT/WILL/WONT
            # add that into the control buffer and move on
            control_buf += c

        elif len(control_buf) == 2:
            # control buffer is already loaded with IAC and directive, we now have an option to
            # deal with, create teh base command out of the existing buffer then reset the buf
            # for the next go around
            cmd = control_buf[1:2]
            control_buf = b""

            if cmd in (DO, DONT):
                # if server says do/dont we always say wont for that option
                self.stdin.write(IAC + WONT + c)
            elif cmd in (WILL, WONT):
                # if server says will/wont we always say dont for that option
                self.stdin.write(IAC + DONT + c)

        return control_buf

    async def _handle_control_chars(self) -> None:
        """ "
        Handle control characters -- nearly identical to CPython telnetlib

        Basically we want to read and "decline" any and all control options that the server proposes
        to us -- so if they say "DO" XYZ directive, we say "DONT", if they say "WILL" we say "WONT".

        Args:
            N/A

        Returns:
            None

        Raises:
            ScrapliConnectionNotOpened: if connection is not opened for some reason

        """
        if not self.stdout:
            raise ScrapliConnectionNotOpened

        # control_buf is the buffer for control characters, we reset this after being "done" with
        # responding to a control sequence, so it always represents the "current" control sequence
        # we are working on responding to
        control_buf = b""

        # initial read timeout for control characters can be 1/4 of socket timeout, after reading a
        # single byte we crank it way down; the next value used to be 0.1 but this was causing some
        # issues for folks that had devices behaving very slowly... so hopefully 1/10 is a
        # reasonable value for the follow up char read timeout... of course we will return early if
        # we do get a char in the buffer so it should be all good!
        char_read_timeout = self._base_transport_args.timeout_socket / 4

        while True:
            try:
                c = await asyncio.wait_for(self.stdout.read(1), timeout=char_read_timeout)
            except asyncio.TimeoutError:
                return
            char_read_timeout = self._base_transport_args.timeout_socket / 10
            control_buf = self._handle_control_chars_response(control_buf=control_buf, c=c)

    async def open(self) -> None:
        self._pre_open_closing_log(closing=False)

        try:
            fut = asyncio.open_connection(
                host=self._base_transport_args.host, port=self._base_transport_args.port
            )
            self.stdout, self.stdin = await asyncio.wait_for(
                fut, timeout=self._base_transport_args.timeout_socket
            )
        except ConnectionError as exc:
            msg = f"Failed to open telnet session to host {self._base_transport_args.host}"
            if "connection refused" in str(exc).lower():
                msg = (
                    f"Failed to open telnet session to host {self._base_transport_args.host}, "
                    "connection refused"
                )
            raise ScrapliConnectionError(msg) from exc
        except (OSError, socket.gaierror) as exc:
            msg = (
                f"Failed to open telnet session to host {self._base_transport_args.host} -- "
                "do you have a bad host/port?"
            )
            raise ScrapliConnectionError(msg) from exc
        except asyncio.TimeoutError as exc:
            msg = "timed out opening connection to device"
            self.logger.critical(msg)
            raise ScrapliAuthenticationFailed(msg) from exc

        await self._handle_control_chars()

        self._post_open_closing_log(closing=False)

    def close(self) -> None:
        self._pre_open_closing_log(closing=True)

        if self.stdin:
            self.stdin.close()

            try:
                self.stdin.close()
            except AttributeError:
                # wait closed only in 3.7+... unclear if we should be doing something else for 3.6?
                # it doesnt seem to hurt anything...
                pass

        self.stdin = None
        self.stdout = None

        self._post_open_closing_log(closing=True)

    def isalive(self) -> bool:
        if not self.stdin or not self.stdout:
            return False
        return not self.stdout.at_eof()

    @TransportTimeout("timed out reading from transport")
    async def read(self) -> bytes:
        if not self.stdout:
            raise ScrapliConnectionNotOpened

        if self._initial_buf:
            buf = self._initial_buf
            self._initial_buf = b""
            return buf

        try:
            buf = await self.stdout.read(65535)
            # nxos at least sends "binary transmission" control char, but seems to not (afaik?)
            # actually advertise it during the control protocol exchange, causing us to not be able
            # to "know" that it is in binary transmit mode until later... so we will just always
            # strip this option (b"\x00") out of the buffered data...
            buf = buf.replace(b"\x00", b"")
        except EOFError as exc:
            raise ScrapliConnectionError(
                "encountered EOF reading from transport; typically means the device closed the "
                "connection"
            ) from exc

        return buf

    def write(self, channel_input: bytes) -> None:
        if not self.stdin:
            raise ScrapliConnectionNotOpened
        self.stdin.write(channel_input)
