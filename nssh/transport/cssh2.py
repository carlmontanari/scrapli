"""nssh.transport.cssh2"""
import warnings
from logging import getLogger
from threading import Lock
from typing import Optional

from nssh.exceptions import MissingDependencies, NSSHAuthenticationFailed
from nssh.transport.socket import Socket
from nssh.transport.transport import Transport

LOG = getLogger("transport")


SSH2_TRANSPORT_ARGS = (
    "host",
    "port",
    "timeout_ssh",
    "timeout_socket",
    "auth_username",
    "auth_public_key",
    "auth_password",
)


class SSH2Transport(Socket, Transport):
    def __init__(
        self,
        host: str,
        port: int = 22,
        auth_username: str = "",
        auth_public_key: str = "",
        auth_password: str = "",
        timeout_ssh: int = 5000,
        timeout_socket: int = 5,
    ):
        """
        SSH2Transport Object

        Inherit from Transport ABC and Socket base class:
        SSH2Transport <- Transport (ABC)
        SSH2Transport <- Socket

        Args:
            host: host ip/name to connect to
            port: port to connect to
            auth_username: username for authentication
            auth_public_key: path to public key for authentication
            auth_password: password for authentication
            timeout_ssh: timeout for ssh2 transport in milliseconds
            timeout_socket: timeout for establishing socket in seconds

        Returns:
            N/A  # noqa

        Raises:
            Exception: if socket handshake fails
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

        try:
            # import here so these are optional
            from ssh2.channel import Channel  # pylint: disable=C0415
            from ssh2.session import Session  # pylint: disable=C0415
            from ssh2.exceptions import AuthenticationError  # pylint: disable=C0415

            self.lib_session = Session
            self.session: Session = None
            self.channel: Channel = None
            self.lib_auth_exception = AuthenticationError
        except ModuleNotFoundError as exc:
            err = f"Module '{exc.name}' not installed!"
            msg = f"***** {err} {'*' * (80 - len(err))}"
            fix = (
                f"To resolve this issue, install '{exc.name}'. You can do this in one of the "
                "following ways:\n"
                "1: 'pip install -r requirements-ssh2.txt'\n"
                "2: 'pip install nssh[ssh2]'"
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
            N/A  # noqa

        Returns:
            N/A  # noqa

        Raises:
            Exception: if socket handshake fails
            AuthenticationFailed: if all authentication means fail

        """
        if not self.socket_isalive():
            self.socket_open()
        self.session_lock.acquire()
        self.session = self.lib_session()
        self.set_timeout(self.timeout_ssh)
        try:
            self.session.handshake(self.sock)
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
            raise NSSHAuthenticationFailed(msg)
        self._open_channel()
        self.session_lock.release()

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
            self._authenticate_public_key()
            if self.isauthenticated():
                LOG.debug(f"Authenticated to host {self.host} with public key")
                return
        if self.auth_password:
            self._authenticate_password()
            if self.isauthenticated():
                LOG.debug(f"Authenticated to host {self.host} with password")
                return
            self._authenticate_keyboard_interactive()
            if self.isauthenticated():
                LOG.debug(f"Authenticated to host {self.host} with keyboard interactive")
                return
        return

    def _authenticate_public_key(self) -> None:
        """
        Attempt to authenticate with public key authentication

        Args:
            N/A  # noqa

        Returns:
            N/A  # noqa

        Raises:
            Exception: if unknown (i.e. not auth failed) exception occurs

        """
        try:
            self.session.userauth_publickey_fromfile(self.auth_username, self.auth_public_key)
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
            N/A  # noqa

        Returns:
            N/A  # noqa

        Raises:
            Exception: if unknown (i.e. not auth failed) exception occurs

        """
        try:
            self.session.userauth_password(self.auth_username, self.auth_password)
        except self.lib_auth_exception as exc:
            LOG.critical(f"Password authentication with host {self.host} failed. Exception: {exc}.")
        except Exception as exc:
            LOG.critical(
                "Unknown error occurred during password authentication with host "
                f"{self.host}; Exception: {exc}"
            )
            raise exc

    def _authenticate_keyboard_interactive(self) -> None:
        """
        Attempt to authenticate with keyboard interactive authentication

        Args:
            N/A  # noqa

        Returns:
            N/A  # noqa

        Raises:
            Exception: if unknown (i.e. not auth failed) exception occurs

        """
        try:
            self.session.userauth_keyboardinteractive(  # pylint: disable=C0415
                self.auth_username, self.auth_password
            )
        except AttributeError as exc:
            LOG.critical(
                "Keyboard interactive authentication not supported in your ssh2-python version. "
                f"Exception: {exc}"
            )
        except self.lib_auth_exception as exc:
            LOG.critical(
                f"Keyboard interactive authentication with host {self.host} failed. "
                f"Exception: {exc}."
            )
        except Exception as exc:
            LOG.critical(
                "Unknown error occurred during keyboard interactive authentication with host "
                f"{self.host}; Exception: {exc}"
            )
            raise exc

    def isauthenticated(self) -> bool:
        """
        Check if session is authenticated

        Args:
            N/A  # noqa

        Returns:
            authenticated: True if authenticated, else False

        Raises:
            N/A  # noqa

        """
        authenticated: bool = self.session.userauth_authenticated()
        return authenticated

    def _open_channel(self) -> None:
        """
        Open channel, acquire pty, request interactive shell

        Args:
            N/A  # noqa

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa

        """
        self.channel = self.session.open_session()
        self.channel.pty()
        self.channel.shell()
        LOG.debug(f"Channel to host {self.host} opened")

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
        self.channel.close()
        LOG.debug(f"Channel to host {self.host} closed")
        self.socket_close()
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
        if self.socket_isalive() and not self.channel.eof() and self.isauthenticated():
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
        output: bytes
        _, output = self.channel.read(65535)
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
        self.channel.write(channel_input)

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
        self.channel.flush()

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
        if isinstance(timeout, int):
            set_timeout = timeout
        else:
            set_timeout = self.timeout_ssh
        self.session.set_timeout(set_timeout)

    def set_blocking(self, blocking: bool = False) -> None:
        """
        Set session blocking configuration

        Args:
            blocking: True/False set session to blocking

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa

        """
        self.session.set_blocking(blocking)
