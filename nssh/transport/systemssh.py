"""nssh.transport.systemssh"""
from logging import getLogger
from subprocess import PIPE, Popen
from threading import Lock
from typing import Optional

from nssh.exceptions import NSSHAuthenticationFailed
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

        self.lib_session = Popen
        self.session: Popen[bytes]  # pylint: disable=E1136
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
        open_cmd = ["ssh", self.host, "-l", "carl"]
        self.session = self.lib_session(
            open_cmd, bufsize=0, shell=False, stdin=PIPE, stdout=PIPE, stderr=PIPE,
        )
        self.session_lock.release()

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
        self.session.kill()
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
        # TODO add isauthenticated
        # if self.socket_isalive() and self.isauthenticated():
        #     return True
        if self.session.poll() is None:
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
        output = self.session.stdout.read(65535)
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
        self.session.stdin.write(channel_input.encode())

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
        self.session.stdout.flush()

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
