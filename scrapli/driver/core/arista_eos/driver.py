"""scrapli.driver.core.arista_eos.driver"""
from typing import Any, Callable, Dict, Optional

from scrapli.driver import NetworkDriver
from scrapli.driver.network_driver import PrivilegeLevel


def eos_on_connect(conn: NetworkDriver) -> None:
    """
    EOSDriver default on_connect callable

    Args:
        conn: NetworkDriver object

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A
    """
    conn.channel.send_inputs("terminal length 0")


EOS_ARG_MAPPER = {
    "comms_prompt_regex": r"^[a-z0-9.\-@()/:]{1,32}[#>$]$",
    "comms_return_char": "\n",
    "comms_pre_login_handler": "",
    "on_connect": eos_on_connect,
}

PRIVS = {
    "exec": (
        PrivilegeLevel(
            r"^[a-z0-9.\-@()/:]{1,32}>$",
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
            r"^[a-z0-9.\-@/:]{1,32}#$",
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
            r"^[a-z0-9.\-@/:]{1,32}\(config[a-z0-9.\-@/:]{0,16}\)#$",
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
            r"^[a-z0-9.\-@/:]{1,32}\(config[a-z0-9.\-@/:]{1,16}\)#$",
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


class EOSDriver(NetworkDriver):
    def __init__(
        self,
        auth_secondary: str = "",
        on_connect: Optional[Callable[..., Any]] = None,
        **kwargs: Dict[str, Any],
    ):
        """
        EOSDriver Object

        Args:
            auth_secondary: password to use for secondary authentication (enable)
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
            on_connect = eos_on_connect
        super().__init__(auth_secondary, on_connect=on_connect, **kwargs)
        self.privs = PRIVS
        self.default_desired_priv = "privilege_exec"
        self.textfsm_platform = "arista_eos"
        self.exit_command = "exit"
