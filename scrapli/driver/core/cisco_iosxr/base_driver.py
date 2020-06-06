"""scrapli.driver.core.cisco_iosxr.base_driver"""
from scrapli.driver.base_network_driver import PrivilegeLevel

PRIVS = {
    "privilege_exec": (
        PrivilegeLevel(
            pattern=r"^[a-z0-9.\-_@/:]{1,63}#\s?$",
            name="privilege_exec",
            previous_priv="",
            deescalate="",
            escalate="",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
    "configuration": (
        PrivilegeLevel(
            pattern=r"^[a-z0-9.\-_@/:]{1,63}\(config[a-z0-9.\-@/:]{0,32}\)#\s?$",
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
            pattern=r"^[a-z0-9.\-_@/:]{1,63}\(config[a-z0-9.\-@/:]{0,32}\)#\s?$",
            name="configuration_exclusive",
            previous_priv="privilege_exec",
            deescalate="end",
            escalate="configure exclusive",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
}
