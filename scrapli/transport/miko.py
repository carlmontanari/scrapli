"""scrapli.transport.miko"""
import warnings
from logging import getLogger
from threading import Lock
from typing import Optional

from scrapli.exceptions import MissingDependencies, ScrapliAuthenticationFailed
from scrapli.transport.socket import Socket
from scrapli.transport.transport import Transport

LOG = getLogger("transport")

MIKO_TRANSPORT_ARGS = (
    "host",
    "port",
    "timeout_transport",
    "timeout_socket",
    "auth_username",
    "auth_public_key",
    "auth_password",
)


class MikoTransport(Socket, Transport):
    def __init__(
        self,
        host: str,
        port: int = 22,
        auth_username: str = "",
        auth_public_key: str = "",
        auth_password: str = "",
        timeout_transport: int = 5000,
        timeout_socket: int = 5,
    ):
        """
        MikoTransport Object

        Inherit from Transport ABC and Socket base class:
        MikoTransport <- Transport (ABC)
        MikoTransport <- Socket

        Args:
            host: host ip/name to connect to
            port: port to connect to
            auth_username: username for authentication
            auth_public_key: path to public key for authentication
            auth_password: password for authentication
            timeout_socket: timeout for establishing socket in seconds
            timeout_transport: timeout for ssh transport in milliseconds

        Returns:
            N/A  # noqa: DAR202

        Raises:
            MissingDependencies: if paramiko is not installed

        """
        self.host: str = host
        self.port: int = port
        self.timeout_transport: int = timeout_transport
        self.timeout_socket: int = timeout_socket
        self.session_lock: Lock = Lock()
        self.auth_username: str = auth_username
        self.auth_public_key: str = auth_public_key
        self.auth_password: str = auth_password

        try:
            # import here so these are optional
            from paramiko import Transport as pTransport  # pylint: disable=C0415
            from paramiko import Channel  # pylint: disable=C0415
            from paramiko.ssh_exception import (  # pylint: disable=C0415
                AuthenticationException,
                SSHException,
            )

            self.lib_session = pTransport
            self.session: pTransport = None
            self.channel: Channel = None
            self.lib_auth_exception = AuthenticationException
        except ModuleNotFoundError as exc:
            err = f"Module '{exc.name}' not installed!"
            msg = f"***** {err} {'*' * (80 - len(err))}"
            fix = (
                f"To resolve this issue, install '{exc.name}'. You can do this in one of the "
                "following ways:\n"
                "1: 'pip install -r requirements-paramiko.txt'\n"
                "2: 'pip install scrapli[paramiko]'"
            )
            warning = "\n" + msg + "\n" + fix + "\n" + msg
            warnings.warn(warning)
            LOG.warning(warning)
            raise MissingDependencies

        super().__init__(host=self.host, port=self.port, timeout=self.timeout_socket)

    def open(self) -> None:
        """
        Parent method to open session, authenticate and acquire shell

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            exc: if socket handshake fails
            ScrapliAuthenticationFailed: if all authentication means fail

        """
        if not self.socket_isalive():
            self.socket_open()
        self.session_lock.acquire()
        try:
            self.session = self.lib_session(self.sock)
            self.session.start_client()
        except Exception as exc:
            LOG.critical(
                f"Failed to complete handshake with host {self.host}; " f"Exception: {exc}"
            )
            raise exc
        LOG.debug(f"Session to host {self.host} opened")
        self.authenticate()
        if not self.isauthenticated():
            msg = f"Authentication to host {self.host} failed"
            LOG.critical(msg)
            raise ScrapliAuthenticationFailed(msg)
        self._open_channel()
        self.session_lock.release()

    def authenticate(self) -> None:
        """
        Parent method to try all means of authentication

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        if self.auth_public_key:
            self._authenticate_public_key()
            if self.isauthenticated():
                LOG.debug(f"Authenticated to host {self.host} with public key")
                return
        if self.auth_password:
            self._authenticate_password()
            if self.isauthenticated():
                LOG.debug(f"Authenticated to host {self.host} with password")
                return
        return

    def _authenticate_public_key(self) -> None:
        """
        Attempt to authenticate with public key authentication

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            exc: if unknown (i.e. not auth failed) exception occurs

        """
        try:
            self.session.auth_publickey(self.auth_username, self.auth_public_key)
        except self.lib_auth_exception as exc:
            LOG.critical(
                f"Public key authentication with host {self.host} failed. Exception: {exc}."
            )
        except Exception as exc:
            LOG.critical(
                "Unknown error occurred during public key authentication with host "
                f"{self.host}; Exception: {exc}"
            )
            raise exc

    def _authenticate_password(self) -> None:
        """
        Attempt to authenticate with password authentication

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            exc: if unknown (i.e. not auth failed) exception occurs

        """
        try:
            self.session.auth_password(self.auth_username, self.auth_password)
        except self.lib_auth_exception as exc:
            LOG.critical(
                f"Password authentication with host {self.host} failed. Exception: {exc}."
                "\n\tNote: Paramiko automatically attempts both standard auth as well as keyboard "
                "interactive auth. Paramiko exception about bad auth type may be misleading!"
            )
        except Exception as exc:
            LOG.critical(
                "Unknown error occurred during password authentication with host "
                f"{self.host}; Exception: {exc}"
            )
            raise exc

    def isauthenticated(self) -> bool:
        """
        Check if session is authenticated

        Args:
            N/A

        Returns:
            bool: True if authenticated, else False

        Raises:
            N/A

        """
        authenticated: bool = self.session.is_authenticated()
        return authenticated

    def _open_channel(self) -> None:
        """
        Open channel, acquire pty, request interactive shell

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.channel = self.session.open_session()
        self.set_timeout(self.timeout_transport)
        self.channel.get_pty()
        self.channel.invoke_shell()
        LOG.debug(f"Channel to host {self.host} opened")

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
        self.channel.close()
        LOG.debug(f"Channel to host {self.host} closed")
        self.socket_close()
        self.session_lock.release()

    def isalive(self) -> bool:
        """
        Check if socket is alive and session is authenticated

        Args:
            N/A

        Returns:
            bool: True if socket is alive and session authenticated, else False

        Raises:
            N/A

        """
        if self.socket_isalive() and self.session.is_alive() and self.isauthenticated():
            return True
        return False

    def read(self) -> bytes:
        """
        Read data from the channel

        Args:
            N/A

        Returns:
            bytes: bytes output as read from channel

        Raises:
            N/A

        """
        channel_read: bytes = self.channel.recv(65535)
        return channel_read

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
        self.channel.send(channel_input)

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
        if isinstance(timeout, int):
            set_timeout = timeout
        else:
            set_timeout = self.timeout_transport
        self.channel.settimeout(set_timeout)

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
        self.channel.setblocking(blocking)
        self.set_timeout()
