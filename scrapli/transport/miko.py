"""scrapli.transport.miko"""
import warnings
from logging import getLogger
from threading import Lock
from typing import Optional, Tuple

from scrapli.exceptions import (
    KeyVerificationFailed,
    MissingDependencies,
    ScrapliAuthenticationFailed,
)
from scrapli.ssh_config import SSHConfig, SSHKnownHosts
from scrapli.transport.socket import Socket
from scrapli.transport.transport import Transport

LOG = getLogger("transport")

MIKO_TRANSPORT_ARGS = (
    "auth_username",
    "auth_private_key",
    "auth_password",
    "auth_strict_key",
    "ssh_config_file",
    "ssh_known_hosts_file",
    "timeout_socket",
)


class MikoTransport(Transport):
    def __init__(
        self,
        host: str,
        port: int = -1,
        auth_username: str = "",
        auth_private_key: str = "",
        auth_password: str = "",
        auth_strict_key: bool = True,
        timeout_socket: int = 5,
        timeout_transport: int = 5,
        timeout_exit: bool = True,
        keepalive: bool = False,
        keepalive_interval: int = 30,
        keepalive_type: str = "",
        keepalive_pattern: str = "\005",
        ssh_config_file: str = "",
        ssh_known_hosts_file: str = "",
    ) -> None:
        """
        MikoTransport Object

        Inherit from Transport ABC
        MikoTransport <- Transport (ABC)

        Args:
            host: host ip/name to connect to
            port: port to connect to
            auth_username: username for authentication
            auth_private_key: path to private key for authentication
            auth_password: password for authentication
            auth_strict_key: True/False to enforce strict key checking (default is True)
            timeout_socket: timeout for establishing socket in seconds
            timeout_transport: timeout for ssh transport in seconds
            timeout_exit: True/False close transport if timeout encountered. If False and keepalives
                are in use, keepalives will prevent program from exiting so you should be sure to
                catch Timeout exceptions and handle them appropriately
            keepalive: whether or not to try to keep session alive
            keepalive_interval: interval to use for session keepalives
            keepalive_type: network|standard -- 'network' sends actual characters over the
                transport channel. This is useful for network-y type devices that may not support
                'standard' keepalive mechanisms. 'standard' is not currently implemented w/ paramiko
            keepalive_pattern: pattern to send to keep network channel alive. Default is
                u'\005' which is equivalent to 'ctrl+e'. This pattern moves cursor to end of the
                line which should be an innocuous pattern. This will only be entered *if* a lock
                can be acquired. This is only applicable if using keepalives and if the keepalive
                type is 'network'
            ssh_config_file: string to path for ssh config file
            ssh_known_hosts_file: string to path for ssh known hosts file

        Returns:
            N/A  # noqa: DAR202

        Raises:
            MissingDependencies: if paramiko is not installed

        """
        cfg_port, cfg_user, cfg_private_key = self._process_ssh_config(host, ssh_config_file)

        if port == -1:
            port = cfg_port or 22

        super().__init__(
            host,
            port,
            timeout_socket,
            timeout_transport,
            timeout_exit,
            keepalive,
            keepalive_interval,
            keepalive_type,
            keepalive_pattern,
        )

        self.auth_username: str = auth_username or cfg_user
        self.auth_private_key: str = auth_private_key or cfg_private_key
        self.auth_password: str = auth_password
        self.auth_strict_key: bool = auth_strict_key
        self.ssh_known_hosts_file: str = ssh_known_hosts_file

        self.session_lock: Lock = Lock()

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

        self.socket = Socket(host=self.host, port=self.port, timeout=self.timeout_socket)

    @staticmethod
    def _process_ssh_config(host: str, ssh_config_file: str) -> Tuple[Optional[int], str, str]:
        """
        Method to parse ssh config file

        In the future this may move to be a 'helper' function as it should be very similar between
        paramiko and and ssh2-python... for now it can be a static method as there may be varying
        supported args between the two transport drivers.

        Args:
            host: host to lookup in ssh config file
            ssh_config_file: string path to ssh config file; passed down from `Scrape`, or the
                `NetworkDriver` or subclasses of it, in most cases.

        Returns:
            Tuple: port to use for ssh, username to use for ssh, identity file (private key) to
                use for ssh auth

        Raises:
            N/A

        """
        ssh = SSHConfig(ssh_config_file)
        host_config = ssh.lookup(host)
        return host_config.port, host_config.user or "", host_config.identity_file or ""

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
        if not self.socket.socket_isalive():
            self.socket.socket_open()
        self.session_lock.acquire()
        try:
            self.session = self.lib_session(self.socket.sock)
            self.session.start_client()
        except Exception as exc:
            LOG.critical(f"Failed to complete handshake with host {self.host}; Exception: {exc}")
            self.session_lock.release()
            raise exc

        if self.auth_strict_key:
            LOG.debug(f"Attempting to validate {self.host} public key")
            self._verify_key()

        self.authenticate()
        if not self.isauthenticated():
            msg = f"Authentication to host {self.host} failed"
            LOG.critical(msg)
            self.session_lock.release()
            raise ScrapliAuthenticationFailed(msg)
        self._open_channel()
        self.session_lock.release()

        if self.keepalive:
            self._session_keepalive()

    def _verify_key(self) -> None:
        """
        Verify target host public key, raise exception if invalid/unknown

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            KeyVerificationFailed: if host is not in known hosts
            KeyVerificationFailed: if host is in known hosts but public key does not match

        """
        known_hosts = SSHKnownHosts(self.ssh_known_hosts_file)

        if self.host not in known_hosts.hosts.keys():
            raise KeyVerificationFailed(f"{self.host} not in known_hosts!")

        remote_server_key = self.session.get_remote_server_key()
        remote_public_key = remote_server_key.get_base64()

        if known_hosts.hosts[self.host]["public_key"] != remote_public_key:
            raise KeyVerificationFailed(
                f"{self.host} in known_hosts but public key does not match!"
            )

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
        if self.auth_private_key:
            self._authenticate_public_key()
            if self.isauthenticated():
                LOG.debug(f"Authenticated to host {self.host} with public key auth")
                return
            if not self.auth_password or not self.auth_username:
                msg = (
                    f"Public key authentication to host {self.host} failed. Missing username or"
                    " password unable to attempt password authentication."
                )
                LOG.critical(msg)
                raise ScrapliAuthenticationFailed(msg)
        self._authenticate_password()
        if self.isauthenticated():
            LOG.debug(f"Authenticated to host {self.host} with password")

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
            # paramiko wants to see its key in a PKey object when crafting the paramiko connection
            # from Transport and Channel objects
            from paramiko.rsakey import RSAKey  # pylint: disable=C0415

            paramiko_key = RSAKey(filename=self.auth_private_key)
            self.session.auth_publickey(self.auth_username, paramiko_key)
        except self.lib_auth_exception as exc:
            LOG.critical(
                f"Public key authentication with host {self.host} failed. Exception: {exc}."
            )
        except Exception as exc:  # pylint: disable=W0703
            LOG.critical(
                "Unknown error occurred during public key authentication with host "
                f"{self.host}; Exception: {exc}"
            )

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
        self.socket.socket_close()
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
        if self.socket.socket_isalive() and self.session.is_alive() and self.isauthenticated():
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

    def _keepalive_standard(self) -> None:
        """
        Send 'out of band' (protocol level) keepalives to devices.

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            NotImplementedError: always, because this is not implemented for telnet

        """
        raise NotImplementedError("No 'standard' keepalive mechanism for telnet.")
