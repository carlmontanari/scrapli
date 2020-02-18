from scrapli import Scrape

args = {
    "host": "172.18.0.11",
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
}

conn = Scrape(**args)
conn.open()

print(conn.channel.get_prompt())
print(conn.channel.send_inputs("show run | i hostname")[0].result)

# paging is NOT disabled w/ scrapli driver!
conn.channel.send_inputs("terminal length 0")
print(conn.channel.send_inputs("show run")[0].result)
conn.close()


# Context manager is a great way to use scrapli:
with Scrape(**args) as conn:
    result = conn.channel.send_inputs("show run | i hostname")
print(result[0].result)
