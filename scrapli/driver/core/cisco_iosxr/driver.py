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
    conn.channel.send_inputs("terminal length 0")


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
    conn.channel.send_inputs("end")
    conn.channel.send_inputs("exit")


IOSXR_ARG_MAPPER = {
    "comms_prompt_regex": r"^[a-z0-9.\-@()/:]{1,32}[#>$]$",
    "comms_return_char": "\n",
    "on_open": iosxr_on_open,
    "on_close": iosxr_on_close,
}

PRIVS = {
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


class IOSXRDriver(NetworkDriver):
    def __init__(
        self,
        auth_secondary: str = "",
        on_open: Optional[Callable[..., Any]] = None,
        on_close: Optional[Callable[..., Any]] = None,
        **kwargs: Dict[str, Any],
    ):
        """
        IOSXRDriver Object

        Args:
            auth_secondary: password to use for secondary authentication (enable)
            on_open: callable that accepts the class instance as its only argument. this callable,
                if provided, is executed immediately after authentication is completed. Common use
                cases for this callable would be to disable paging or accept any kind of banner
                message that prompts a user upon connection
            on_close: callable that accepts the class instance as its only argument. this callable,
                if provided, is executed immediately prior to closing the underlying transport.
                Common use cases for this callable would be to save configurations prior to exiting,
                or to logout properly to free up vtys or similar.
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
        super().__init__(auth_secondary, on_open=on_open, on_close=on_close, **kwargs)
        self.privs = PRIVS
        self.default_desired_priv = "privilege_exec"
        self.textfsm_platform = "cisco_xr"
