import logging

from scrapli import Scrape

logging.basicConfig(filename="scrapli.log", level=logging.DEBUG)
logger = logging.getLogger("scrapli")

args = {"host": "172.18.0.11", "auth_username": "vrnetlab", "auth_password": "VR-netlab9"}

conn = Scrape(**args)
conn.open()

print(conn.channel.get_prompt())
print(conn.channel.send_inputs("show run | i hostname")[0].result)
