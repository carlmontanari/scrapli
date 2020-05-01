"""scrapli.driver.core.cisco_nxos.driver"""
from typing import Any, Callable, Dict, Optional

from scrapli.driver import NetworkDriver
from scrapli.driver.network_driver import PrivilegeLevel


def nxos_on_open(conn: NetworkDriver) -> None:
    """
    NXOSDriver default on_open callable

    Args:
        conn: NetworkDriver object

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A
    """
    conn.acquire_priv(desired_priv=conn.default_desired_privilege_level)
    conn.channel.send_input(channel_input="terminal length 0")
    conn.channel.send_input(channel_input="terminal width 511")


def nxos_on_close(conn: NetworkDriver) -> None:
    """
    NXOSDriver default on_close callable

    Args:
        conn: NetworkDriver object

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A
    """
    # write exit directly to the transport as channel would fail to find the prompt after sending
    # the exit command!
    conn.acquire_priv(desired_priv=conn.default_desired_privilege_level)
    conn.transport.write(channel_input="exit")
    conn.transport.write(channel_input=conn.channel.comms_prompt_pattern)


PRIVS = {
    "exec": (PrivilegeLevel(r"^[a-z0-9.\-@()/:]{1,32}>\s?$", "exec", "", "", "", False, "",)),
    "privilege_exec": (
        PrivilegeLevel(
            r"^[a-z0-9.\-@/:]{1,32}#\s?$",
            "privilege_exec",
            "exec",
            "disable",
            "enable",
            True,
            "Password:",
        )
    ),
    "configuration": (
        PrivilegeLevel(
            r"^[a-z0-9.\-@/:]{1,32}\(config[a-z0-9.\-@/:]{0,32}\)#\s?$",
            "configuration",
            "privilege_exec",
            "end",
            "configure terminal",
            False,
            "",
        )
    ),
}


class NXOSDriver(NetworkDriver):
    def __init__(
        self,
        on_open: Optional[Callable[..., Any]] = None,
        on_close: Optional[Callable[..., Any]] = None,
        auth_secondary: str = "",
        transport: str = "system",
        **kwargs: Dict[str, Any],
    ):
        """
        NXOSDriver Object

        Args:
            on_open: callable that accepts the class instance as its only argument. this callable,
                if provided, is executed immediately after authentication is completed. Common use
                cases for this callable would be to disable paging or accept any kind of banner
                message that prompts a user upon connection
            on_close: callable that accepts the class instance as its only argument. this callable,
                if provided, is executed immediately prior to closing the underlying transport.
                Common use cases for this callable would be to save configurations prior to exiting,
                or to logout properly to free up vtys or similar.
            auth_secondary: password to use for secondary authentication (enable)
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
        if on_open is None:
            on_open = nxos_on_open
        if on_close is None:
            on_close = nxos_on_close

        _telnet = False
        if transport == "telnet":
            _telnet = True

        super().__init__(
            privilege_levels=PRIVS,
            default_desired_privilege_level="privilege_exec",
            auth_secondary=auth_secondary,
            on_open=on_open,
            on_close=on_close,
            transport=transport,
            **kwargs,
        )

        if _telnet:
            self.transport.username_prompt = "login:"

        self.textfsm_platform = "cisco_nxos"
        self.genie_platform = "nxos"

        self.failed_when_contains = [
            "% Ambiguous command",
            "% Incomplete command",
            "% Invalid input detected",
            "% Invalid command at",
        ]
