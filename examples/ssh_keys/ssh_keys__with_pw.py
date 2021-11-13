"""examples.ssh_keys.ssh_keys"""
from pathlib import Path

import scrapli
from scrapli.driver import GenericDriver

SSH_KEYS_EXAMPLE_DIR = f"{Path(scrapli.__file__).parents[1]}/examples/ssh_keys"


MY_DEVICE = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_private_key": f"{SSH_KEYS_EXAMPLE_DIR}/scrapli_key_w-pw",
    "auth_private_key_passphrase": "scrapli_key_w-pw",
    "auth_strict_key": False,
    "transport": "ssh2",
}


def main():
    """
    Example demonstrating handling authentication with ssh private key
    where the latter is protected with a password

    Make sure the key permissions are 0600!
    """
    with GenericDriver(**MY_DEVICE) as conn:
        result = conn.send_command("show run | i hostname")
    print(result.result)


if __name__ == "__main__":
    main()
