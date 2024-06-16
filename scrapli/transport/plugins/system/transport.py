"""scrapli.transport.plugins.system.transport"""

import sys
from dataclasses import dataclass
from typing import List, Optional

from scrapli.decorators import timeout_wrapper
from scrapli.exceptions import (
    ScrapliConnectionError,
    ScrapliConnectionNotOpened,
    ScrapliUnsupportedPlatform,
)
from scrapli.transport.base import BasePluginTransportArgs, BaseTransportArgs, Transport
from scrapli.transport.plugins.system.ptyprocess import PtyProcess


@dataclass()
class PluginTransportArgs(BasePluginTransportArgs):
    auth_username: str
    auth_private_key: str = ""
    auth_strict_key: bool = True
    ssh_config_file: str = ""
    ssh_known_hosts_file: str = ""


class SystemTransport(Transport):
    SSH_SYSTEM_CONFIG_MAGIC_STRING: str = "SYSTEM_TRANSPORT_SSH_CONFIG_TRUE"
    SSH_SYSTEM_KNOWN_HOSTS_FILE_MAGIC_STRING: str = "SYSTEM_TRANSPORT_KNOWN_HOSTS_TRUE"

    def __init__(
        self, base_transport_args: BaseTransportArgs, plugin_transport_args: PluginTransportArgs
    ) -> None:
        """
        System (i.e. /bin/ssh) transport plugin.

        This transport supports some additional `transport_options` to control behavior --

        `ptyprocess` is a dictionary that has the following options:
            rows: integer number of rows for ptyprocess "window"
            cols: integer number of cols for ptyprocess "window"
            echo: defaults to `True`, passing `False` disables echo in the ptyprocess; should only
                be used with scrapli-netconf, will break scrapli!

        `netconf_force_pty` is a scrapli-netconf only argument. This setting defaults to `True` and
            allows you to *not* force a pty. This setting seems to only be necessary when connecting
            to juniper devices on port 830 as junos decides to not allocate a pty on that port for
            some reason!

        Args:
            base_transport_args: scrapli base transport plugin arguments
            plugin_transport_args: system ssh specific transport plugin arguments

        Returns:
            N/A

        Raises:
            ScrapliUnsupportedPlatform: if system is windows

        """
        super().__init__(base_transport_args=base_transport_args)
        self.plugin_transport_args = plugin_transport_args

        if sys.platform.startswith("win"):
            raise ScrapliUnsupportedPlatform("system transport is not supported on windows devices")

        self.open_cmd: List[str] = []
        self.session: Optional[PtyProcess] = None

    def _build_open_cmd(self) -> None:
        """
        Method to craft command to open ssh session

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        if self.open_cmd:
            self.open_cmd = []

        self.open_cmd.extend(["ssh", self._base_transport_args.host])
        self.open_cmd.extend(["-p", str(self._base_transport_args.port)])

        self.open_cmd.extend(
            ["-o", f"ConnectTimeout={int(self._base_transport_args.timeout_socket)}"]
        )
        self.open_cmd.extend(
            ["-o", f"ServerAliveInterval={int(self._base_transport_args.timeout_transport)}"]
        )

        if self.plugin_transport_args.auth_private_key:
            self.open_cmd.extend(["-i", self.plugin_transport_args.auth_private_key])
        if self.plugin_transport_args.auth_username:
            self.open_cmd.extend(["-l", self.plugin_transport_args.auth_username])

        if self.plugin_transport_args.auth_strict_key is False:
            self.open_cmd.extend(["-o", "StrictHostKeyChecking=no"])
            self.open_cmd.extend(["-o", "UserKnownHostsFile=/dev/null"])
        else:
            self.open_cmd.extend(["-o", "StrictHostKeyChecking=yes"])

            if (
                self.plugin_transport_args.ssh_known_hosts_file
                == self.SSH_SYSTEM_KNOWN_HOSTS_FILE_MAGIC_STRING
            ):
                self.logger.debug(
                    "Using system transport and ssh_known_hosts_file is True, not specifying any "
                    "known_hosts file"
                )
            elif self.plugin_transport_args.ssh_known_hosts_file:
                self.open_cmd.extend(
                    [
                        "-o",
                        f"UserKnownHostsFile={self.plugin_transport_args.ssh_known_hosts_file}",
                    ]
                )
            else:
                self.logger.debug("No known hosts file specified")
        if not self.plugin_transport_args.ssh_config_file:
            self.open_cmd.extend(["-F", "/dev/null"])
        elif self.plugin_transport_args.ssh_config_file == self.SSH_SYSTEM_CONFIG_MAGIC_STRING:
            self.logger.debug(
                "Using system transport and ssh_config is True, not specifying any SSH config"
            )
        else:
            self.open_cmd.extend(["-F", self.plugin_transport_args.ssh_config_file])

        open_cmd_user_args = self._base_transport_args.transport_options.get("open_cmd", [])
        if isinstance(open_cmd_user_args, str):
            open_cmd_user_args = [open_cmd_user_args]
        self.open_cmd.extend(open_cmd_user_args)

        self.logger.debug(f"created transport 'open_cmd': '{self.open_cmd}'")

    def open(self) -> None:
        self._pre_open_closing_log(closing=False)

        if not self.open_cmd:
            self._build_open_cmd()

        self.session = PtyProcess.spawn(
            self.open_cmd,
            echo=self._base_transport_args.transport_options.get("ptyprocess", {}).get(
                "echo", True
            ),
            rows=self._base_transport_args.transport_options.get("ptyprocess", {}).get("rows", 80),
            cols=self._base_transport_args.transport_options.get("ptyprocess", {}).get("cols", 256),
        )

        self._post_open_closing_log(closing=False)

    def close(self) -> None:
        self._pre_open_closing_log(closing=True)

        if self.session:
            self.session.close()

        self.session = None

        self._post_open_closing_log(closing=True)

    def isalive(self) -> bool:
        if not self.session:
            return False
        if self.session.isalive() and not self.session.eof():
            return True
        return False

    @timeout_wrapper
    def read(self) -> bytes:
        if not self.session:
            raise ScrapliConnectionNotOpened
        try:
            buf = self.session.read(65535)
        except EOFError as exc:
            msg = (
                "encountered EOF reading from transport; typically means the device closed the "
                "connection"
            )
            self.logger.critical(msg)
            raise ScrapliConnectionError(msg) from exc

        return buf

    def write(self, channel_input: bytes) -> None:
        if not self.session:
            raise ScrapliConnectionNotOpened
        self.session.write(channel_input)
