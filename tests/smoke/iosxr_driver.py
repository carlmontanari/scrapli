import logging
import time
from pathlib import Path

from device_info import iosxr_device
from scrapli.driver.core import IOSXRDriver

logging.basicConfig(
    filename=f"{Path(__file__).resolve().parents[0]}/iosxr_driver.log", level=logging.DEBUG
)
logger = logging.getLogger("scrapli")

args = {
    "host": iosxr_device["host"],
    "port": iosxr_device["port"],
    "auth_username": iosxr_device["auth_username"],
    "auth_password": iosxr_device["auth_password"],
    "auth_strict_key": False,
    "keepalive_interval": iosxr_device["keepalive_interval"],
    "transport": iosxr_device["transport"],
    "keepalive": iosxr_device["keepalive"],
}

conn = IOSXRDriver(**args)
conn.open()

print("***** Get Prompt:")
prompt = conn.get_prompt()
print(prompt)

print("***** Show run | i hostname:")
result = conn.send_command("show run | i hostname")
print(result, result.result)

print("***** Show run:")
result = conn.send_command("show run")
print(result, result.result)

if iosxr_device["keepalive"]:
    print("***** Waiting for keepalive....")
    time.sleep(5)

conn.close()
