from scrapli.driver.core import IOSXEDriver

args = {
    "host": "172.18.0.11",
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
}

with IOSXEDriver(**args) as conn:
    result = conn.send_command("show version")

print(result.textfsm_parse_output())
