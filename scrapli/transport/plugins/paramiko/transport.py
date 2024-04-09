"""scrapli.transport.plugins.paramiko.transport"""

from contextlib import suppress
from dataclasses import dataclass
from typing import Optional

from paramiko import Channel
from paramiko import Transport as _ParamikoTransport
from paramiko.rsakey import RSAKey
from paramiko.ssh_exception import AuthenticationException

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


class ParamikoTransport(Transport):
    def __init__(
        self, base_transport_args: BaseTransportArgs, plugin_transport_args: PluginTransportArgs
    ) -> None:
        """
        Paramiko transport plugin.

        This transport supports some additional `transport_options` to control behavior --

        `enable_rsa2` is bool defaulting to `False`. Please see the paramiko changelog entry for
            version 2.9.0 here: https://www.paramiko.org/changelog.html. Basically, even though
            scrapli *tries* to default to safe/sane/secure things where possible, it is also focused
            on *network* devices which maybe sometimes are less up-to-date/safe/secure than we'd
            all hope. In this case paramiko 2.9.0 defaults to supporting only RSA2based servers,
            which, causes issues for the devices in the test suite, and likely for many other
            network devices out there. So, by default, we'll *disable* this. If you wish to enable
            this you can simply pass `True` to this transport option!

        Args:
            base_transport_args: scrapli base transport plugin arguments
            plugin_transport_args: paramiko ssh specific transport plugin arguments

        Returns:
            N/A

        Raises:
            N/A

        """
        super().__init__(base_transport_args=base_transport_args)
        self.plugin_transport_args = plugin_transport_args

        self.socket: Optional[Socket] = None
        self.session: Optional[_ParamikoTransport] = None
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

        try:
            self.session = _ParamikoTransport(self.socket.sock)  # type: ignore
            self.session.start_client()
        except Exception as exc:
            self.logger.critical("failed to complete handshake with host")
            raise ScrapliConnectionNotOpened from exc

        if self.plugin_transport_args.auth_strict_key:
            self.logger.debug(f"attempting to validate {self._base_transport_args.host} public key")
            self._verify_key()

        self._authenticate()

        if not self.session.is_authenticated():
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
            ScrapliAuthenticationFailed: if host is not in known hosts
            ScrapliAuthenticationFailed: if host is in known hosts but public key does not match

        """
        if not self.session:
            raise ScrapliConnectionNotOpened

        known_hosts = SSHKnownHosts(self.plugin_transport_args.ssh_known_hosts_file)
        known_host_public_key = known_hosts.lookup(self._base_transport_args.host)

        if not known_host_public_key:
            raise ScrapliAuthenticationFailed(
                f"{self._base_transport_args.host} not in known_hosts!"
            )

        remote_server_key = self.session.get_remote_server_key()
        remote_public_key = remote_server_key.get_base64()

        if known_host_public_key["public_key"] != remote_public_key:
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
            if self.session.is_authenticated():
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

        if self._base_transport_args.transport_options.get("enable_rsa2", False) is False:
            # do this for "keys" and "pubkeys": https://github.com/paramiko/paramiko/issues/1984
            self.session.disabled_algorithms = {
                "keys": ["rsa-sha2-256", "rsa-sha2-512"],
                "pubkeys": ["rsa-sha2-256", "rsa-sha2-512"],
            }

        try:
            paramiko_key = RSAKey(filename=self.plugin_transport_args.auth_private_key)
            self.session.auth_publickey(
                username=self.plugin_transport_args.auth_username, key=paramiko_key
            )
        except AuthenticationException:
            pass
        except Exception:  # pylint: disable=W0703
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

        with suppress(AuthenticationException):
            self.session.auth_password(
                username=self.plugin_transport_args.auth_username,
                password=self.plugin_transport_args.auth_password,
            )

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
        self._set_timeout(self._base_transport_args.timeout_transport)
        self.session_channel.get_pty()
        self.session_channel.invoke_shell()

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
        if not self.session:
            return False
        _isalive: bool = self.session.is_alive()
        return _isalive

    def read(self) -> bytes:
        if not self.session_channel:
            raise ScrapliConnectionNotOpened
        try:
            buf: bytes = self.session_channel.recv(65535)
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
        self.session_channel.send(channel_input)

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
        if not self.session_channel:
            raise ScrapliConnectionNotOpened
        self.session_channel.settimeout(value)
