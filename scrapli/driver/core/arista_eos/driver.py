"""scrapli.driver.core.arista_eos.driver"""
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional

from scrapli.driver import NetworkDriver
from scrapli.driver.base_network_driver import PrivilegeLevel
from scrapli.driver.core.arista_eos.base_driver import PRIVS, EOSDriverBase


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


class EOSDriver(NetworkDriver, EOSDriverBase):
    def __init__(
        self,
        privilege_levels: Optional[Dict[str, PrivilegeLevel]] = None,
        default_desired_privilege_level: str = "privilege_exec",
        auth_secondary: str = "",
        on_open: Optional[Callable[..., Any]] = None,
        on_close: Optional[Callable[..., Any]] = None,
        textfsm_platform: str = "arista_eos",
        genie_platform: str = "",
        failed_when_contains: Optional[List[str]] = None,
        **kwargs: Dict[str, Any],
    ):
        """
        EOSDriver Object

        Args:
            privilege_levels: optional user provided privilege levels, if left None will default to
                scrapli standard privilege levels
            default_desired_privilege_level: string of name of default desired priv, this is the
                priv level that is generally used to disable paging/set terminal width and things
                like that upon first login, and is also the priv level scrapli will try to acquire
                for normal "command" operations (`send_command`, `send_commands`)
            auth_secondary: password to use for secondary authentication (enable)
            on_open: callable that accepts the class instance as its only argument. this callable,
                if provided, is executed immediately after authentication is completed. Common use
                cases for this callable would be to disable paging or accept any kind of banner
                message that prompts a user upon connection
            on_close: callable that accepts the class instance as its only argument. this callable,
                if provided, is executed immediately prior to closing the underlying transport.
                Common use cases for this callable would be to save configurations prior to exiting,
                or to logout properly to free up vtys or similar.
            textfsm_platform: string name of textfsm parser platform
            genie_platform: string name of cisco genie parser platform
            failed_when_contains: List of strings that indicate a command/config has failed
            **kwargs: keyword args to pass to inherited class(es)

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        if privilege_levels is None:
            privilege_levels = deepcopy(PRIVS)

        if on_open is None:
            on_open = eos_on_open
        if on_close is None:
            on_close = eos_on_close

        if failed_when_contains is None:
            failed_when_contains = [
                "% Ambiguous command",
                "% Incomplete command",
                "% Invalid input",
                "% Cannot commit",
            ]

        super().__init__(
            privilege_levels=privilege_levels,
            default_desired_privilege_level=default_desired_privilege_level,
            auth_secondary=auth_secondary,
            failed_when_contains=failed_when_contains,
            textfsm_platform=textfsm_platform,
            genie_platform=genie_platform,
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
        """
        EOS specific implementation of register_configuration_session

        Args:
            session_name: name of session to register

        Returns:
            N/A:  # noqa: DAR202

        Raises:
            N/A

        """
        self._create_configuration_session(session_name=session_name)
        self.update_privilege_levels(update_channel=True)
