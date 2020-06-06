"""scrapli.driver.core.cisco_iosxr.driver"""
import time
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional

from scrapli.driver import NetworkDriver
from scrapli.driver.base_network_driver import PrivilegeLevel
from scrapli.driver.core.cisco_iosxr.base_driver import PRIVS


def iosxr_on_open(conn: NetworkDriver) -> None:
    """
    IOSXRDriver default on_open callable

    Args:
        conn: NetworkDriver object

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A
    """
    # sleep for session to establish; without this we never find base prompt for some reason?
    # maybe this is an artifact from previous iterations/tests and can be done away with...
    time.sleep(1)
    conn.acquire_priv(desired_priv=conn.default_desired_privilege_level)
    conn.send_command(command="terminal length 0")
    conn.send_command(command="terminal width 512")


def iosxr_on_close(conn: NetworkDriver) -> None:
    """
    IOSXRDriver default on_close callable

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


class IOSXRDriver(NetworkDriver):
    def __init__(
        self,
        privilege_levels: Optional[Dict[str, PrivilegeLevel]] = None,
        default_desired_privilege_level: str = "privilege_exec",
        auth_secondary: str = "",
        on_open: Optional[Callable[..., Any]] = None,
        on_close: Optional[Callable[..., Any]] = None,
        textfsm_platform: str = "cisco_iosxr",
        genie_platform: str = "iosxr",
        failed_when_contains: Optional[List[str]] = None,
        **kwargs: Dict[str, Any],
    ):
        """
        IOSXRDriver Object

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
            on_open = iosxr_on_open
        if on_close is None:
            on_close = iosxr_on_close

        if failed_when_contains is None:
            failed_when_contains = [
                "% Ambiguous command",
                "% Incomplete command",
                "% Invalid input detected",
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
        Abort IOSXR configuration session

        Args:
            N/A

        Returns:
            N/A:  # noqa: DAR202

        Raises:
            N/A

        """
        self.channel.send_input(channel_input="abort")
        self._current_priv_level = self.privilege_levels["privilege_exec"]
