"""examples.non_core_device.wlc"""
import logging
import time

from scrapli.driver import GenericDriver

logging.basicConfig(filename="scrapli.log", level=logging.DEBUG)
logger = logging.getLogger("scrapli")


def wlc_on_open(cls):
    """Example `on_open` function for use with cisco wlc"""
    # time.sleeps here are just because my test device was a bit sluggish, without these scrapli is
    #  just going to send the username/password right away
    time.sleep(0.25)
    # since the channel isn't fully setup, we access the transport and send the commands directly
    #  note that when accessing the transport directly we need to manually send the return char
    cls.transport.write(cls.transport.auth_username)
    cls.transport.write(cls.channel.comms_return_char)
    time.sleep(0.25)
    cls.transport.write(cls.transport.auth_password)
    cls.transport.write(cls.channel.comms_return_char)


def main():
    """Example of working with a non "core" or non standard device"""
    # using a cisco WLC as since it has an interesting login pattern where the it prompts for the
    #  username after the initial ssh connection (even though ssh already knows your username!)
    wlc = {
        "host": "1.2.3.4",
        "auth_username": "some_username",
        "auth_password": "some_password",
        "auth_strict_key": False,
        "auth_bypass": True,
        # set a custom "on_open" function to deal with the non-standard login
        "on_open": wlc_on_open,
        # set a custom "comms_prompt_pattern" to deal with the non-standard prompt pattern
        "comms_prompt_pattern": r"^\(Cisco Controller\) >$",
    }

    conn = GenericDriver(**wlc)
    conn.open()
    print(conn.get_prompt())
    print(conn.send_command("show boot").result)
    conn.close()


if __name__ == "__main__":
    main()
