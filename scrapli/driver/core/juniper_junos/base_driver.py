"""scrapli.driver.core.juniper_junos.base_driver"""

from scrapli.driver.network.base_driver import PrivilegeLevel

PRIVS = {
    "exec": (
        PrivilegeLevel(
            pattern=r"^({\w+(:(\w+){0,1}\d){0,1}}\n){0,1}[\w\-@()/:\.]{1,63}>\s?$",
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
            pattern=r"^({\w+(:(\w+){0,1}\d){0,1}}\[edit\]\n){0,1}[\w\-@()/:\.]{1,63}#\s?$",
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
            pattern=r"^({\w+(:(\w+){0,1}\d){0,1}}\[edit\]\n){0,1}[\w\-@()/:\.]{1,63}#\s?$",
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
            pattern=r"^({\w+(:(\w+){0,1}\d){0,1}}\[edit\]\n){0,1}[\w\-@()/:\.]{1,63}#\s?$",
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
            pattern=r"^.*[%\$]\s?$",
            not_contains=["root"],
            name="shell",
            previous_priv="exec",
            deescalate="exit",
            escalate="start shell",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
    "root_shell": (
        PrivilegeLevel(
            pattern=r"^.*root@(?:\S*:?\S*\s?)?[%\#]\s?$",
            name="root_shell",
            previous_priv="exec",
            deescalate="exit",
            escalate="start shell user root",
            escalate_auth=True,
            escalate_prompt=r"^[pP]assword:\s?$",
        )
    ),
}

FAILED_WHEN_CONTAINS = [
    "is ambiguous",
    "No valid completions",
    "unknown command",
    "syntax error",
]
