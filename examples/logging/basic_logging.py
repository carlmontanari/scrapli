import logging

from nssh import NSSH

logging.basicConfig(filename="nssh.log", level=logging.DEBUG)
logger = logging.getLogger("nssh")

args = {"host": "172.18.0.11", "auth_username": "vrnetlab", "auth_password": "VR-netlab9"}

conn = NSSH(**args)
conn.open()

print(conn.channel.get_prompt())
print(conn.channel.send_inputs("show run | i hostname")[0].result)
