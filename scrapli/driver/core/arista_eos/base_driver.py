"""scrapli.driver.core.arista_eos.base_driver"""
import re
from typing import Dict

from scrapli.driver.network.base_driver import PrivilegeLevel
from scrapli.exceptions import ScrapliValueError

PRIVS = {
    "exec": (
        PrivilegeLevel(
            # pattern has... gotten a bit out of hand. it seems some eos devices can have things in
            # parenthesis in a "normal" (non config) prompt... something like `my(eos)#`. To make
            # sure we account for that but do *not* include config modes we need this negative
            # lookahead to *not* match "config"... the remaining pattern is the "normal" scrapli
            # eos pattern basically
            pattern=r"^((?!config)[a-z0-9.\-@()/: ]){1,63}>\s?$",
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
            pattern=r"^((?!config)[a-z0-9.\-@()/: ]){1,63}#\s?$",
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
            pattern=r"^[a-z0-9.\-@()/: ]{1,63}\(config(?!\-s\-)[a-z0-9_.\-@/:]{0,32}\)#\s?$",
            name="configuration",
            previous_priv="privilege_exec",
            deescalate="end",
            escalate="configure terminal",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
}

FAILED_WHEN_CONTAINS = [
    "% Ambiguous command",
    "% Error",
    "% Incomplete command",
    "% Invalid input",
    "% Cannot commit",
    "% Unavailable command",
]


class EOSDriverBase:
    # EOSDriverBase Mixin values set in init of sync/async NetworkDriver classes
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
        sess_prompt = re.escape(session_name[:6])
        pattern = (
            rf"^[a-z0-9.\-@()/: ]{{1,63}}\(config\-s\-{sess_prompt}[a-z0-9_.\-@/:]{{0,32}}\)#\s?$"
        )
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
