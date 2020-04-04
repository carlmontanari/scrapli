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
    conn.channel.send_input("terminal length 0")
    conn.channel.send_input("terminal width 511")


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
    conn.acquire_priv(conn.default_desired_priv)
    conn.transport.write("exit")
    conn.transport.write(conn.channel.comms_prompt_pattern)


PRIVS = {
    "exec": (
        PrivilegeLevel(
            r"^[a-z0-9.\-@()/:]{1,32}>\s?$",
            "exec",
            "",
            "",
            "privilege_exec",
            "enable",
            True,
            "Password:",
            True,
            0,
        )
    ),
    "privilege_exec": (
        PrivilegeLevel(
            r"^[a-z0-9.\-@/:]{1,32}#\s?$",
            "privilege_exec",
            "exec",
            "disable",
            "configuration",
            "configure terminal",
            False,
            "",
            True,
            1,
        )
    ),
    "configuration": (
        PrivilegeLevel(
            r"^[a-z0-9.\-@/:]{1,32}\(config[a-z0-9.\-@/:]{0,16}\)#\s?$",
            "configuration",
            "privilege_exec",
            "end",
            "",
            "",
            False,
            "",
            True,
            2,
        )
    ),
    "special_configuration": (
        PrivilegeLevel(
            r"^[a-z0-9.\-@/:]{1,32}\(config[a-z0-9.\-@/:]{1,16}\)#\s?$",
            "special_configuration",
            "privilege_exec",
            "end",
            "",
            "",
            False,
            "",
            False,
            3,
        )
    ),
}


class NXOSDriver(NetworkDriver):
    def __init__(
        self,
        comms_prompt_pattern: str = r"^[a-z0-9.\-@()/:]{1,32}[#>$]\s?$",
        on_open: Optional[Callable[..., Any]] = None,
        on_close: Optional[Callable[..., Any]] = None,
        auth_secondary: str = "",
        transport: str = "system",
        **kwargs: Dict[str, Any],
    ):
        """
        NXOSDriver Object

        Args:
            comms_prompt_pattern: raw string regex pattern -- preferably use `^` and `$` anchors!
                this is the single most important attribute here! if this does not match a prompt,
                scrapli will not work!
                IMPORTANT: regex search uses multi-line + case insensitive flags. multi-line allows
                for highly reliably matching for prompts however we do NOT strip trailing whitespace
                for each line, so be sure to add `\\s*` if your device needs that. This should be
                mostly sorted for you if using network drivers (i.e. `IOSXEDriver`). Lastly, the
                case insensitive is just a convenience factor so i can be lazy.
            on_open: callable that accepts the class instance as its only argument. this callable,
                if provided, is executed immediately after authentication is completed. Common use
                cases for this callable would be to disable paging or accept any kind of banner
                message that prompts a user upon connection
            on_close: callable that accepts the class instance as its only argument. this callable,
                if provided, is executed immediately prior to closing the underlying transport.
                Common use cases for this callable would be to save configurations prior to exiting,
                or to logout properly to free up vtys or similar.
            auth_secondary: password to use for secondary authentication (enable)
            transport: system|ssh2|paramiko|telnet -- type of transport to use for connection
                system uses system available ssh (/usr/bin/ssh)
                ssh2 uses ssh2-python
                paramiko uses... paramiko
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
            auth_secondary,
            comms_prompt_pattern=comms_prompt_pattern,
            on_open=on_open,
            on_close=on_close,
            transport=transport,
            **kwargs,
        )

        if _telnet:
            self.transport.username_prompt = "login:"

        self.privs = PRIVS
        self.default_desired_priv = "privilege_exec"

        self.textfsm_platform = "cisco_nxos"
        self.genie_platform = "nxos"

        self.failed_when_contains = [
            "% Ambiguous command",
            "% Incomplete command",
            "% Invalid input detected",
        ]
