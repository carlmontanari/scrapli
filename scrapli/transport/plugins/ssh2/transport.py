"""scrapli.transport.plugins.ssh2.transport"""
import base64
from dataclasses import dataclass
from typing import Optional

from ssh2.channel import Channel
from ssh2.exceptions import AuthenticationError, SSH2Error
from ssh2.session import Session

from scrapli.exceptions import (
    ScrapliAuthenticationFailed,
    ScrapliConnectionError,
    ScrapliConnectionNotOpened,
)
from scrapli.ssh_config import SSHKnownHosts
from scrapli.transport.base import BasePluginTransportArgs, BaseTransportArgs, Transport
from scrapli.transport.base.base_socket import Socket


@dataclass()
class PluginTransportArgs(BasePluginTransportArgs):
    auth_username: str
    auth_password: str = ""
    auth_private_key: str = ""
    auth_strict_key: bool = True
    ssh_config_file: str = ""
    ssh_known_hosts_file: str = ""


class Ssh2Transport(Transport):
    def __init__(
        self, base_transport_args: BaseTransportArgs, plugin_transport_args: PluginTransportArgs
    ) -> None:
        super().__init__(base_transport_args=base_transport_args)
        self.plugin_transport_args = plugin_transport_args

        self.socket: Optional[Socket] = None
        self.session: Optional[Session] = None
        self.session_channel: Optional[Channel] = None

    def open(self) -> None:
        self._pre_open_closing_log(closing=False)

        if not self.socket:
            self.socket = Socket(
                host=self._base_transport_args.host,
                port=self._base_transport_args.port,
                timeout=self._base_transport_args.timeout_socket,
            )

        if not self.socket.isalive():
            self.socket.open()

        self.session = Session()
        self._set_timeout(value=self._base_transport_args.timeout_transport)

        try:
            self.session.handshake(self.socket.sock)
        except Exception as exc:
            self.logger.critical("failed to complete handshake with host")
            raise ScrapliConnectionNotOpened from exc

        if self.plugin_transport_args.auth_strict_key:
            self.logger.debug(f"attempting to validate {self._base_transport_args.host} public key")
            self._verify_key()

        self._authenticate()

        if not self.session.userauth_authenticated():
            msg = "all authentication methods failed"
            self.logger.critical(msg)
            raise ScrapliAuthenticationFailed(msg)

        self._open_channel()

        self._post_open_closing_log(closing=False)

    def _verify_key(self) -> None:
        """
        Verify target host public key, raise exception if invalid/unknown

        Args:
            N/A

        Returns:
            None

        Raises:
            ScrapliConnectionNotOpened: if session is unopened/None
            ScrapliAuthenticationFailed: if public key verification fails

        """
        if not self.session:
            raise ScrapliConnectionNotOpened

        known_hosts = SSHKnownHosts(self.plugin_transport_args.ssh_known_hosts_file)

        if self._base_transport_args.host not in known_hosts.hosts.keys():
            raise ScrapliAuthenticationFailed(
                f"{self._base_transport_args.host} not in known_hosts!"
            )

        remote_server_key_info = self.session.hostkey()
        encoded_remote_server_key = remote_server_key_info[0]
        raw_remote_public_key = base64.encodebytes(encoded_remote_server_key)
        remote_public_key = raw_remote_public_key.replace(b"\n", b"").decode()

        if known_hosts.hosts[self._base_transport_args.host]["public_key"] != remote_public_key:
            raise ScrapliAuthenticationFailed(
                f"{self._base_transport_args.host} in known_hosts but public key does not match!"
            )

    def _authenticate(self) -> None:
        """
        Parent method to try all means of authentication

        Args:
            N/A

        Returns:
            None

        Raises:
            ScrapliConnectionNotOpened: if session is unopened/None
            ScrapliAuthenticationFailed: if auth fails

        """
        if not self.session:
            raise ScrapliConnectionNotOpened

        if self.plugin_transport_args.auth_private_key:
            self._authenticate_public_key()
            if self.session.userauth_authenticated():
                return
            if (
                not self.plugin_transport_args.auth_password
                or not self.plugin_transport_args.auth_username
            ):
                msg = (
                    f"Failed to authenticate to host {self._base_transport_args.host} with private "
                    f"key `{self.plugin_transport_args.auth_private_key}`. Unable to continue "
                    "authentication, missing username, password, or both."
                )
                raise ScrapliAuthenticationFailed(msg)

        self._authenticate_password()

    def _authenticate_public_key(self) -> None:
        """
        Attempt to authenticate with public key authentication

        Args:
            N/A

        Returns:
            None

        Raises:
            ScrapliConnectionNotOpened: if session is unopened/None

        """
        if not self.session:
            raise ScrapliConnectionNotOpened

        try:
            self.session.userauth_publickey_fromfile(
                self.plugin_transport_args.auth_username,
                self.plugin_transport_args.auth_private_key.encode(),
            )
        except (AuthenticationError, SSH2Error):
            pass

    def _authenticate_password(self) -> None:
        """
        Attempt to authenticate with password authentication

        Args:
            N/A

        Returns:
            None

        Raises:
            ScrapliConnectionNotOpened: if session is unopened/None

        """
        if not self.session:
            raise ScrapliConnectionNotOpened

        try:
            self.session.userauth_password(
                username=self.plugin_transport_args.auth_username,
                password=self.plugin_transport_args.auth_password,
            )
            return
        except AuthenticationError:
            pass
        try:
            self.session.userauth_keyboardinteractive(
                self.plugin_transport_args.auth_username, self.plugin_transport_args.auth_password
            )
        except AttributeError:
            msg = (
                "Keyboard interactive authentication may not be supported in your "
                "ssh2-python version."
            )
            self.logger.warning(msg)
        except AuthenticationError:
            pass

    def _open_channel(self) -> None:
        """
        Open channel, acquire pty, request interactive shell

        Args:
            N/A

        Returns:
            None

        Raises:
            ScrapliConnectionNotOpened: if session is unopened/None

        """
        if not self.session:
            raise ScrapliConnectionNotOpened

        self.session_channel = self.session.open_session()
        self.session_channel.pty()
        self.session_channel.shell()

    def close(self) -> None:
        self._pre_open_closing_log(closing=True)

        if self.session_channel:
            self.session_channel.close()

            if self.socket:
                self.socket.close()

        self.session = None
        self.session_channel = None

        self._post_open_closing_log(closing=True)

    def isalive(self) -> bool:
        if not self.session_channel:
            return False
        return not self.session_channel.eof()

    def read(self) -> bytes:
        if not self.session_channel:
            raise ScrapliConnectionNotOpened
        try:
            buf: bytes
            _, buf = self.session_channel.read(65535)
        except Exception as exc:
            msg = (
                "encountered EOF reading from transport; typically means the device closed the "
                "connection"
            )
            self.logger.critical(msg)
            raise ScrapliConnectionError(msg) from exc
        return buf

    def write(self, channel_input: bytes) -> None:
        if not self.session_channel:
            raise ScrapliConnectionNotOpened
        self.session_channel.write(channel_input)

    def _set_timeout(self, value: float) -> None:
        """
        Set session object timeout value

        Args:
            value: timeout in seconds

        Returns:
            None

        Raises:
            ScrapliConnectionNotOpened: if session is unopened/None

        """
        if not self.session:
            raise ScrapliConnectionNotOpened

        # ssh2-python expects timeout in milliseconds
        self.session.set_timeout(value * 1000)
