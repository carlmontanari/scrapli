import logging
import time
from pathlib import Path

from device_info import iosxe_device

from scrapli.driver.core import IOSXEDriver

logging.basicConfig(
    filename=f"{Path(__file__).resolve().parents[0]}/iosxe_driver.log", level=logging.DEBUG
)
logger = logging.getLogger("scrapli")

conn = IOSXEDriver(**iosxe_device)
conn.open()

print("***** Get Prompt:")
prompt = conn.get_prompt()
print(prompt)

print("***** Show run | i hostname:")
result = conn.send_command("show run | i hostname")
print(result, result.result)

print("***** Clear logging buffer:")
interact = [("clear logg", "Clear logging buffer [confirm]"), ("", prompt)]
result = conn.send_interactive(interact)
print(result, result.result)

print("***** Show run:")
result = conn.send_command("show run")
print(result, result.result)

if iosxe_device["keepalive"]:
    print("***** Waiting for keepalive....")
    time.sleep(2)

conn.close()
