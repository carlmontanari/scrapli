"""scrapli.driver.core.cisco_nxos.base_driver"""
from typing import Dict

from scrapli.driver.network.base_driver import PrivilegeLevel
from scrapli.exceptions import ScrapliValueError

PRIVS = {
    "exec": (
        PrivilegeLevel(
            pattern=r"^[a-z0-9.\-_@()/:]{1,63}>\s?$",
            name="exec",
            previous_priv="",
            deescalate="",
            escalate="",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
    "privilege_exec": (
        PrivilegeLevel(
            pattern=r"^((?!\-tcl)[a-z0-9.\-_@/:]){1,63}#\s?$",
            name="privilege_exec",
            previous_priv="exec",
            deescalate="disable",
            escalate="enable",
            escalate_auth=True,
            escalate_prompt=r"^[pP]assword:\s?$",
        )
    ),
    "configuration": (
        PrivilegeLevel(
            pattern=r"^[a-z0-9.\-_@/:]{1,63}\(config(?!\-s)(?!\-tcl)[a-z0-9.\-@/:]{0,32}\)#\s?$",
            name="configuration",
            previous_priv="privilege_exec",
            deescalate="end",
            escalate="configure terminal",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
    "tclsh": (
        PrivilegeLevel(
            # annoyingly tclsh has many variations... exec/priv exec/config and just ">"
            # for now doesnt seem to be a reason to differentiate between them, so just have one
            # giant pattern
            pattern=(
                r"(^[a-z0-9.\-_@/:]{1,63}\-tcl#\s?$)|"
                r"(^[a-z0-9.\-_@/:]{1,63}\(config\-tcl\)#\s?$)|"
                r"(^>\s?$)"
            ),
            name="tclsh",
            previous_priv="privilege_exec",
            deescalate="tclquit",
            escalate="tclsh",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
}

FAILED_WHEN_CONTAINS = [
    "% Ambiguous command",
    "% Incomplete command",
    "% Invalid input detected",
    "% Invalid command at",
]


class NXOSDriverBase:
    # NXOSDriverBase Mixin values set in init of sync/async NetworkDriver classes
    privilege_levels: Dict[str, PrivilegeLevel]

    def _create_configuration_session(self, session_name: str) -> None:
        """
        Handle configuration session creation tasks for consistency between sync/async versions

        Args:
            session_name: name of session to register

        Returns:
            None

        Raises:
            ScrapliValueError: if a session of given name already exists

        """
        if session_name in self.privilege_levels.keys():
            msg = (
                f"session name `{session_name}` already registered as a privilege level, chose a "
                "unique session name"
            )
            raise ScrapliValueError(msg)
        pattern = r"^[a-z0-9.\-_@/:]{1,32}\(config\-s[a-z0-9.\-@/:]{0,32}\)#\s?$"
        name = session_name
        config_session = PrivilegeLevel(
            pattern=pattern,
            name=name,
            previous_priv="privilege_exec",
            deescalate="end",
            escalate=f"configure session {session_name}",
            escalate_auth=False,
            escalate_prompt="",
        )
        self.privilege_levels[name] = config_session
