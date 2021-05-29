"""examples.basic_usage.scrapli_driver"""
from scrapli import Driver

MY_DEVICE = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
}


def main():
    """Example demonstrating using the `Driver` driver directly"""
    # the `Driver` driver is only for use if you *really* want to manually handle the channel
    # input/output if your device type is supported by a core platform you should probably use that,
    # otherwise check out the `GenericDriver` before diving into `Driver` as a last resort!
    conn = Driver(**MY_DEVICE)
    conn.open()

    print(conn.channel.get_prompt())
    print(conn.channel.send_input("show run | i hostname")[1])

    # paging is NOT disabled w/ Scrape driver!
    conn.channel.send_input("terminal length 0")
    print(conn.channel.send_input("show run")[1])
    conn.close()

    # Context manager is a great way to use scrapli:
    with Driver(**MY_DEVICE) as conn:
        result = conn.channel.send_input("show run | i hostname")
    print(result[1])


if __name__ == "__main__":
    main()
