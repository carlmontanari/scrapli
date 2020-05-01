"""scrapli.driver.core.cisco_iosxr.driver"""
import time
from typing import Any, Callable, Dict, Optional

from scrapli.driver import NetworkDriver
from scrapli.driver.network_driver import PrivilegeLevel


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
    conn.channel.send_input(channel_input="terminal length 0")
    conn.channel.send_input(channel_input="terminal width 512")


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


PRIVS = {
    "privilege_exec": (
        PrivilegeLevel(r"^[a-z0-9.\-@/:]{1,32}#\s?$", "privilege_exec", "", "", "", False, "",)
    ),
    "configuration": (
        PrivilegeLevel(
            r"^[a-z0-9.\-@/:]{1,32}\(config[a-z0-9.\-@/:]{0,32}\)#\s?$",
            "configuration",
            "privilege_exec",
            "end",
            "configure terminal",
            False,
            "",
        )
    ),
    "configuration_exclusive": (
        PrivilegeLevel(
            r"^[a-z0-9.\-@/:]{1,32}\(config[a-z0-9.\-@/:]{1,32}\)#\s?$",
            "configuration_exclusive",
            "privilege_exec",
            "end",
            "configure exclusive",
            False,
            "",
        )
    ),
}


class IOSXRDriver(NetworkDriver):
    def __init__(
        self,
        on_open: Optional[Callable[..., Any]] = None,
        on_close: Optional[Callable[..., Any]] = None,
        auth_secondary: str = "",
        **kwargs: Dict[str, Any],
    ):
        """
        IOSXRDriver Object

        Args:
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
        if on_open is None:
            on_open = iosxr_on_open
        if on_close is None:
            on_close = iosxr_on_close

        super().__init__(
            privilege_levels=PRIVS,
            default_desired_privilege_level="privilege_exec",
            auth_secondary=auth_secondary,
            on_open=on_open,
            on_close=on_close,
            **kwargs,
        )

        self.textfsm_platform = "cisco_xr"
        self.genie_platform = "iosxr"

        self.failed_when_contains = [
            "% Ambiguous command",
            "% Incomplete command",
            "% Invalid input detected",
        ]

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
        self.channel.comms_prompt_pattern = self.privilege_levels[
            self.default_desired_privilege_level
        ].pattern
        self.channel.send_input(channel_input="abort")
