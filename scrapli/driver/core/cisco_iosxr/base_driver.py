"""scrapli.driver.core.cisco_iosxr.base_driver"""
from scrapli.driver.network.base_driver import PrivilegeLevel

PRIVS = {
    "privilege_exec": (
        PrivilegeLevel(
            pattern=r"^[\w.\-@/:]{1,63}#\s?$",
            name="privilege_exec",
            previous_priv="",
            deescalate="",
            escalate="",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
    "admin_privilege_exec": (
        PrivilegeLevel(
            pattern=r"^[\w.\-@/:]{1,63}\(admin\)#\s?$",
            name="admin_privilege_exec",
            previous_priv="privilege_exec",
            deescalate="exit",
            escalate="admin",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
    "configuration": (
        PrivilegeLevel(
            pattern=r"^[\w.\-@/:]{1,63}\(config[\w.\-@/:]{0,32}\)#\s?$",
            name="configuration",
            previous_priv="privilege_exec",
            deescalate="end",
            escalate="configure terminal",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
    "configuration_exclusive": (
        PrivilegeLevel(
            pattern=r"^[\w.\-@/:]{1,63}\(config[\w.\-@/:]{0,32}\)#\s?$",
            name="configuration_exclusive",
            previous_priv="privilege_exec",
            deescalate="end",
            escalate="configure exclusive",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
    "admin_configuration": (
        PrivilegeLevel(
            pattern=r"^[\w.\-@/:]{1,63}\(admin-config[\w.\-@/:]{0,32}\)#\s?$",
            name="admin_configuration",
            previous_priv="privilege_exec",
            deescalate="end",
            escalate="admin configure terminal",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
    "admin_configuration_exclusive": (
        PrivilegeLevel(
            pattern=r"^[\w.\-@/:]{1,63}\(admin-config[\w.\-@/:]{0,32}\)#\s?$",
            name="admin_configuration_exclusive",
            previous_priv="privilege_exec",
            deescalate="end",
            escalate="admin configure exclusive",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
}

FAILED_WHEN_CONTAINS = [
    "% Ambiguous command",
    "% Incomplete command",
    "% Invalid input detected",
]
