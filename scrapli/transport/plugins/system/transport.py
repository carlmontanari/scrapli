"""scrapli.transport.plugins.system.transport"""
import sys
from dataclasses import dataclass
from typing import List, Optional

from scrapli.decorators import TransportTimeout
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
    def __init__(
        self, base_transport_args: BaseTransportArgs, plugin_transport_args: PluginTransportArgs
    ):
        super().__init__(base_transport_args=base_transport_args)
        self.plugin_transport_args = plugin_transport_args

        if sys.platform.startswith("win"):
            raise ScrapliUnsupportedPlatform("system transport is not supported on windows devices")

        self.open_cmd: List[str] = []
        self._build_open_cmd()
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
            if self.plugin_transport_args.ssh_known_hosts_file:
                self.open_cmd.extend(
                    ["-o", f"UserKnownHostsFile={self.plugin_transport_args.ssh_known_hosts_file}"]
                )

        if self.plugin_transport_args.ssh_config_file:
            self.open_cmd.extend(["-F", self.plugin_transport_args.ssh_config_file])
        else:
            self.open_cmd.extend(["-F", "/dev/null"])

        open_cmd_user_args = self._base_transport_args.transport_options.get("open_cmd", [])
        if isinstance(open_cmd_user_args, str):
            open_cmd_user_args = [open_cmd_user_args]
        self.open_cmd.extend(open_cmd_user_args)

        self.logger.debug(f"created transport 'open_cmd': '{self.open_cmd}'")

    def open(self) -> None:
        self._pre_open_closing_log(closing=False)

        self.session = PtyProcess.spawn(
            self.open_cmd,
            rows=self._base_transport_args.transport_options.get("ptyprocess", {}).get("rows", 24),
            cols=self._base_transport_args.transport_options.get("ptyprocess", {}).get("cols", 80),
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

    @TransportTimeout("timed out reading from transport")
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
