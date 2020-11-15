import logging
from pathlib import Path

from device_info import iosxr_device

from scrapli.driver.core import IOSXRDriver

logging.basicConfig(
    filename=f"{Path(__file__).resolve().parents[0]}/iosxr_driver.log", level=logging.DEBUG
)
logger = logging.getLogger("scrapli")

conn = IOSXRDriver(**iosxr_device)
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

conn.close()
