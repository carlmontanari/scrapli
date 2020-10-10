"""scrapli.transport.telnet"""
import re
from datetime import datetime
from telnetlib import Telnet

from scrapli.decorators import OperationTimeout, requires_open_session
from scrapli.exceptions import ConnectionNotOpened, ScrapliAuthenticationFailed
from scrapli.helper import get_prompt_pattern, strip_ansi
from scrapli.transport.transport import Transport

TELNET_TRANSPORT_ARGS = (
    "auth_username",
    "auth_password",
    "auth_bypass",
    "comms_prompt_pattern",
    "comms_return_char",
    "comms_ansi",
    "timeout_ops",
)


class ScrapliTelnet(Telnet):
    def __init__(self, host: str, port: int, timeout: int) -> None:
        """
        ScrapliTelnet class for typing purposes

        Args:
            host: string of host
            port: integer port to connect to
            timeout: timeout value in seconds

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.eof: bool
        self.timeout: int
        super().__init__(host, port, timeout)


class TelnetTransport(Transport):
    def __init__(
        self,
        host: str,
        port: int = 23,
        auth_username: str = "",
        auth_password: str = "",
        auth_bypass: bool = False,
        timeout_socket: int = 5,
        timeout_transport: int = 5,
        timeout_ops: int = 10,
        timeout_exit: bool = True,
        comms_prompt_pattern: str = r"^[a-z0-9.\-@()/:]{1,32}[#>$]$",
        comms_return_char: str = "\n",
        comms_ansi: bool = False,
    ) -> None:
        r"""
        TelnetTransport Object

        Inherit from Transport ABC
        TelnetTransport <- Transport (ABC)

        Note that comms_prompt_pattern, comms_return_char and comms_ansi are only passed here to
        handle "in channel" authentication required by SystemSSH -- these are assigned to private
        attributes in this class and ignored after authentication. If you wish to modify these
        values on a "live" scrapli connection, modify them in the Channel object, i.e.
        `conn.channel.comms_prompt_pattern`. Additionally timeout_ops is passed and assigned to
        _timeout_ops to use the same timeout_ops that is used in Channel to decorate the
        authentication methods here.

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

        self.session: ScrapliTelnet
        self.lib_auth_exception = ScrapliAuthenticationFailed
        self._isauthenticated = False

    def open(self) -> None:
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
        # establish session with "socket" timeout, then reset timeout to "transport" timeout
        try:
            self.session = ScrapliTelnet(
                host=self.host, port=self.port, timeout=self.timeout_socket
            )
        except ConnectionError as exc:
            msg = f"Failed to open telnet session to host {self.host}"
            if "connection refused" in str(exc).lower():
                msg = f"Failed to open telnet session to host {self.host}, connection refused"
            raise ConnectionNotOpened(msg) from exc
        self.session.timeout = self.timeout_transport
        self.logger.debug(f"Session to host {self.host} spawned")

        if not self.auth_bypass:
            self._authenticate()
        else:
            self.logger.info("`auth_bypass` is True, bypassing authentication")
            # if we skip auth, we'll manually set _isauthenticated to True
            self._isauthenticated = True

        if not self._isauthenticated and not self._telnet_isauthenticated():
            raise ScrapliAuthenticationFailed(
                f"Could not authenticate over telnet to host: {self.host}"
            )

        self.logger.debug(f"Authenticated to host {self.host} with password")

    @OperationTimeout("_timeout_ops_auth", "Timed out looking for telnet login prompts")
    def _authenticate(self) -> None:
        """
        Parent private method to handle telnet authentication

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            ScrapliAuthenticationFailed: if an EOFError is encountered; we in theory *did* open the
                connection, so we won't raise a ConnectionNotOpened here

        """
        output = b""

        # capture the start time of the authentication event; we also set a "return_interval" which
        # is 1/10 the timout_ops value, we will send a return character at roughly this interval if
        # there is no output on the channel. we do this because sometimes telnet needs a kick to get
        # it to prompt for auth -- particularity when connecting to terminal server/console port
        auth_start_time = datetime.now().timestamp()
        return_interval = self._timeout_ops / 10
        return_attempts = 1

        while True:
            try:
                new_output = self.session.read_eager()
                output += new_output
                self.logger.debug(f"Attempting to authenticate. Read: {repr(new_output)}")
            except EOFError as exc:
                # EOF means telnet connection is dead :(
                msg = f"Failed to open connection to host {self.host}. Connection lost."
                self.logger.critical(msg)
                raise ScrapliAuthenticationFailed(msg) from exc

            if self.username_prompt.lower().encode() in output.lower():
                self.logger.info("Found username prompt, sending username")
                # if/when we see username, reset the output to empty byte string
                output = b""
                self.session.write(self.auth_username.encode())
                self.session.write(self._comms_return_char.encode())
            elif self.password_prompt.lower().encode() in output.lower():
                self.logger.info("Found password prompt, sending password")
                self.session.write(self.auth_password.encode())
                self.session.write(self._comms_return_char.encode())
                break
            elif not output:
                current_iteration_time = datetime.now().timestamp()
                if (current_iteration_time - auth_start_time) > (return_interval * return_attempts):
                    self.logger.debug(
                        "No username or password prompt found, sending return character..."
                    )
                    self.session.write(self._comms_return_char.encode())
                    return_attempts += 1

    @OperationTimeout("_timeout_ops_auth", "Timed determining if telnet session is authenticated")
    def _telnet_isauthenticated(self) -> bool:
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
        if not self.session.eof:
            prompt_pattern = get_prompt_pattern(prompt="", class_prompt=self._comms_prompt_pattern)
            self.session.write(self._comms_return_char.encode())
            self._wait_for_session_fd_ready(fd=self.session.fileno())

            output = b""
            while True:
                new_output = self.session.read_eager()
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
        self.session.close()
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
        if self._isauthenticated and not self.session.eof:
            return True
        return False

    @requires_open_session()
    @OperationTimeout("timeout_transport", "Timed out reading from transport")
    def read(self) -> bytes:
        """
        Read data from the channel

        Args:
            N/A

        Returns:
            bytes: bytes read from the telnet channel

        Raises:
            N/A

        """
        return self.session.read_eager()

    @requires_open_session()
    @OperationTimeout("timeout_transport", "Timed out writing to transport")
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
        self.session.write(channel_input.encode())

    @requires_open_session()
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
        self.session.timeout = timeout
