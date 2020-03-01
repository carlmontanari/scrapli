"""scrapli.driver.core.cisco_nxos.driver"""
from typing import Any, Callable, Dict, Optional

from scrapli.driver import NetworkDriver
from scrapli.driver.network_driver import PrivilegeLevel


def nxos_on_connect(conn: NetworkDriver) -> None:
    """
    NXOSDriver default on_connect callable

    Args:
        conn: NetworkDriver object

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A
    """
    conn.channel.send_inputs("terminal length 0")


NXOS_ARG_MAPPER = {
    "comms_prompt_regex": r"^[a-z0-9.\-@()/:]{1,32}[#>$]\s*$",
    "comms_return_char": "\n",
    "comms_pre_login_handler": "",
    "comms_disable_paging": nxos_on_connect,
}

PRIVS = {
    "exec": (
        PrivilegeLevel(
            r"^[a-z0-9.\-@()/:]{1,32}>\s*$",
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
            r"^[a-z0-9.\-@/:]{1,32}#\s*$",
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
            r"^[a-z0-9.\-@/:]{1,32}\(config[a-z0-9.\-@/:]{0,16}\)#\s*$",
            "configuration",
            "priv",
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
            r"^[a-z0-9.\-@/:]{1,32}\(config[a-z0-9.\-@/:]{1,16}\)#\s*$",
            "special_configuration",
            "priv",
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
        auth_secondary: str = "",
        comms_prompt_pattern: str = r"^[a-z0-9.\-@()/:]{1,32}[#>$]\s*$",
        on_connect: Optional[Callable[..., Any]] = None,
        **kwargs: Dict[str, Any],
    ):
        """
        NXOSDriver Object

        Args:
            auth_secondary: password to use for secondary authentication (enable)
            comms_prompt_pattern: raw string regex pattern -- preferably use `^` and `$` anchors!
                this is the single most important attribute here! if this does not match a prompt,
                scrapli will not work!
                IMPORTANT: regex search uses multi-line + case insensitive flags. multi-line allows
                for highly reliably matching for prompts however we do NOT strip trailing whitespace
                for each line, so be sure to add `\\s*` if your device needs that. This should be
                mostly sorted for you if using network drivers (i.e. `IOSXEDriver`). Lastly, the
                case insensitive is just a convenience factor so i can be lazy.
            on_connect: callable that accepts the class instance as its only argument. this callable
                if provided is executed immediately after authentication is completed. Common use
                cases for this callable would be to disable paging or accept any kind of banner
                message that prompts a user upon connection
            **kwargs: keyword args to pass to inherited class(es)

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A
        """
        if on_connect is None:
            on_connect = nxos_on_connect
        super().__init__(
            auth_secondary,
            comms_prompt_pattern=comms_prompt_pattern,
            on_connect=on_connect,
            **kwargs,
        )
        self.privs = PRIVS
        self.default_desired_priv = "privilege_exec"
        self.textfsm_platform = "cisco_nxos"
        self.exit_command = "exit"
