"""examples.basic_usage.generic_driver"""
from scrapli.driver import GenericDriver

MY_DEVICE = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
}


def main():
    """Simple example of connecting to an IOSXEDevice with the GenericDriver"""
    # the `GenericDriver` is a good place to start if your platform is not supported by a "core"
    #  platform drivers
    conn = GenericDriver(**MY_DEVICE)
    conn.open()

    print(conn.channel.get_prompt())
    print(conn.send_command("show run | i hostname").result)

    # IMPORTANT: paging is NOT disabled w/ GenericDriver driver!
    conn.send_command("terminal length 0")
    print(conn.send_command("show run").result)
    conn.close()

    # Context manager is a great way to use scrapli, it will auto open/close the connection for you:
    with GenericDriver(**MY_DEVICE) as conn:
        result = conn.send_command("show run | i hostname")
    print(result.result)


if __name__ == "__main__":
    main()
