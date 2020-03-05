"""scrapli.driver.core.juniper_junos.driver"""
from typing import Any, Callable, Dict, Optional

from scrapli.driver import NetworkDriver
from scrapli.driver.network_driver import PrivilegeLevel


def junos_on_open(conn: NetworkDriver) -> None:
    """
    JunosDriver default on_open callable

    Args:
        conn: NetworkDriver object

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A
    """
    conn.channel.send_inputs("set cli screen-length 0")
    conn.channel.send_inputs("set cli screen-width 511")


def junos_on_close(conn: NetworkDriver) -> None:
    """
    JunosDriver default on_close callable

    Args:
        conn: NetworkDriver object

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A
    """
    conn.channel.send_inputs("exit")


JUNOS_ARG_MAPPER = {
    "comms_prompt_regex": r"^[a-z0-9.\-@()/:]{1,32}[#>$]$",
    "comms_return_char": "\n",
    "on_open": junos_on_open,
    "on_close": junos_on_close,
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
    def __init__(
        self,
        auth_secondary: str = "",
        on_open: Optional[Callable[..., Any]] = None,
        on_close: Optional[Callable[..., Any]] = None,
        **kwargs: Dict[str, Any],
    ):
        """
        JunosDriver Object

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
            on_open = junos_on_open
        if on_close is None:
            on_close = junos_on_close
        super().__init__(auth_secondary, on_open=on_open, on_close=on_close, **kwargs)
        self.privs = PRIVS
        self.default_desired_priv = "exec"
        self.textfsm_platform = "juniper_junos"
