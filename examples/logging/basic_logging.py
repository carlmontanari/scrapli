"""examples.logging.basic_logging"""
import logging

from scrapli.driver.core import IOSXEDriver

# set the name for the logfile and the logging level... thats about it for bare minimum!
logging.basicConfig(filename="scrapli.log", level=logging.DEBUG)

MY_DEVICE = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
}


def main():
    """Example demonstrating basic logging with scrapli"""
    conn = IOSXEDriver(**MY_DEVICE)
    conn.open()
    print(conn.get_prompt())
    print(conn.send_command("show run | i hostname").result)


if __name__ == "__main__":
    main()
