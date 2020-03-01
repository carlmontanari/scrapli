import logging
from pathlib import Path

from device_info import device
from scrapli import ConnectHandler

logging.basicConfig(
    filename=f"{Path(__file__).resolve().parents[0]}/netmiko_style.log", level=logging.DEBUG
)
logger = logging.getLogger("scrapli")

netmiko_device = {}
netmiko_device["device_type"] = "cisco_xe"
netmiko_device["host"] = device["host"]
netmiko_device["port"] = device["port"]
netmiko_device["username"] = device["auth_username"]
netmiko_device["password"] = device["auth_password"]

conn = ConnectHandler(auto_open=False, **netmiko_device)
conn.open()

print(conn.find_prompt())
print(conn.send_command("show run | i hostname"))
print(conn.send_command("show ip int brief", use_textfsm=True))
print(conn.send_config_set(["interface loopback123", "description racecar"]))
