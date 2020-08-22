import logging
import time
from pathlib import Path

from device_info import eos_device

from scrapli.driver.core import EOSDriver

logging.basicConfig(
    filename=f"{Path(__file__).resolve().parents[0]}/eos_driver.log", level=logging.DEBUG
)
logger = logging.getLogger("scrapli")

conn = EOSDriver(**eos_device, auth_secondary="VR-netlab9")
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

if eos_device["keepalive"]:
    print("***** Waiting for keepalive....")
    time.sleep(5)

conn.close()
