"""nssh.transport.systemssh"""
import re
from logging import getLogger
from select import select
from threading import Lock
from typing import Optional

from nssh.exceptions import NSSHAuthenticationFailed
from nssh.helper import get_prompt_pattern
from nssh.transport.ptyprocess import PtyProcess
from nssh.transport.transport import Transport

LOG = getLogger(f"{__name__}_transport")

SYSTEM_SSH_TRANSPORT_ARGS = (
    "host",
    "port",
    "timeout_ssh",
    "timeout_socket",
    "auth_username",
    "auth_public_key",
    "auth_password",
    "comms_return_char",
)


class SystemSSHTransport(Transport):
    def __init__(
        self,
        host: str,
        port: int = 22,
        timeout_ssh: int = 5000,
        timeout_socket: int = 5,
        auth_username: str = "",
        auth_public_key: str = "",
        auth_password: str = "",
        comms_prompt_pattern: str = r"^[a-z0-9.\-@()/:]{1,32}[#>$]$",
        comms_return_char: str = "\n",
    ):  # pylint: disable=W0231
        """
        SystemSSHTransport Object

        Inherit from Transport ABC
        SSH2Transport <- Transport (ABC)

        Args:
            host: host ip/name to connect to
            port: port to connect to
            timeout_ssh: timeout for ssh2 transport in milliseconds
            timeout_socket: timeout for establishing socket in seconds
            auth_username: username for authentication
            auth_public_key: path to public key for authentication
            auth_password: password for authentication
            comms_prompt_pattern: prompt pattern expected for device, same as the one provided to
                channel -- system ssh needs to know this to know how to decide if we are properly
                sending/receiving data -- i.e. we are not stuck at some password prompt or some
                other failure scenario. If using driver, this should be passed from driver (NSSH, or
                IOSXE, etc.) to this Transport class.
            comms_return_char: return character to use on the channel, same as the one provided to
                channel -- system ssh needs to know this to know what to send so that we can probe
                the channel to make sure we are authenticated and sending/receiving data. If using
                driver, this should be passed from driver (NSSH, or IOSXE, etc.) to this Transport
                class.

        Returns:
            N/A  # noqa

        Raises:
            AuthenticationFailed: if all authentication means fail

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

        self.lib_session = PtyProcess
        self.session: PtyProcess  # pylint: disable=E1136
        self.lib_auth_exception = NSSHAuthenticationFailed

    def open(self) -> None:
        """
        Parent method to open session, authenticate and acquire shell

        Args:
            N/A  # noqa

        Returns:
            N/A  # noqa

        Raises:
            Exception: if socket handshake fails
            AuthenticationFailed: if all authentication means fail

        """
        self.session_lock.acquire()
        # TODO -- construct open command -- this means parsing ssh keys and such prior to getting
        #  here in case users dont want to just rely on their ssh config file
        open_cmd = ["ssh", self.host, "-l", "STi305"]
        self.session = PtyProcess.spawn(open_cmd)
        LOG.debug(f"Session to host {self.host} spawned")
        self.authenticate()
        # need to release the lock so isauthenticated can acquire it...
        self.session_lock.release()
        if not self.isauthenticated():
            msg = f"Authentication to host {self.host} failed"
            LOG.critical(msg)
            raise NSSHAuthenticationFailed(msg)

    def authenticate(self) -> None:
        """
        Parent method to try all means of authentication

        Args:
            N/A  # noqa

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa

        """
        if self.auth_public_key:
            LOG.debug(f"Authenticated to host {self.host} with public key")
            # TODO - just assuming we are working w/ keys and this works for now...
            return
        if self.auth_password:
            self._authenticate_password()
            LOG.debug(f"Authenticated to host {self.host} with password")
            # TODO - just assuming password auth works -- need to implement `isauthenticated`
            return
        return

    def _authenticate_password(self) -> None:
        """
        Attempt to authenticate with password authentication

        Args:
            N/A  # noqa

        Returns:
            N/A  # noqa

        Raises:
            Exception: if unknown (i.e. not auth failed) exception occurs

        """
        try:
            attempt_count = 0
            while True:
                output = self.read()
                if b"password" in output.lower():
                    self.write(self.auth_password)
                    self.write("\n")
                    break
                attempt_count += 1
                if attempt_count > 250:
                    raise self.lib_auth_exception
        except self.lib_auth_exception as exc:
            LOG.critical(f"Password authentication with host {self.host} failed. Exception: {exc}.")
        except Exception as exc:
            LOG.critical(
                "Unknown error occurred during password authentication with host "
                f"{self.host}; Exception: {exc}"
            )
            raise exc

    def isauthenticated(self) -> bool:
        """
        Check if session is authenticated

        This is very naive -- it only knows if the sub process is alive and has not received an EOF.
        Beyond that we lock the session and send the return character and re-read the channel.

        Args:
            N/A  # noqa

        Returns:
            authenticated: True if authenticated, else False

        Raises:
            N/A  # noqa

        """
        if self.session.isalive() and not self.session.eof():
            prompt_pattern = get_prompt_pattern("", self.comms_prompt_pattern)
            self.session_lock.acquire()
            self.write(self.comms_return_char)
            fd_ready, _, _ = select([self.session.fd], [], [], 0)
            if self.session.fd in fd_ready:
                # TODO -- it seems that i need two reads here...? doesn't seem to be a problem
                #  elsewhere though...? not sure whats going on
                self.read()
                output = self.read()
                output_copy = output.decode("unicode_escape").strip()
                output_copy = re.sub("\r", "\n", output_copy)
                channel_match = re.search(prompt_pattern, output_copy)
                if channel_match:
                    self.session_lock.release()
                    return True
        self.session_lock.release()
        return False

    def close(self) -> None:
        """
        Close session and socket

        Args:
            N/A  # noqa

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa

        """
        self.session_lock.acquire()
        self.session.kill(1)
        LOG.debug(f"Channel to host {self.host} closed")
        self.session_lock.release()

    def isalive(self) -> bool:
        """
        Check if socket is alive and session is authenticated

        Args:
            N/A  # noqa

        Returns:
            bool: True if socket is alive and session authenticated, else False

        Raises:
            N/A  # noqa

        """
        if self.session.isalive() and self.isauthenticated() and not self.session.eof():
            return True
        return False

    def read(self) -> bytes:
        """
        Read data from the channel

        Args:
            N/A  # noqa

        Returns:
            bytes_read: int of bytes read
            output: bytes output as read from channel

        Raises:
            N/A  # noqa

        """
        # TODO what value should read be...?
        output: bytes = self.session.read(65535)
        return output

    def write(self, channel_input: str) -> None:
        """
        Write data to the channel

        Args:
            channel_input: string to send to channel

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa

        """
        self.session.write(channel_input.encode())

    def flush(self) -> None:
        """
        Flush channel stdout stream

        Args:
            N/A  # noqa

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa

        """
        self.session.flush()

    def set_timeout(self, timeout: Optional[int] = None) -> None:
        """
        Set session timeout

        Args:
            timeout: timeout in seconds

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa

        """
        # TODO would be good to be able to set this?? Or is it unnecessary for popen??

    def set_blocking(self, blocking: bool = False) -> None:
        """
        Set session blocking configuration

        Unnecessary when using Popen/system ssh

        Args:
            blocking: True/False set session to blocking

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa

        """
