"""scrapli.transport.telnet"""
import re
import time
from logging import getLogger
from select import select
from telnetlib import Telnet
from threading import Lock
from typing import Optional

from scrapli.decorators import operation_timeout
from scrapli.exceptions import ScrapliAuthenticationFailed
from scrapli.helper import get_prompt_pattern
from scrapli.transport.transport import Transport

LOG = getLogger("transport")

TELNET_TRANSPORT_ARGS = (
    "host",
    "port",
    "timeout_transport",
    "timeout_ops",
    "auth_username",
    "auth_password",
    "comms_prompt_pattern",
    "comms_return_char",
)


class ScrapliTelnet(Telnet):
    def __init__(self, host: str, port: int, timeout: int) -> None:
        self.eof: bool
        super().__init__(host, port, timeout)


class TelnetTransport(Transport):
    def __init__(
        self,
        host: str,
        port: int = 23,
        auth_username: str = "",
        auth_password: str = "",
        timeout_transport: int = 5000,
        timeout_ops: int = 10,
        comms_prompt_pattern: str = r"^[a-z0-9.\-@()/:]{1,32}[#>$]$",
        comms_return_char: str = "\n",
    ):  # pylint: disable=W0231
        """
        TelnetTransport Object

        Inherit from Transport ABC and Socket base class:
        TelnetTransport <- Transport (ABC)
        TelnetTransport <- Socket

        Args:
            host: host ip/name to connect to
            port: port to connect to
            auth_username: username for authentication
            auth_password: password for authentication
            timeout_transport: timeout for telnet transport in milliseconds
            timeout_ops: timeout for telnet channel operations in seconds -- this is also the
                timeout for finding and responding to username and password prompts at initial
                login.
            comms_prompt_pattern: prompt pattern expected for device, same as the one provided to
                channel -- system ssh needs to know this to know how to decide if we are properly
                sending/receiving data -- i.e. we are not stuck at some password prompt or some
                other failure scenario. If using driver, this should be passed from driver (Scrape,
                or IOSXE, etc.) to this Transport class.
            comms_return_char: return character to use on the channel, same as the one provided to
                channel -- system ssh needs to know this to know what to send so that we can probe
                the channel to make sure we are authenticated and sending/receiving data. If using
                driver, this should be passed from driver (Scrape, or IOSXE, etc.) to this Transport
                class.

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.host: str = host
        self.port: int = port
        self.timeout_transport: int = int(timeout_transport / 1000)
        self.timeout_ops: int = timeout_ops
        self.session_lock: Lock = Lock()
        self.auth_username: str = auth_username
        self.auth_password: str = auth_password
        self.comms_prompt_pattern: str = comms_prompt_pattern
        self.comms_return_char: str = comms_return_char

        self.username_prompt: str = "Username:"
        self.password_prompt: str = "Password:"

        self.session: ScrapliTelnet
        self.lib_auth_exception = ScrapliAuthenticationFailed
        self._isauthenticated = False

    def open(self) -> None:
        """
        Open channel, acquire pty, request interactive shell

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            ScrapliAuthenticationFailed: if cant successfully authenticate

        """
        self.session_lock.acquire()
        telnet_session = ScrapliTelnet(
            host=self.host, port=self.port, timeout=self.timeout_transport
        )
        LOG.debug(f"Session to host {self.host} spawned")
        self.session_lock.release()
        self._authenticate(telnet_session)
        if not self._telnet_isauthenticated(telnet_session):
            raise ScrapliAuthenticationFailed(
                f"Could not authenticate over telnet to host: {self.host}"
            )
        LOG.debug(f"Authenticated to host {self.host} with password")
        self.session = telnet_session

    def _authenticate(self, telnet_session: ScrapliTelnet) -> None:
        """
        Parent private method to handle telnet authentication

        Args:
            telnet_session: Telnet session object

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self._authenticate_username(telnet_session)
        self._authenticate_password(telnet_session)

    @operation_timeout("timeout_ops", "Timed out looking for telnet login username prompt")
    def _authenticate_username(self, telnet_session: ScrapliTelnet) -> None:
        """
        Private method to enter username for telnet authentication

        Args:
            telnet_session: Telnet session object

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.session_lock.acquire()
        while True:
            output = telnet_session.read_eager()
            if self.username_prompt.lower().encode() in output.lower():
                telnet_session.write(self.auth_username.encode())
                telnet_session.write(self.comms_return_char.encode())
                self.session_lock.release()
                break

    @operation_timeout("timeout_ops", "Timed out looking for telnet login password prompt")
    def _authenticate_password(self, telnet_session: ScrapliTelnet) -> None:
        """
        Private method to enter password for telnet authentication

        Args:
            telnet_session: Telnet session object

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.session_lock.acquire()
        while True:
            output = telnet_session.read_eager()
            if self.password_prompt.lower().encode() in output.lower():
                telnet_session.write(self.auth_password.encode())
                telnet_session.write(self.comms_return_char.encode())
                self.session_lock.release()
                break

    def _telnet_isauthenticated(self, telnet_session: ScrapliTelnet) -> bool:
        """
        Check if session is authenticated

        This is very naive -- it only knows if the sub process is alive and has not received an EOF.
        Beyond that we lock the session and send the return character and re-read the channel.

        Args:
            telnet_session: Telnet session object

        Returns:
            bool: True if authenticated, else False

        Raises:
            N/A

        """
        if not telnet_session.eof:
            prompt_pattern = get_prompt_pattern("", self.comms_prompt_pattern)
            telnet_session_fd = telnet_session.fileno()
            self.session_lock.acquire()
            telnet_session.write(self.comms_return_char.encode())
            time.sleep(0.25)
            fd_ready, _, _ = select([telnet_session_fd], [], [], 0)
            if telnet_session_fd in fd_ready:
                output = telnet_session.read_eager()
                # we do not need to deal w/ line replacement for the actual output, only for
                # parsing if a prompt-like thing is at the end of the output
                output = re.sub(b"\r", b"\n", output.strip())
                channel_match = re.search(prompt_pattern, output)
                if channel_match:
                    self.session_lock.release()
                    self._isauthenticated = True
                    return True
        self.session_lock.release()
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
        self.session_lock.acquire()
        self.session.close()
        LOG.debug(f"Channel to host {self.host} closed")
        self.session_lock.release()

    def isalive(self) -> bool:
        """
        Check if alive and session is authenticated

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        if self._isauthenticated and not self.session.eof:
            return True
        return False

    def read(self) -> bytes:
        """
        Read data from the channel

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        return self.session.read_eager()

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

    def set_timeout(self, timeout: Optional[int] = None) -> None:
        """
        Set session timeout

        Args:
            timeout: timeout in seconds

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """

    def set_blocking(self, blocking: bool = False) -> None:
        """
        Set session blocking configuration

        Args:
            blocking: True/False set session to blocking

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
