import logging
import time
from pathlib import Path

from device_info import nxos_device
from scrapli.driver.core import NXOSDriver

logging.basicConfig(
    filename=f"{Path(__file__).resolve().parents[0]}/nxos_driver.log", level=logging.DEBUG
)
logger = logging.getLogger("scrapli")

args = {
    "host": nxos_device["host"],
    "port": nxos_device["port"],
    "auth_username": nxos_device["auth_username"],
    "auth_password": nxos_device["auth_password"],
    "auth_strict_key": False,
    "keepalive_interval": nxos_device["keepalive_interval"],
    "transport": nxos_device["transport"],
    "keepalive": nxos_device["keepalive"],
}

conn = NXOSDriver(**args)
conn.open()

print("***** Get Prompt:")
prompt = conn.get_prompt()
print(prompt)

print("***** Show run | i hostname:")
result = conn.send_command("show run | i hostname")
print(result, result.result)

print("***** Disable Paging:")
result = conn.send_command("term length 0")
print(result, result.result)

print("***** Show run:")
result = conn.send_command("show run")
print(result, result.result)

if nxos_device["keepalive"]:
    print("***** Waiting for keepalive....")
    time.sleep(5)

conn.close()
