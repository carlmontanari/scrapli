import logging
import time
from pathlib import Path

from device_info import device

from scrapli.driver.core import IOSXEDriver

logging.basicConfig(
    filename=f"{Path(__file__).resolve().parents[0]}/ssh_config_file_and_key_auth.log",
    level=logging.DEBUG,
)
logger = logging.getLogger("scrapli")

args = {
    "host": device["host"],
    "port": device["port"],
    "ssh_config_file": True,
    "auth_strict_key": False,
    "keepalive_interval": device["keepalive_interval"],
    "transport": device["transport"],
    "keepalive": device["keepalive"],
}

conn = IOSXEDriver(**args)
conn.open()

print("***** Get Prompt:")
print(conn.get_prompt())

print("***** Show run | i hostname:")
result = conn.send_commands("show run | i hostname")
print(result, result[0].result)

print("***** Clear logging buffer:")
interact = [("clear logg", "Clear logging buffer [confirm]"), ("", "3560CX#")]
result = conn.send_interactive(interact)
print(result, result[0].result)

print("***** Disable Paging:")
result = conn.send_commands("term length 0")
print(result, result[0].result)

print("***** Show run:")
result = conn.send_commands("show run")
print(result, result[0].result)

if device["keepalive"]:
    print("***** Waiting for keepalive....")
    time.sleep(5)

conn.close()
