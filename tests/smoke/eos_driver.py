import logging
import time
from pathlib import Path

from device_info import eos_device
from scrapli.driver.core import EOSDriver

logging.basicConfig(
    filename=f"{Path(__file__).resolve().parents[0]}/eos_driver.log", level=logging.DEBUG
)
logger = logging.getLogger("scrapli")

args = {
    "host": eos_device["host"],
    "port": eos_device["port"],
    "auth_username": eos_device["auth_username"],
    "auth_password": eos_device["auth_password"],
    "auth_strict_key": False,
    "keepalive_interval": eos_device["keepalive_interval"],
    "transport": eos_device["transport"],
    "keepalive": eos_device["keepalive"],
    "comms_ansi": True,
}

conn = EOSDriver(**args)
conn.open()

# vrnetlab eos has no enable password so we just enable this manually for now
# conn.channel.send_inputs("enable")

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

if eos_device["keepalive"]:
    print("***** Waiting for keepalive....")
    time.sleep(5)

conn.close()
