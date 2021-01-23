"""scrapli.transport.plugins.asyncssh.transport"""
import asyncio
from dataclasses import dataclass
from typing import Optional

from asyncssh import connect
from asyncssh.connection import SSHClientConnection
from asyncssh.misc import ConnectionLost, PermissionDenied
from asyncssh.stream import SSHReader, SSHWriter

from scrapli.decorators import TransportTimeout
from scrapli.exceptions import (
    ScrapliAuthenticationFailed,
    ScrapliConnectionError,
    ScrapliConnectionNotOpened,
)
from scrapli.ssh_config import SSHKnownHosts
from scrapli.transport.base import AsyncTransport, BasePluginTransportArgs, BaseTransportArgs


@dataclass()
class PluginTransportArgs(BasePluginTransportArgs):
    auth_username: str
    auth_password: str = ""
    auth_private_key: str = ""
    auth_strict_key: bool = True
    ssh_config_file: str = ""
    ssh_known_hosts_file: str = ""


class AsyncsshTransport(AsyncTransport):
    def __init__(
        self, base_transport_args: BaseTransportArgs, plugin_transport_args: PluginTransportArgs
    ) -> None:
        super().__init__(base_transport_args=base_transport_args)
        self.plugin_transport_args = plugin_transport_args

        self.session: Optional[SSHClientConnection] = None
        self.stdout: Optional[SSHReader] = None
        self.stdin: Optional[SSHWriter] = None

    def _verify_key(self) -> None:
        """
        Verify target host public key, raise exception if invalid/unknown

        Args:
            N/A

        Returns:
            None

        Raises:
            ScrapliAuthenticationFailed: if host is not in known hosts

        """
        known_hosts = SSHKnownHosts(self.plugin_transport_args.ssh_known_hosts_file)

        if self._base_transport_args.host not in known_hosts.hosts.keys():
            raise ScrapliAuthenticationFailed(
                f"{self._base_transport_args.host} not in known_hosts!"
            )

    def _verify_key_value(self) -> None:
        """
        Verify target host public key, raise exception if invalid/unknown

        Args:
            N/A

        Returns:
            None

        Raises:
            ScrapliConnectionNotOpened: if session is unopened/None
            ScrapliAuthenticationFailed: if host is in known hosts but public key does not match

        """
        if not self.session:
            raise ScrapliConnectionNotOpened

        known_hosts = SSHKnownHosts(self.plugin_transport_args.ssh_known_hosts_file)

        remote_server_key = self.session.get_server_host_key()
        remote_public_key = remote_server_key.export_public_key().split()[1].decode()

        if known_hosts.hosts[self._base_transport_args.host]["public_key"] != remote_public_key:
            raise ScrapliAuthenticationFailed(
                f"{self._base_transport_args.host} in known_hosts but public key does not match!"
            )

    async def open(self) -> None:
        self._pre_open_closing_log(closing=False)

        if self.plugin_transport_args.auth_strict_key:
            self.logger.debug(
                f"Attempting to validate {self._base_transport_args.host} public key is in known "
                f"hosts"
            )
            self._verify_key()

        # we already fetched host/port/user from the user input and/or the ssh config file, so we
        # want to use those explicitly. likewise we pass config file we already found. set known
        # hosts and agent to None so we can not have an agent and deal w/ known hosts ourselves
        common_args = {
            "host": self._base_transport_args.host,
            "port": self._base_transport_args.port,
            "username": self.plugin_transport_args.auth_username,
            "known_hosts": None,
            "agent_path": None,
            "config": self.plugin_transport_args.ssh_config_file,
        }

        try:
            self.session = await asyncio.wait_for(
                connect(
                    client_keys=self.plugin_transport_args.auth_private_key,
                    password=self.plugin_transport_args.auth_password,
                    preferred_auth=(
                        "publickey",
                        "keyboard-interactive",
                        "password",
                    ),
                    **common_args,
                ),
                timeout=self._base_transport_args.timeout_socket,
            )
        except PermissionDenied as exc:
            msg = "all authentication methods failed"
            self.logger.critical(msg)
            raise ScrapliAuthenticationFailed(msg) from exc
        except asyncio.TimeoutError as exc:
            msg = "timed out opening connection to device"
            self.logger.critical(msg)
            raise ScrapliAuthenticationFailed(msg) from exc

        if not self.session:
            raise ScrapliConnectionNotOpened

        if self.plugin_transport_args.auth_strict_key:
            self.logger.debug(
                f"Attempting to validate {self._base_transport_args.host} public key is in known "
                f"hosts and is valid"
            )
            self._verify_key_value()

        self.stdin, self.stdout, _ = await self.session.open_session(
            term_type="xterm", encoding=None
        )

        self._post_open_closing_log(closing=False)

    def close(self) -> None:
        self._pre_open_closing_log(closing=True)

        if self.session:

            try:
                self.session.close()
            except BrokenPipeError:
                # it seems it is possible for the connection transport is_closing() to be true
                # already in some cases... since we are closing the connection anyway we will just
                # ignore this note that this seemed to only happen in github actions on
                # ubuntu-latest w/ py3.8...
                pass

        # always reset session/stdin/stdout back to None if we are closing!
        self.session = None
        self.stdin = None
        self.stdout = None

        self._post_open_closing_log(closing=True)

    def isalive(self) -> bool:
        if not self.session:
            return False

        # this may need to be revisited in the future, but this seems to be a good check for
        # aliveness
        try:
            if (
                self.session._auth_complete  # pylint:  disable=W0212
                and self.session._transport.is_closing() is False  # pylint:  disable=W0212
            ):
                return True
        except AttributeError:
            pass
        return False

    @TransportTimeout("timed out reading from transport")
    async def read(self) -> bytes:
        if not self.stdout:
            raise ScrapliConnectionNotOpened

        try:
            buf: bytes = await self.stdout.read(65535)
        except ConnectionLost as exc:
            msg = (
                "encountered EOF reading from transport; typically means the device closed the "
                "connection"
            )
            self.logger.critical(msg)
            raise ScrapliConnectionError(msg) from exc

        return buf

    def write(self, channel_input: bytes) -> None:
        if not self.stdin:
            raise ScrapliConnectionNotOpened
        self.stdin.write(channel_input)
