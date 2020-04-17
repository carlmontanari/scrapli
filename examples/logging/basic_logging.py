import logging

from scrapli.driver.core import IOSXEDriver

# set the name for the logfile and the logging level
logging.basicConfig(filename="scrapli.log", level=logging.DEBUG)
# get the scrapli logger, thats about it!
logger = logging.getLogger("scrapli")

MY_DEVICE = {
    "host": "172.18.0.11",
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
}


def main():
    conn = IOSXEDriver(**MY_DEVICE)
    conn.open()
    print(conn.get_prompt())
    print(conn.send_command("show run | i hostname").result)


if __name__ == "__main__":
    main()
