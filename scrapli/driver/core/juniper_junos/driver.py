"""scrapli.driver.core.juniper_junos.driver"""
from typing import Any, Callable, Dict, Optional

from scrapli.driver import NetworkDriver
from scrapli.driver.network_driver import PrivilegeLevel


def junos_on_open(conn: NetworkDriver) -> None:
    """
    JunosDriver default on_open callable

    Args:
        conn: NetworkDriver object

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A
    """
    conn.acquire_priv(desired_priv=conn.default_desired_privilege_level)
    conn.channel.send_input(channel_input="set cli complete-on-space off")
    conn.channel.send_input(channel_input="set cli screen-length 0")
    conn.channel.send_input(channel_input="set cli screen-width 511")


def junos_on_close(conn: NetworkDriver) -> None:
    """
    JunosDriver default on_close callable

    Args:
        conn: NetworkDriver object

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A
    """
    # write exit directly to the transport as channel would fail to find the prompt after sending
    # the exit command!
    conn.transport.write(channel_input="exit")
    conn.transport.write(channel_input=conn.channel.comms_prompt_pattern)


PRIVS = {
    "exec": (PrivilegeLevel(r"^[a-z0-9.\-@()/:]{1,32}>\s?$", "exec", "", "", "", False, "",)),
    "configuration": (
        PrivilegeLevel(
            r"^[a-z0-9.\-@()/:]{1,32}#\s?$",
            "configuration",
            "exec",
            "exit configuration-mode",
            "configure",
            False,
            "",
        )
    ),
}


class JunosDriver(NetworkDriver):
    def __init__(
        self,
        on_open: Optional[Callable[..., Any]] = None,
        on_close: Optional[Callable[..., Any]] = None,
        auth_secondary: str = "",
        transport: str = "system",
        **kwargs: Dict[str, Any],
    ):
        """
        JunosDriver Object

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
            on_open = junos_on_open
        if on_close is None:
            on_close = junos_on_close

        _telnet = False
        if transport == "telnet":
            _telnet = True

        super().__init__(
            privilege_levels=PRIVS,
            default_desired_privilege_level="exec",
            auth_secondary=auth_secondary,
            on_open=on_open,
            on_close=on_close,
            transport=transport,
            **kwargs,
        )

        if _telnet:
            self.transport.username_prompt = "login:"

        self.default_desired_priv = "exec"
        self.textfsm_platform = "juniper_junos"

        self.failed_when_contains = [
            "is ambiguous",
            "No valid completions",
            "unknown command",
            "syntax error",
        ]

    def _abort_config(self) -> None:
        """
        Abort Junos configuration session

        Args:
            N/A

        Returns:
            N/A:  # noqa: DAR202

        Raises:
            N/A

        """
        self.channel.comms_prompt_pattern = self.privilege_levels[
            self.default_desired_privilege_level
        ].pattern
        interact_events = [
            ("exit", "Exit with uncommitted changes? [yes,no] (yes)", False),
            ("yes", self.channel.comms_prompt_pattern, False),
        ]
        self.channel.send_inputs_interact(interact_events=interact_events)
