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
    conn.channel.send_inputs("set cli complete-on-space off")
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
    # write exit directly to the transport as channel would fail to find the prompt after sending
    # the exit command!
    conn.transport.write("exit")
    conn.transport.write(conn.channel.comms_prompt_pattern)


JUNOS_ARG_MAPPER = {
    "comms_prompt_regex": r"^[a-z0-9.\-@()/:]{1,32}[#>$]\s?$",
    "comms_return_char": "\n",
    "on_open": junos_on_open,
    "on_close": junos_on_close,
}

PRIVS = {
    "exec": (
        PrivilegeLevel(
            r"^[a-z0-9.\-@()/:]{1,32}>\s?$",
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
            r"^[a-z0-9.\-@()/:]{1,32}#\s?$",
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
        comms_prompt_pattern: str = r"^[a-z0-9.\-@()/:]{1,32}[#>$]\s?$",
        on_open: Optional[Callable[..., Any]] = None,
        on_close: Optional[Callable[..., Any]] = None,
        auth_secondary: str = "",
        **kwargs: Dict[str, Any],
    ):
        """
        JunosDriver Object

        Args:
            comms_prompt_pattern: raw string regex pattern -- preferably use `^` and `$` anchors!
                this is the single most important attribute here! if this does not match a prompt,
                scrapli will not work!
                IMPORTANT: regex search uses multi-line + case insensitive flags. multi-line allows
                for highly reliably matching for prompts however we do NOT strip trailing whitespace
                for each line, so be sure to add '\\s*' if your device needs that. This should be
                mostly sorted for you if using network drivers (i.e. `IOSXEDriver`). Lastly, the
                case insensitive is just a convenience factor so i can be lazy.
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
            on_open = junos_on_open
        if on_close is None:
            on_close = junos_on_close

        super().__init__(
            auth_secondary,
            comms_prompt_pattern=comms_prompt_pattern,
            on_open=on_open,
            on_close=on_close,
            **kwargs,
        )

        self.privs = PRIVS
        self.default_desired_priv = "exec"
        self.textfsm_platform = "juniper_junos"
