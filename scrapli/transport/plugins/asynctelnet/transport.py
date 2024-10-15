"""scrapli.transport.plugins.asynctelnet.transport"""

import asyncio
import socket
from contextlib import suppress
from dataclasses import dataclass
from typing import Optional

from scrapli.decorators import timeout_wrapper
from scrapli.exceptions import (
    ScrapliAuthenticationFailed,
    ScrapliConnectionError,
    ScrapliConnectionNotOpened,
)
from scrapli.transport.base import AsyncTransport, BasePluginTransportArgs, BaseTransportArgs
from scrapli.transport.base.telnet_common import DO, DONT, IAC, NULL, SUPPRESS_GO_AHEAD, WILL, WONT


@dataclass()
class PluginTransportArgs(BasePluginTransportArgs):
    pass


class AsynctelnetTransport(AsyncTransport):
    def __init__(
        self, base_transport_args: BaseTransportArgs, plugin_transport_args: PluginTransportArgs
    ) -> None:
        super().__init__(base_transport_args=base_transport_args)
        self.plugin_transport_args = plugin_transport_args

        self.stdout: Optional[asyncio.StreamReader] = None
        self.stdin: Optional[asyncio.StreamWriter] = None

        self._eof = False
        self._raw_buf = b""
        self._cooked_buf = b""

        self._control_char_sent_counter = 0
        self._control_char_sent_limit = 10

    def _handle_control_chars_response(self, control_buf: bytes, c: bytes) -> bytes:
        """
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
                self._cooked_buf += c
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

            if (cmd == DO) and (c == SUPPRESS_GO_AHEAD):
                # if server says do suppress go ahead we say will for that option
                self.stdin.write(IAC + WILL + c)
            elif cmd in (DO, DONT):
                # if server says do/dont we always say wont for that option
                self.stdin.write(IAC + WONT + c)
            elif cmd == WILL:
                # if server says will we always say do for that option
                self.stdin.write(IAC + DO + c)
            elif cmd == WONT:
                # if server says wont we always say dont for that option
                self.stdin.write(IAC + DONT + c)

        return control_buf

    def _handle_control_chars(self) -> None:
        """
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

        index = self._raw_buf.find(IAC)
        if index == -1:
            self._cooked_buf = self._raw_buf
            self._raw_buf = b""
            return

        self._cooked_buf = self._raw_buf[:index]
        self._raw_buf = self._raw_buf[index:]

        # control_buf is the buffer for control characters, we reset this after being "done" with
        # responding to a control sequence, so it always represents the "current" control sequence
        # we are working on responding to
        control_buf = b""

        while self._raw_buf:
            c, self._raw_buf = self._raw_buf[:1], self._raw_buf[1:]
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
        except asyncio.TimeoutError as exc:
            msg = "timed out opening connection to device"
            self.logger.critical(msg)
            raise ScrapliAuthenticationFailed(msg) from exc
        except (OSError, socket.gaierror) as exc:
            msg = (
                f"Failed to open telnet session to host {self._base_transport_args.host} -- "
                "do you have a bad host/port?"
            )
            raise ScrapliConnectionError(msg) from exc

        self._post_open_closing_log(closing=False)

    def close(self) -> None:
        self._pre_open_closing_log(closing=True)

        if self.stdin:
            self.stdin.close()

            with suppress(AttributeError):
                # wait closed only in 3.7+... unclear if we should be doing something else for 3.6?
                # it doesnt seem to hurt anything... note 9/2022 probably can remove this but...
                # it still doesnt seem to hurt anything :)
                self.stdin.close()

        self.stdin = None
        self.stdout = None

        self._post_open_closing_log(closing=True)

    def isalive(self) -> bool:
        if not self.stdin or not self.stdout:
            return False
        return not self.stdout.at_eof()

    async def _read(self, n: int = 65535) -> None:
        if not self.stdout:
            raise ScrapliConnectionNotOpened

        if not self._raw_buf:
            try:
                buf = await self.stdout.read(n)
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
    async def read(self) -> bytes:
        if not self.stdout:
            raise ScrapliConnectionNotOpened

        while not self._cooked_buf and not self._eof:
            await self._read()
            if self._control_char_sent_counter < self._control_char_sent_limit:
                self._handle_control_chars()

        buf = self._cooked_buf
        self._cooked_buf = b""

        # possible to still have null bytes in the buf, replace them with nothing
        return buf.replace(NULL, b"")

    def write(self, channel_input: bytes) -> None:
        if not self.stdin:
            raise ScrapliConnectionNotOpened
        self.stdin.write(channel_input)
