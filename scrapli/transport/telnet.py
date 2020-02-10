"""scrapli.transport.telnet"""
import re
import time
from logging import getLogger
from select import select
from telnetlib import Telnet
from threading import Lock
from typing import Optional

from scrapli.exceptions import ScrapliAuthenticationFailed
from scrapli.helper import get_prompt_pattern
from scrapli.transport.transport import Transport

LOG = getLogger("transport")

TELNET_TRANSPORT_ARGS = (
    "host",
    "port",
    "timeout_ssh",
    "timeout_socket",
    "auth_username",
    "auth_public_key",
    "auth_password",
    "comms_prompt_pattern",
    "comms_return_char",
)


class ScrapliTelnet(Telnet):
    def __init__(self, host: str, port: int) -> None:
        self.eof: bool
        super().__init__(host, port)


class TelnetTransport(Transport):
    def __init__(
        self,
        host: str,
        port: int = 23,
        auth_username: str = "",
        auth_public_key: str = "",
        auth_password: str = "",
        timeout_ssh: int = 5000,
        timeout_socket: int = 5,
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
            auth_public_key: path to public key for authentication
            auth_password: password for authentication
            timeout_socket: timeout for establishing socket in seconds
            timeout_ssh: timeout for ssh transport in milliseconds
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
        self.timeout_ssh: int = timeout_ssh
        self.timeout_socket: int = timeout_socket
        self.session_lock: Lock = Lock()
        self.auth_username: str = auth_username
        self.auth_public_key: str = auth_public_key
        self.auth_password: str = auth_password
        self.comms_prompt_pattern: str = comms_prompt_pattern
        self.comms_return_char: str = comms_return_char

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
        telnet_session = ScrapliTelnet(host=self.host, port=self.port)
        LOG.debug(f"Session to host {self.host} spawned")
        self.session_lock.release()
        self._authenticate(telnet_session)
        if not self._telnet_isauthenticated(telnet_session):
            raise ScrapliAuthenticationFailed(
                f"Could not authenticate over telnet to host: {self.host}"
            )
        LOG.debug(f"Authenticated to host {self.host} with password")
        print("SUCH GOOD SUCCESS")
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

    def _authenticate_username(self, telnet_session: ScrapliTelnet) -> None:
        """
        Private method to enter username for telnet authentication

        Args:
            telnet_session: Telnet session object

        Returns:
            N/A  # noqa: DAR202

        Raises:
            exc: if unknown (i.e. not auth failed) exception occurs

        """
        self.session_lock.acquire()
        try:
            attempt_count = 0
            while True:
                output = telnet_session.read_eager()
                if b"username:" in output.lower():
                    telnet_session.write(self.auth_username.encode())
                    telnet_session.write(self.comms_return_char.encode())
                    break
                attempt_count += 1
                if attempt_count > 1000:
                    break
        except self.lib_auth_exception as exc:
            LOG.critical(f"Did not see username prompt from {self.host} failed. Exception: {exc}.")
            raise exc
        finally:
            self.session_lock.release()

    def _authenticate_password(self, telnet_session: ScrapliTelnet) -> None:
        """
        Private method to enter password for telnet authentication

        Args:
            telnet_session: Telnet session object

        Returns:
            N/A  # noqa: DAR202

        Raises:
            exc: if unknown (i.e. not auth failed) exception occurs

        """
        self.session_lock.acquire()
        try:
            attempt_count = 0
            while True:
                output = telnet_session.read_eager()
                if b"password" in output.lower():
                    telnet_session.write(self.auth_password.encode())
                    telnet_session.write(self.comms_return_char.encode())
                    break
                attempt_count += 1
                if attempt_count > 1000:
                    break
        except self.lib_auth_exception as exc:
            LOG.critical(f"Password authentication with host {self.host} failed. Exception: {exc}.")
        except Exception as exc:
            LOG.critical(
                "Unknown error occurred during password authentication with host "
                f"{self.host}; Exception: {exc}"
            )
            raise exc
        finally:
            self.session_lock.release()

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
        Check if socket is alive and session is authenticated

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """

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
