import logging
import time

from scrapli.driver import GenericDriver

logging.basicConfig(filename="scrapli.log", level=logging.DEBUG)
logger = logging.getLogger("scrapli")


def wlc_on_open(cls):
    time.sleep(0.25)
    cls.transport.write(cls.transport.auth_username)
    cls.transport.write(cls.channel.comms_return_char)
    time.sleep(0.25)
    cls.transport.write(cls.transport.auth_password)
    cls.transport.write(cls.channel.comms_return_char)


def main():
    wlc = {
        "host": "1.2.3.4",
        "auth_username": "some_username",
        "auth_password": "some_password",
        "auth_strict_key": False,
        "auth_bypass": True,
        "on_open": wlc_on_open,
        "comms_prompt_pattern": r"^\(Cisco Controller\) >$",
    }

    conn = GenericDriver(**wlc)
    conn.open()
    print(conn.get_prompt())
    print(conn.send_command("show boot").result)
    conn.close()


if __name__ == "__main__":
    main()
