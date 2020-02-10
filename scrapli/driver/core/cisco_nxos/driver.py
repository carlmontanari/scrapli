"""scrapli.driver.core.cisco_nxos.driver"""
from typing import Any, Dict

from scrapli.driver import NetworkDriver
from scrapli.driver.network_driver import PrivilegeLevel

NXOS_ARG_MAPPER = {
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


class NXOSDriver(NetworkDriver):
    def __init__(self, auth_secondary: str = "", **kwargs: Dict[str, Any]):
        """
        NXOSDriver Object

        Args:
            auth_secondary: password to use for secondary authentication (enable)
            **kwargs: keyword args to pass to inherited class(es)

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A
        """
        super().__init__(auth_secondary, **kwargs)
        self.privs = PRIVS
        self.default_desired_priv = "privilege_exec"
        self.textfsm_platform = "cisco_nxos"
        self.exit_command = "exit"
