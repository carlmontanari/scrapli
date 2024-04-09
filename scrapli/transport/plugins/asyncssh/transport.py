"""scrapli.transport.plugins.asyncssh.transport"""

import asyncio
from contextlib import suppress
from dataclasses import dataclass
from typing import Any, Dict, Optional

from asyncssh.connection import SSHClientConnection, connect
from asyncssh.misc import ConnectionLost, PermissionDenied
from asyncssh.stream import SSHReader, SSHWriter

from scrapli.decorators import timeout_wrapper
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
        """
        Asyncssh transport plugin.

        Important note: some ssh servers may refuse connections if too many ssh host key algorithms
        are passed to it during the connection opening -- Asyncssh sends a bunch by default! If you
        encounter this issue, you can simply update your SSH config file to set a smaller (or one)
        number of ssh host key algorithms to work around this like so:

        ```
        Host *
            HostKeyAlgorithms ssh-rsa
        ```

        Thank you to @davaeron [https://github.com/davaeron] for reporting this in #173, see also
        asyncssh #323 here: https://github.com/ronf/asyncssh/issues/323.

        This transport supports some additional `transport_options` to control behavior --
        `asyncssh` is a dictionary that contains options that are passed directly to asyncssh during
        connection creation, you can find the SSH Client options of asyncssh here:
        https://asyncssh.readthedocs.io/en/latest/api.html#sshclientconnectionoptions.

        Below is an example of passing in options to modify kex and encryption algorithms

        ```
        device = {
            "host": "localhost",
            "transport_options": {
                "asyncssh": {
                    "kex_algs": ["diffie-hellman-group14-sha1", "diffie-hellman-group1-sha1"],
                    "encryption_algs": ["aes256-cbc", "aes192-cbc", "aes256-ctr", "aes192-ctr"],
                }
            },
            "platform": "cisco_iosxe"
        }

        conn = Scrapli(**device)
        ```

        Args:
            base_transport_args: scrapli base transport plugin arguments
            plugin_transport_args: asyncssh ssh specific transport plugin arguments

        Returns:
            N/A

        Raises:
            N/A

        """
        super().__init__(base_transport_args=base_transport_args)
        self.plugin_transport_args = plugin_transport_args

        self.session: Optional[SSHClientConnection] = None
        self.stdout: Optional[SSHReader[Any]] = None
        self.stdin: Optional[SSHWriter[Any]] = None

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
        known_host_public_key = known_hosts.lookup(self._base_transport_args.host)

        if not known_host_public_key:
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
            ScrapliAuthenticationFailed: if host is in known hosts but public key does not match or
                cannot glean remote server key from session.

        """
        if not self.session:
            raise ScrapliConnectionNotOpened

        known_hosts = SSHKnownHosts(self.plugin_transport_args.ssh_known_hosts_file)
        known_host_public_key = known_hosts.lookup(self._base_transport_args.host)

        remote_server_key = self.session.get_server_host_key()
        if remote_server_key is None:
            raise ScrapliAuthenticationFailed(
                f"failed gleaning remote server ssh key for host {self._base_transport_args.host}"
            )

        remote_public_key = remote_server_key.export_public_key().split()[1].decode()

        if known_host_public_key["public_key"] != remote_public_key:
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
        # hosts and agent to None so we can not have an agent and deal w/ known hosts ourselves.
        # to use ssh-agent either pass an empty tuple (to pick up ssh-agent socket from
        # SSH_AUTH_SOCK), or pass an explicit path to ssh-agent socket should be provided as part
        # of transport_options -- in either case these get merged into the dict *after* we set the
        # default value of `None`, so users options override our defaults.

        common_args: Dict[str, Any] = {
            "host": self._base_transport_args.host,
            "port": self._base_transport_args.port,
            "username": self.plugin_transport_args.auth_username,
            "known_hosts": None,
            "agent_path": None,
            "config": self.plugin_transport_args.ssh_config_file,
        }

        # Allow passing `transport_options` to asyncssh
        common_args.update(self._base_transport_args.transport_options.get("asyncssh", {}))

        # Common authentication args
        auth_args: Dict[str, Any] = {
            "client_keys": self.plugin_transport_args.auth_private_key,
            "password": self.plugin_transport_args.auth_password,
            "preferred_auth": (
                "publickey",
                "keyboard-interactive",
                "password",
            ),
        }

        # The session args to use in connect() - to merge the dicts in
        # the order to have transport options preference over predefined auth args
        conn_args = {**auth_args, **common_args}

        try:
            self.session = await asyncio.wait_for(
                connect(**conn_args),
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
            with suppress(BrokenPipeError):
                # this may raise a BrokenPipeError because seems it is possible for the connection
                # transport is_closing() to be true already in some cases... since we are closing
                # the connection anyway we will just ignore this note that this seemed to only
                # happen in github actions on ubuntu-latest w/ py3.8... hence the suppress!
                self.session.close()

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
        with suppress(AttributeError):
            if (
                self.session._auth_complete  # pylint:  disable=W0212
                and self.session._transport is not None  # pylint:  disable=W0212
                and self.session._transport.is_closing() is False  # pylint:  disable=W0212
            ):
                return True

        return False

    @timeout_wrapper
    async def read(self) -> bytes:
        if not self.stdout:
            raise ScrapliConnectionNotOpened

        if self.stdout.at_eof():
            raise ScrapliConnectionError("transport at EOF; no more data to be read")

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
