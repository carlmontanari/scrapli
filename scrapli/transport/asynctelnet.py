"""scrapli.transport.asynctelnet"""
import asyncio
import re
import socket
from asyncio import StreamReader, StreamWriter
from datetime import datetime

from scrapli.decorators import OperationTimeout, requires_open_session
from scrapli.exceptions import ConnectionNotOpened, ScrapliAuthenticationFailed, ScrapliTimeout
from scrapli.helper import get_prompt_pattern, strip_ansi
from scrapli.transport.async_transport import AsyncTransport

ASYNC_TELNET_TRANSPORT_ARGS = (
    "auth_username",
    "auth_password",
    "auth_bypass",
    "comms_prompt_pattern",
    "comms_return_char",
    "comms_ansi",
    "timeout_ops",
)

# telnet control characters we care about
IAC = bytes([255])
DONT = bytes([254])
DO = bytes([253])
WONT = bytes([252])
WILL = bytes([251])


class AsyncTelnetTransport(AsyncTransport):
    def __init__(
        self,
        host: str,
        port: int = 23,
        auth_username: str = "",
        auth_password: str = "",
        auth_bypass: bool = False,
        timeout_socket: int = 10,
        timeout_transport: int = 30,
        timeout_ops: int = 30,
        timeout_exit: bool = True,
        comms_prompt_pattern: str = r"^[a-z0-9.\-@()/:]{1,32}[#>$]$",
        comms_return_char: str = "\n",
        comms_ansi: bool = False,
    ) -> None:
        r"""
        AsyncTelnetTransport Object

        Asyncio telnet driver built using standard library asyncio streams. Declines any and all
        control characters sent by the server, thus providing the base telnet NVT -- so far this
        works for all tested platforms!

        Args:
            host: host ip/name to connect to
            port: port to connect to
            auth_username: username for authentication
            auth_password: password for authentication
            auth_bypass: bypass authentication process
            timeout_socket: timeout for establishing socket in seconds -- since this is not directly
                exposed in telnetlib, this is just the initial timeout for the telnet connection.
                After the connection is established, the timeout is modified to the value of
                `timeout_transport`.
            timeout_transport: timeout for telnet transport in seconds
            timeout_ops: timeout for telnet channel operations in seconds -- this is also the
                timeout for finding and responding to username and password prompts at initial
                login. This is assigned to a private attribute and is ignored after authentication
                is completed.
            timeout_exit: True/False close transport if timeout encountered. If False and keepalives
                are in use, keepalives will prevent program from exiting so you should be sure to
                catch Timeout exceptions and handle them appropriately
            comms_prompt_pattern: prompt pattern expected for device, same as the one provided to
                channel -- telnet needs to know this to know how to decide if we are properly
                sending/receiving data -- i.e. we are not stuck at some password prompt or some
                other failure scenario. If using driver, this should be passed from driver (Scrape,
                or IOSXE, etc.) to this Transport class. This is assigned to a private attribute and
                is ignored after authentication is completed.
            comms_return_char: return character to use on the channel, same as the one provided to
                channel -- telnet needs to know this to know what to send so that we can probe
                the channel to make sure we are authenticated and sending/receiving data. If using
                driver, this should be passed from driver (Scrape, or IOSXE, etc.) to this Transport
                class. This is assigned to a private attribute and is ignored after authentication
                is completed.
            comms_ansi: True/False strip comms_ansi characters from output; this value is assigned
                self._comms_ansi and is ignored after authentication. We only need it for transport
                on the off chance (maybe never, especially here in telnet land?) that
                username/password prompts contain ansi characters, otherwise "comms_ansi" is really
                a channel attribute and is treated as such. This is assigned to a private attribute
                and is ignored after authentication is completed.

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        super().__init__(
            host,
            port,
            timeout_socket,
            timeout_transport,
            timeout_exit,
        )
        self.auth_username: str = auth_username
        self.auth_password: str = auth_password
        self.auth_bypass: bool = auth_bypass

        self._timeout_ops: int = timeout_ops
        # timeout_ops_auth is only used for authentication; base ops timeout * 2 as we are doing
        # two operations -- entering username and entering password (in most cases at least)
        self._timeout_ops_auth: int = timeout_ops * 2

        self._comms_prompt_pattern: str = comms_prompt_pattern
        self._comms_return_char: str = comms_return_char
        self._comms_ansi: bool = comms_ansi

        self.username_prompt: str = "Username:"
        self.password_prompt: str = "Password:"

        self.stdout: StreamReader
        self.stdin: StreamWriter
        self._stdout_binary_transmission = False
        self.lib_auth_exception = ScrapliAuthenticationFailed
        self._isauthenticated = False

    async def _open(self) -> bytes:
        """ "
        Private open method so that it can be wrapped with timeout_socket timeout

        Args:
            N/A

        Returns:
            bytes: bytes read during control character handling

        Raises:
            ConnectionNotOpened: if we encounter a ConnectionError, socket.gaierror, or OSError

        """
        try:
            self.stdout, self.stdin = await asyncio.open_connection(host=self.host, port=self.port)
        except ConnectionError as exc:
            msg = f"Failed to open telnet session to host {self.host}"
            if "connection refused" in str(exc).lower():
                msg = f"Failed to open telnet session to host {self.host}, connection refused"
            raise ConnectionNotOpened(msg) from exc
        except (OSError, socket.gaierror) as exc:
            msg = (
                f"Failed to open telnet session to host {self.host} -- do you have a bad host/port?"
            )
            raise ConnectionNotOpened(msg) from exc

        output = await self._handle_control_chars()
        return output

    async def _handle_control_chars(self) -> bytes:
        """ "
        Handle control characters -- nearly identical to CPython telnetlib

        Basically we want to read and "decline" any and all control options that the server proposes
        to us -- so if they say "DO" XYZ directive, we say "DONT", if they say "WILL" we say "WONT".

        Args:
            N/A

        Returns:
            bytes: bytes read during control character handling

        Raises:
            N/A

        """
        # control_buf is the buffer for control characters, we reset this after being "done" with
        # responding to a control sequence, so it always represents the "current" control sequence
        # we are working on responding to
        control_buf = b""
        output = b""

        # initial read timeout for control characters can be 1/4 of socket timeout, after reading a
        # single byte we crank it way down to 0.1 as we now expect all the characters to already be
        # in the buffer to be read
        char_read_timeout = self.timeout_socket / 4

        while True:
            try:
                c = await asyncio.wait_for(self.stdout.read(1), timeout=char_read_timeout)
            except asyncio.TimeoutError:
                self.logger.debug("done reading control chars from the stream, moving on")
                return output

            char_read_timeout = 0.1

            # control_buf is empty, lets see if we got a control character
            if not control_buf:
                if c != IAC:
                    # add whatever character we read to the "normal" output buf so it gets sent off
                    # to the auth method later (username/show prompts may show up here)
                    output += c
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

    async def open(self) -> None:
        """
        Open telnet channel

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            ConnectionNotOpened: if connection cant be opened
            ScrapliAuthenticationFailed: if cant successfully authenticate

        """
        try:
            output = await asyncio.wait_for(self._open(), timeout=self.timeout_socket)
        except asyncio.TimeoutError as exc:
            raise ConnectionNotOpened(
                "timed out opening connection and processing telnet control characters"
            ) from exc

        self.logger.debug(f"Session to host {self.host} spawned")

        if self.auth_bypass:
            self.logger.info("`auth_bypass` is True, bypassing authentication")
            # if we skip auth, we'll manually set _isauthenticated to True, the rest is up to the
            # user to handle, or things will just time out later... either way, not our problem :)
            self._isauthenticated = True
            return

        await self._authenticate(output=output)

        _telnet_isauthenticated = await self._telnet_isauthenticated()
        if not self._isauthenticated and not _telnet_isauthenticated:
            raise ScrapliAuthenticationFailed(
                f"Could not authenticate over telnet to host: {self.host}"
            )
        self.logger.debug(f"Authenticated to host {self.host} with password")

    @OperationTimeout("_timeout_ops_auth", "Timed out looking for telnet login prompts")
    async def _authenticate(self, output: bytes = b"") -> None:
        """
        Parent private method to handle telnet authentication

        Nearly the same as the sync telnet operation, however we accept bytes from the control char
        handling section and thus we read from the socket at the end of the while loop instead of at
        the beginning.

        Args:
            output: any output already read from reading the server directives

        Returns:
            N/A  # noqa: DAR202

        Raises:
            ScrapliAuthenticationFailed: if an EOFError is encountered; we in theory *did* open the
                connection, so we won't raise a ConnectionNotOpened here

        """
        # capture the start time of the authentication event; we also set a "return_interval" which
        # is 1/10 the timout_ops value, we will send a return character at roughly this interval if
        # there is no output on the channel. we do this because sometimes telnet needs a kick to get
        # it to prompt for auth -- particularity when connecting to terminal server/console port
        auth_start_time = datetime.now().timestamp()
        return_interval = self._timeout_ops / 10
        return_attempts = 1

        while True:
            if self.username_prompt.lower().encode() in output.lower():
                self.logger.info("Found username prompt, sending username")
                # if/when we see username, reset the output to empty byte string
                output = b""
                self.stdin.write(self.auth_username.encode())
                self.stdin.write(self._comms_return_char.encode())
            elif self.password_prompt.lower().encode() in output.lower():
                self.logger.info("Found password prompt, sending password")
                self.stdin.write(self.auth_password.encode())
                self.stdin.write(self._comms_return_char.encode())
                break

            try:
                new_output = await asyncio.wait_for(self.stdout.read(65535), timeout=1)
                output += new_output
                self.logger.debug(f"Attempting to authenticate. Read: {repr(new_output)}")
            except asyncio.TimeoutError:
                new_output = b""
            except EOFError as exc:
                # EOF means telnet connection is dead :(
                msg = f"Failed to open connection to host {self.host}. Connection lost."
                self.logger.critical(msg)
                raise ScrapliAuthenticationFailed(msg) from exc

            if not new_output:
                current_iteration_time = datetime.now().timestamp()
                if (current_iteration_time - auth_start_time) > (return_interval * return_attempts):
                    self.logger.debug(
                        "No username or password prompt found, sending return character..."
                    )
                    self.stdin.write(self._comms_return_char.encode())
                    return_attempts += 1

    @OperationTimeout("_timeout_ops_auth", "Timed determining if telnet session is authenticated")
    async def _telnet_isauthenticated(self) -> bool:
        """
        Check if session is authenticated

        This is very naive -- it only knows if the telnet session has not received an EOF.
        Beyond that we send the return character and re-read the channel.

        Args:
            N/A

        Returns:
            bool: True if authenticated, else False

        Raises:
            N/A

        """
        self.logger.debug("Attempting to determine if telnet authentication was successful")
        if not self.stdout.at_eof():
            prompt_pattern = get_prompt_pattern(prompt="", class_prompt=self._comms_prompt_pattern)
            self.stdin.write(self._comms_return_char.encode())

            output = b""
            while True:
                new_output = await self.stdout.read(65535)
                output += new_output
                self.logger.debug(
                    f"Attempting to validate authentication. Read: {repr(new_output)}"
                )
                # we do not need to deal w/ line replacement for the actual output, only for
                # parsing if a prompt-like thing is at the end of the output
                output = output.replace(b"\r", b"")
                # always check to see if we should strip ansi here; if we don't handle this we
                # may raise auth failures for the wrong reason which would be confusing for
                # users
                if self._comms_ansi or b"\x1B" in output:
                    output = strip_ansi(output=output)
                if b"\x00" in output:
                    # at least nxos likes to send \x00 before output, we can check if the server
                    # does this here, and set the transport attribute to True so we can strip it out
                    # in the read method
                    self._stdout_binary_transmission = True
                    output = output.replace(b"\x00", b"")
                channel_match = re.search(pattern=prompt_pattern, string=output)
                if channel_match:
                    self._isauthenticated = True
                    break
                if b"username:" in output.lower():
                    # if we see "username" prompt we can assume (because telnet) that we failed
                    # to authenticate
                    self.logger.critical(
                        "Found `username:` in output, assuming password authentication failed"
                    )
                    break
                if b"password:" in output.lower():
                    # if we see "password" we know auth failed (hopefully in all scenarios!)
                    self.logger.critical(
                        "Found `password:` in output, assuming password authentication failed"
                    )
                    break
                if output:
                    self.logger.debug(
                        f"Cannot determine if authenticated, \n\tRead: {repr(output)}"
                    )

        if self._isauthenticated:
            return True

        return False

    def close(self) -> None:
        """
        Close session and socket

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.stdin.close()
        try:
            asyncio.get_event_loop().create_task(coro=self.stdin.wait_closed())
        except AttributeError:
            # wait closed only in 3.7+... unclear if we should be doing something else for 3.6? but
            # it doesnt seem to hurt anything...
            pass
        self._isauthenticated = False
        self.logger.debug(f"Channel to host {self.host} closed")

    def isalive(self) -> bool:
        """
        Check if alive and session is authenticated

        Args:
            N/A

        Returns:
            bool: True if alive, False otherwise.

        Raises:
            N/A

        """
        if self._isauthenticated and not self.stdout.at_eof():
            return True
        return False

    async def read(self) -> bytes:
        """
        Read data from the channel

        Args:
            N/A

        Returns:
            bytes: bytes read from the telnet channel

        Raises:
            ScrapliTimeout: if async read does not complete within timeout_transport interval

        """
        read_timeout = self.timeout_transport or None
        try:
            output = await asyncio.wait_for(self.stdout.read(65535), timeout=read_timeout)
        except asyncio.TimeoutError as exc:
            msg = f"Timed out reading from transport, transport timeout: {self.timeout_transport}"
            self.logger.exception(msg)
            raise ScrapliTimeout(msg) from exc

        if self._stdout_binary_transmission:
            output = output.replace(b"\x00", b"")
        return output

    @requires_open_session()
    def write(self, channel_input: str) -> None:
        """
        Write data to the channel

        Args:
            channel_input: string to send to channel

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.stdin.write(channel_input.encode())

    def set_timeout(self, timeout: int) -> None:
        """
        Set session timeout

        Args:
            timeout: timeout in seconds

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.timeout_transport = timeout
