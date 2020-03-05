"""scrapli.driver.core.cisco_iosxe.driver"""
from typing import Any, Callable, Dict, Optional

from scrapli.driver import NetworkDriver
from scrapli.driver.network_driver import PrivilegeLevel


def iosxe_on_open(conn: NetworkDriver) -> None:
    """
    IOSXEDriver default on_open callable

    Args:
        conn: NetworkDriver object

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A
    """
    conn.channel.send_inputs("terminal length 0")


def iosxe_on_close(conn: NetworkDriver) -> None:
    """
    IOSXEDriver default on_close callable

    Args:
        conn: NetworkDriver object

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A
    """
    conn.channel.send_inputs("end")
    conn.channel.send_inputs("exit")


IOSXE_ARG_MAPPER = {
    "comms_prompt_pattern": r"^[a-z0-9.\-@()/:]{1,32}[#>$]$",
    "comms_return_char": "\n",
    "on_open": iosxe_on_open,
    "on_close": iosxe_on_close,
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
            "privilege_exec",
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
            "privilege_exec",
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


class IOSXEDriver(NetworkDriver):
    def __init__(
        self,
        auth_secondary: str = "",
        on_open: Optional[Callable[..., Any]] = None,
        on_close: Optional[Callable[..., Any]] = None,
        **kwargs: Dict[str, Any],
    ):
        """
        IOSXEDriver Object

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
            on_open = iosxe_on_open
        if on_close is None:
            on_close = iosxe_on_close
        super().__init__(auth_secondary, on_open=on_open, on_close=on_close, **kwargs)
        self.privs = PRIVS
        self.default_desired_priv = "privilege_exec"
        self.textfsm_platform = "cisco_ios"
