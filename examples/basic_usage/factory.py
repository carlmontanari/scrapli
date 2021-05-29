"""examples.basic_usage.factory"""
from scrapli import Scrapli

MY_DEVICE = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
    "platform": "cisco_iosxe",
}


def main():
    """Scrapli factory will return an IOSXEDriver object based on the platform provided"""
    with Scrapli(**MY_DEVICE) as conn:
        result = conn.send_command("show run")

    print(result.result)


if __name__ == "__main__":
    main()
