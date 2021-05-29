"""examples.ssh_keys.ssh_keys"""
from pathlib import Path

import scrapli
from scrapli.driver.core import IOSXEDriver

SSH_KEYS_EXAMPLE_DIR = f"{Path(scrapli.__file__).parents[1]}/examples/ssh_keys"


MY_DEVICE = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_private_key": f"{SSH_KEYS_EXAMPLE_DIR}/scrapli_key",
    "auth_strict_key": False,
}


def main():
    """
    Example demonstrating handling authentication with ssh private key

    Make sure the key permissions are 0600!
    """
    with IOSXEDriver(**MY_DEVICE) as conn:
        # Platform drivers will auto-magically handle disabling paging for you
        result = conn.send_command("show run")

    print(result.result)


if __name__ == "__main__":
    main()
