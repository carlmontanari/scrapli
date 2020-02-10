"""scrapli.driver.core.juniper_junos.driver"""
from typing import Any, Dict

from scrapli.driver import NetworkDriver
from scrapli.driver.network_driver import PrivilegeLevel

JUNOS_ARG_MAPPER = {
    "comms_prompt_regex": r"^[a-z0-9.\-@()/:]{1,32}[#>$]$",
    "comms_return_char": "\n",
    "comms_pre_login_handler": "",
    "comms_disable_paging": "scrapli.driver.core.juniper_junos.helper.disable_paging",
}

PRIVS = {
    "exec": (
        PrivilegeLevel(
            r"^[a-z0-9.\-@()/:]{1,32}>$",
            "exec",
            "",
            "",
            "configuration",
            "configure",
            False,
            "",
            True,
            0,
        )
    ),
    "configuration": (
        PrivilegeLevel(
            r"^[a-z0-9.\-@()/:]{1,32}#$",
            "configuration",
            "exec",
            "exit configuration-mode",
            "",
            "",
            False,
            "",
            True,
            1,
        )
    ),
}


class JunosDriver(NetworkDriver):
    def __init__(self, auth_secondary: str = "", **kwargs: Dict[str, Any]):
        """
        JunosDriver Object

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
        self.default_desired_priv = "exec"
        self.textfsm_platform = "juniper_junos"
        self.exit_command = "exit"
