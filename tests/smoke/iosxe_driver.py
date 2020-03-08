import logging
import time
from pathlib import Path

from device_info import iosxe_device
from scrapli.driver.core import IOSXEDriver

logging.basicConfig(
    filename=f"{Path(__file__).resolve().parents[0]}/iosxe_driver.log", level=logging.DEBUG
)
logger = logging.getLogger("scrapli")

args = {
    "host": iosxe_device["host"],
    "port": iosxe_device["port"],
    "auth_username": iosxe_device["auth_username"],
    "auth_password": iosxe_device["auth_password"],
    "auth_strict_key": False,
    "keepalive_interval": iosxe_device["keepalive_interval"],
    "transport": iosxe_device["transport"],
    "keepalive": iosxe_device["keepalive"],
}

conn = IOSXEDriver(**args)
conn.open()

print("***** Get Prompt:")
prompt = conn.get_prompt()
print(prompt)

print("***** Show run | i hostname:")
result = conn.send_command("show run | i hostname")
print(result, result.result)

print("***** Clear logging buffer:")
interact = ["clear logg", "Clear logging buffer [confirm]", "", prompt]
result = conn.send_interactive(interact)
print(result, result.result)

print("***** Show run:")
result = conn.send_command("show run")
print(result, result.result)

if iosxe_device["keepalive"]:
    print("***** Waiting for keepalive....")
    time.sleep(5)

conn.close()
