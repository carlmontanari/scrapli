"""scrapli.driver.core.arista_eos.driver"""
from typing import Any, Callable, Dict, Union

from scrapli.driver import NetworkDriver
from scrapli.driver.network_driver import PrivilegeLevel

EOS_ARG_MAPPER = {
    "comms_prompt_regex": r"^[a-z0-9.\-@()/:]{1,32}[#>$]$",
    "comms_return_char": "\n",
    "comms_pre_login_handler": "",
    "comms_disable_paging": "terminal length 0",
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
        session_pre_login_handler: Union[str, Callable[..., Any]] = "",
        session_disable_paging: Union[str, Callable[..., Any]] = "terminal length 0",
        **kwargs: Dict[str, Any],
    ):
        """
        EOSDriver Object

        Args:
            auth_secondary: password to use for secondary authentication (enable)
            session_pre_login_handler: callable or string that resolves to an importable function to
                handle pre-login (pre disable paging) operations
            session_disable_paging: callable, string that resolves to an importable function, or
                string to send to device to disable paging
            **kwargs: keyword args to pass to inherited class(es)

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A
        """
        super().__init__(
            auth_secondary, session_pre_login_handler, session_disable_paging, **kwargs
        )
        self.privs = PRIVS
        self.default_desired_priv = "privilege_exec"
        self.textfsm_platform = "arista_eos"
        self.exit_command = "exit"
