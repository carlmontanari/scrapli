from scrapli.driver import GenericDriver

args = {
    "host": "172.18.0.11",
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
}

# the `GenericDriver` is a good place to start if your platform is not supported by a "core" platform driver
conn = GenericDriver(**args)
conn.open()

print(conn.channel.get_prompt())
print(conn.send_command("show run | i hostname").result)

# paging is NOT disabled w/ GenericDriver driver!
conn.send_command("terminal length 0")
print(conn.send_command("show run").result)
conn.close()


# Context manager is a great way to use scrapli:
with GenericDriver(**args) as conn:
    result = conn.send_command("show run | i hostname")
print(result.result)
