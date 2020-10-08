"""scrapli.driver.core.cisco_iosxe.base_driver"""
from scrapli.driver.base_network_driver import PrivilegeLevel

PRIVS = {
    "exec": (
        PrivilegeLevel(
            pattern=r"^[a-z0-9.\-_@()/:]{1,63}>$",
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
            pattern=r"^[a-z0-9.\-_@/:]{1,63}#$",
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
            pattern=r"^[a-z0-9.\-_@/:]{1,63}\([a-z0-9.\-@/:\+]{0,32}\)#$",
            name="configuration",
            previous_priv="privilege_exec",
            deescalate="end",
            escalate="configure terminal",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
}
