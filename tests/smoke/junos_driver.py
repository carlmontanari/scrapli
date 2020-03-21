import logging
import time
from pathlib import Path

from device_info import junos_device
from scrapli.driver.core import JunosDriver

logging.basicConfig(
    filename=f"{Path(__file__).resolve().parents[0]}/junos_driver.log", level=logging.DEBUG
)
logger = logging.getLogger("scrapli")

args = {
    "host": junos_device["host"],
    "port": junos_device["port"],
    "auth_username": junos_device["auth_username"],
    "auth_password": junos_device["auth_password"],
    "auth_strict_key": False,
    "keepalive_interval": junos_device["keepalive_interval"],
    "transport": junos_device["transport"],
    "keepalive": junos_device["keepalive"],
}

conn = JunosDriver(**args)
conn.open()

print("***** Get Prompt:")
prompt = conn.get_prompt()
print(prompt)

print("***** Show configuration | match 10.0.0.15:")
result = conn.send_command("show configuration | match 10.0.0.15")
print(result, result.result)

print("***** Show configuration:")
result = conn.send_command("show configuration")
print(result, result.result)

if junos_device["keepalive"]:
    print("***** Waiting for keepalive....")
    time.sleep(5)

conn.close()
