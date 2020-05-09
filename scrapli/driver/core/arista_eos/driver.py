"""scrapli.driver.core.arista_eos.driver"""
import re
from typing import Any, Callable, Dict, Optional

from scrapli.driver import NetworkDriver
from scrapli.driver.network_driver import PrivilegeLevel


def eos_on_open(conn: NetworkDriver) -> None:
    """
    EOSDriver default on_open callable

    Args:
        conn: NetworkDriver object

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A
    """
    conn.acquire_priv(desired_priv=conn.default_desired_privilege_level)
    conn.channel.send_input(channel_input="terminal length 0")
    conn.channel.send_input(channel_input="terminal width 32767")


def eos_on_close(conn: NetworkDriver) -> None:
    """
    EOSDriver default on_close callable

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
    conn.transport.write(channel_input=conn.channel.comms_return_char)


PRIVS = {
    "exec": (PrivilegeLevel(r"^[a-z0-9.\-@()/: ]{1,32}>\s?$", "exec", "", "", "", False, "",)),
    "privilege_exec": (
        PrivilegeLevel(
            r"^[a-z0-9.\-@/: ]{1,32}#\s?$",
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
            r"^[a-z0-9.\-@/: ]{1,32}\(config(?!\-s\-)[a-z0-9_.\-@/:]{0,32}\)#\s?$",
            "configuration",
            "privilege_exec",
            "end",
            "configure terminal",
            False,
            "",
        )
    ),
}


class EOSDriver(NetworkDriver):
    def __init__(
        self,
        privilege_levels: Optional[Dict[str, PrivilegeLevel]] = None,
        on_open: Optional[Callable[..., Any]] = None,
        on_close: Optional[Callable[..., Any]] = None,
        auth_secondary: str = "",
        **kwargs: Dict[str, Any],
    ):
        """
        EOSDriver Object

        Args:
            privilege_levels: optional user provided privilege levels, if left None will default to
                scrapli standard privilege levels
            on_open: callable that accepts the class instance as its only argument. this callable,
                if provided, is executed immediately after authentication is completed. Common use
                cases for this callable would be to disable paging or accept any kind of banner
                message that prompts a user upon connection
            on_close: callable that accepts the class instance as its only argument. this callable,
                if provided, is executed immediately prior to closing the underlying transport.
                Common use cases for this callable would be to save configurations prior to exiting,
                or to logout properly to free up vtys or similar.
            auth_secondary: password to use for secondary authentication (enable)
            **kwargs: keyword args to pass to inherited class(es)

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        if privilege_levels is None:
            privilege_levels = PRIVS

        if on_open is None:
            on_open = eos_on_open
        if on_close is None:
            on_close = eos_on_close

        failed_when_contains = [
            "% Ambiguous command",
            "% Incomplete command",
            "% Invalid input",
            "% Cannot commit",
        ]

        super().__init__(
            privilege_levels=privilege_levels,
            default_desired_privilege_level="privilege_exec",
            auth_secondary=auth_secondary,
            failed_when_contains=failed_when_contains,
            textfsm_platform="arista_eos",
            genie_platform="",
            on_open=on_open,
            on_close=on_close,
            **kwargs,
        )

    def _abort_config(self) -> None:
        """
        Abort EOS configuration session (if using a config session!)

        Args:
            N/A

        Returns:
            N/A:  # noqa: DAR202

        Raises:
            N/A

        """
        # eos pattern for config sessions should *always* have `config-s`
        if "config\\-s" in self._current_priv_level.pattern:
            self.channel.send_input(channel_input="abort")
            self._current_priv_level = self.privilege_levels["privilege_exec"]

    def register_configuration_session(self, session_name: str) -> None:
        if session_name in self.privilege_levels.keys():
            msg = (
                f"session name `{session_name}` already registered as a privilege level, chose a "
                "unique session name"
            )
            raise ValueError(msg)
        session_prompt = re.escape(session_name[:6])
        pattern = (
            rf"^[a-z0-9.\-@/:]{{1,32}}\(config\-s\-{session_prompt}[a-z0-9_.\-@/:]{{0,32}}\)#\s?$"
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
        self.update_privilege_levels(update_channel=True)
