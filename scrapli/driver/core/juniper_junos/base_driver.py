"""scrapli.driver.core.juniper_junos.base_driver"""
from scrapli.driver.network.base_driver import PrivilegeLevel

PRIVS = {
    "exec": (
        PrivilegeLevel(
            pattern=r"^({\w+:\d}\n){0,1}[a-z0-9.\-_@()/:]{1,63}>\s?$",
            name="exec",
            previous_priv="",
            deescalate="",
            escalate="",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
    "configuration": (
        PrivilegeLevel(
            pattern=r"^({\w+:\d}\[edit\]\n){0,1}[a-z0-9.\-_@()/:]{1,63}#\s?$",
            name="configuration",
            previous_priv="exec",
            deescalate="exit configuration-mode",
            escalate="configure",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
    "configuration_exclusive": (
        PrivilegeLevel(
            pattern=r"^({\w+:\d}\[edit\]\n){0,1}[a-z0-9.\-_@()/:]{1,63}#\s?$",
            name="configuration_exclusive",
            previous_priv="exec",
            deescalate="exit configuration-mode",
            escalate="configure exclusive",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
    "configuration_private": (
        PrivilegeLevel(
            pattern=r"^({\w+:\d}\[edit\]\n){0,1}[a-z0-9.\-_@()/:]{1,63}#\s?$",
            name="configuration_private",
            previous_priv="exec",
            deescalate="exit configuration-mode",
            escalate="configure private",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
    "shell": (
        PrivilegeLevel(
            pattern=r"^%\s?$",
            name="shell",
            previous_priv="exec",
            deescalate="exit",
            escalate="start shell",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
}

FAILED_WHEN_CONTAINS = [
    "is ambiguous",
    "No valid completions",
    "unknown command",
    "syntax error",
]
