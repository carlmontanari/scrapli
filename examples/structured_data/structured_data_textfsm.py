"""examples.structured_data.structured_data_textfsm"""
from scrapli.driver.core import IOSXEDriver

MY_DEVICE = {
    "host": "172.18.0.11",
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
}


def main():
    """Simple example demonstrating getting structured data via the genie parsing library"""
    with IOSXEDriver(**MY_DEVICE) as conn:
        # Platform drivers will auto-magically handle disabling paging for you
        result = conn.send_command("show run")

    print(result.result)
    print(result.textfsm_parse_output())


if __name__ == "__main__":
    main()
