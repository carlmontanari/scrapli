"""examples.ssh_config_files.ssh_config_file"""
from scrapli.driver.core import IOSXEDriver

# setting `ssh_config_file` to True makes scrapli check in ~/.ssh/ and /etc/ssh/ for a file named
#  "config" or "ssh_config" respectively (standard openssh naming convention basically). You can
#  also just pass a path to a file of your choosing as we do here
MY_DEVICE = {
    "host": "172.18.0.11",
    "auth_strict_key": False,
    "ssh_config_file": "ssh_config",
}


def main():
    """Example demonstrating handling authentication/connection settings via ssh config file"""
    with IOSXEDriver(**MY_DEVICE) as conn:
        result = conn.send_command("show run")

    print(result.result)


if __name__ == "__main__":
    main()
