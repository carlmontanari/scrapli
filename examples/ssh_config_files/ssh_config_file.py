from scrapli.driver.core import IOSXEDriver

# setting `ssh_config_file` to True makes scrapli check in ~/.ssh/ and /etc/ssh/ for a file
# named "config", you can also just pass a path to a file of your choosing
args = {
    "host": "172.18.0.11",
    "auth_strict_key": False,
    "ssh_config_file": True
}

with IOSXEDriver(**args) as conn:
    # Platform drivers will auto-magically handle disabling paging for you
    result = conn.send_command("show run")

print(result.result)
