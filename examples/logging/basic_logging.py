import logging

from scrapli.driver.core import IOSXEDriver

logging.basicConfig(filename="scrapli.log", level=logging.DEBUG)
logger = logging.getLogger("scrapli")

args = {
    "host": "172.18.0.11",
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
}

conn = IOSXEDriver(**args)
conn.open()

print(conn.get_prompt())
print(conn.send_command("show run | i hostname").result)
