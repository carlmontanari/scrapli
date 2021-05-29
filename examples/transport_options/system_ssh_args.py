"""examples.transport_options.system_ssh_args"""
from scrapli.driver.core import IOSXEDriver

MY_DEVICE = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
    "transport_options": {"open_cmd": ["-o", "KexAlgorithms=+diffie-hellman-group1-sha1"]},
}


def main():
    """Simple example demonstrating adding transport options"""
    conn = IOSXEDriver(**MY_DEVICE)
    # with the transport options provided, we can extend the open command to include extra args
    print(conn.transport.open_cmd)

    # deleting the transport options we can see what the default open command would look like
    MY_DEVICE.pop("transport_options")
    del conn
    conn = IOSXEDriver(**MY_DEVICE)
    print(conn.transport.open_cmd)


if __name__ == "__main__":
    main()
