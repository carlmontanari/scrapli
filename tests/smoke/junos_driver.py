import logging
import time
from pathlib import Path

from device_info import junos_device

from scrapli.driver.core import JunosDriver

logging.basicConfig(
    filename=f"{Path(__file__).resolve().parents[0]}/junos_driver.log", level=logging.DEBUG
)
logger = logging.getLogger("scrapli")

conn = JunosDriver(**junos_device)
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
