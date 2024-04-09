"""scrapli.driver.core.cisco_iosxe.base_driver"""

from scrapli.driver.network.base_driver import PrivilegeLevel

PRIVS = {
    "exec": (
        PrivilegeLevel(
            pattern=r"^[\w.\-@/:]{1,63}>$",
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
            pattern=r"^[\w.\-@/:]{1,63}#$",
            name="privilege_exec",
            previous_priv="exec",
            deescalate="disable",
            escalate="enable",
            escalate_auth=True,
            escalate_prompt=r"^(?:enable\s){0,1}password:\s?$",
        )
    ),
    "configuration": (
        PrivilegeLevel(
            pattern=r"^[\w.\-@/:]{1,63}\([\w.\-@/:+]{0,32}\)#$",
            name="configuration",
            previous_priv="privilege_exec",
            deescalate="end",
            escalate="configure terminal",
            escalate_auth=False,
            escalate_prompt="",
            not_contains=["tcl)"],
        )
    ),
    "tclsh": (
        PrivilegeLevel(
            pattern=r"^([\w.\-@/+>:]+\(tcl\)[>#]|\+>)$",
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
    "% Unknown command",
]
