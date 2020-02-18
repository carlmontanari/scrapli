from scrapli.driver.core import IOSXEDriver

args = {
    "host": "172.18.0.11",
    "auth_username": "vrnetlab",
    "auth_public_key": "/path/to/your/key",
    "auth_strict_key": False,
}

with IOSXEDriver(**args) as conn:
    # Platform drivers will auto-magically handle disabling paging for you
    result = conn.channel.send_inputs("show run")

print(result[0].result)
