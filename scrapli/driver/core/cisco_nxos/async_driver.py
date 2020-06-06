"""scrapli.driver.core.cisco_nxos.async_driver"""
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional

from scrapli.driver import AsyncNetworkDriver
from scrapli.driver.base_network_driver import PrivilegeLevel
from scrapli.driver.core.cisco_nxos.base_driver import PRIVS, NXOSDriverBase


async def nxos_on_open(conn: AsyncNetworkDriver) -> None:
    """
    AsyncNXOSDriver default on_open callable

    Args:
        conn: NetworkDriver object

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A
    """
    await conn.send_command(command="terminal length 0")
    await conn.send_command(command="terminal width 511")


async def nxos_on_close(conn: AsyncNetworkDriver) -> None:
    """
    AsyncNXOSDriver default on_close callable

    Args:
        conn: NetworkDriver object

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A
    """
    # write exit directly to the transport as channel would fail to find the prompt after sending
    # the exit command!
    await conn.acquire_priv(desired_priv=conn.default_desired_privilege_level)
    conn.transport.write(channel_input="exit")
    conn.transport.write(channel_input=conn.channel.comms_return_char)


class AsyncNXOSDriver(AsyncNetworkDriver, NXOSDriverBase):
    def __init__(
        self,
        privilege_levels: Optional[Dict[str, PrivilegeLevel]] = None,
        default_desired_privilege_level: str = "privilege_exec",
        auth_secondary: str = "",
        on_open: Optional[Callable[..., Any]] = None,
        on_close: Optional[Callable[..., Any]] = None,
        textfsm_platform: str = "cisco_nxos",
        genie_platform: str = "nxos",
        failed_when_contains: Optional[List[str]] = None,
        transport: str = "system",
        **kwargs: Dict[str, Any],
    ):
        """
        NXOSDriver Object

        Args:
            privilege_levels: optional user provided privilege levels, if left None will default to
                scrapli standard privilege levels
            default_desired_privilege_level: string of name of default desired priv, this is the
                priv level that is generally used to disable paging/set terminal width and things
                like that upon first login, and is also the priv level scrapli will try to acquire
                for normal "command" operations (`send_command`, `send_commands`)
            auth_secondary: password to use for secondary authentication (enable)
            on_open: callable that accepts the class instance as its only argument. this callable,
                if provided, is executed immediately after authentication is completed. Common use
                cases for this callable would be to disable paging or accept any kind of banner
                message that prompts a user upon connection
            on_close: callable that accepts the class instance as its only argument. this callable,
                if provided, is executed immediately prior to closing the underlying transport.
                Common use cases for this callable would be to save configurations prior to exiting,
                or to logout properly to free up vtys or similar.
            textfsm_platform: string name of textfsm parser platform
            genie_platform: string name of cisco genie parser platform
            failed_when_contains: List of strings that indicate a command/config has failed
            transport: system|telnet or a plugin -- type of transport to use for connection
                system uses system available ssh (/usr/bin/ssh)
                ssh2 uses ssh2-python *has been migrated to a plugin
                paramiko uses... paramiko *has been migrated to a plugin
                telnet uses telnetlib
                choice of driver depends on the features you need. in general system is easiest as
                it will just 'auto-magically' use your ssh config file ('~/.ssh/config' or
                '/etc/ssh/config_file'). ssh2 is very very fast as it is a thin wrapper around
                libssh2 however it is slightly feature limited. paramiko is slower than ssh2, but
                has more features built in (though scrapli does not expose/support them all).
                explicitly added here to allow for nicely checking if transport is telnet.
            **kwargs: keyword args to pass to inherited class(es)

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A
        """
        if privilege_levels is None:
            privilege_levels = deepcopy(PRIVS)

        if on_open is None:
            on_open = nxos_on_open
        if on_close is None:
            on_close = nxos_on_close

        _telnet = False
        if transport == "telnet":
            _telnet = True

        if failed_when_contains is None:
            failed_when_contains = [
                "% Ambiguous command",
                "% Incomplete command",
                "% Invalid input detected",
                "% Invalid command at",
            ]

        super().__init__(
            privilege_levels=privilege_levels,
            default_desired_privilege_level=default_desired_privilege_level,
            auth_secondary=auth_secondary,
            failed_when_contains=failed_when_contains,
            textfsm_platform=textfsm_platform,
            genie_platform=genie_platform,
            on_open=on_open,
            on_close=on_close,
            transport=transport,
            **kwargs,
        )

        if _telnet:
            self.transport.username_prompt = "login:"

    async def _abort_config(self) -> None:
        """
        Abort NXOS configuration session (if using a config session!)

        Args:
            N/A

        Returns:
            N/A:  # noqa: DAR202

        Raises:
            N/A

        """
        # nxos pattern for config sessions should *always* have `config-s`
        if "config\\-s" in self._current_priv_level.pattern:
            await self.channel.send_input(channel_input="abort")
            self._current_priv_level = self.privilege_levels["privilege_exec"]

    def register_configuration_session(self, session_name: str) -> None:
        """
        NXOS specific implementation of register_configuration_session

        Args:
            session_name: name of session to register

        Returns:
            N/A:  # noqa: DAR202

        Raises:
            N/A

        """
        self._create_configuration_session(session_name=session_name)
        self.update_privilege_levels(update_channel=True)
