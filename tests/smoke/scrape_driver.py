import logging
import time
from pathlib import Path

from device_info import device
from scrapli import Scrape

logging.basicConfig(
    filename=f"{Path(__file__).resolve().parents[0]}/scrape_driver.log", level=logging.DEBUG
)
logger = logging.getLogger("scrapli")

args = {
    "host": device["host"],
    "port": device["port"],
    "auth_username": device["auth_username"],
    "auth_password": device["auth_password"],
    "auth_strict_key": False,
    "keepalive_interval": device["keepalive_interval"],
    "transport": device["transport"],
    "keepalive": device["keepalive"],
}

conn = Scrape(**args)
conn.open()

print("***** Get Prompt:")
print(conn.channel.get_prompt())

print("***** Show run | i hostname:")
result = conn.channel.send_inputs("show run | i hostname")
print(result, result[0].result)

print("***** Clear logging buffer:")
interact = ("clear logg", "Clear logging buffer [confirm]", "", "3560CX#")
result = conn.channel.send_inputs_interact(interact)
print(result, result[0].result)

print("***** Disable Paging:")
result = conn.channel.send_inputs("term length 0")
print(result, result[0].result)

print("***** Show run:")
result = conn.channel.send_inputs("show run")
print(result, result[0].result)

if device["keepalive"]:
    print("***** Waiting for keepalive....")
    time.sleep(5)

conn.close()
