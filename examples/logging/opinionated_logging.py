"""examples.logging.opinionated_logging"""
from scrapli import Scrapli
from scrapli.logging import enable_basic_logging

# the `enable_basic_logging` function accepts a bool or a string for the `file` argument -- if you
# provide a string that string will be used as the output path for the log file, if you just pass
# `True` as in this example, a file called "scrapli.log" will be created in your working directory
enable_basic_logging(file=True, level="debug")

MY_DEVICE = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
    "platform": "cisco_iosxe",
}


def main():
    """
    Example demonstrating basic logging with scrapli

    In this example rather than dealing with python logging module directly, we simply import and
    call the `enable_basic_logging` function of the scrapli.logging package. This will apply logging
    formatting and handlers in an opinionated fashion -- so basically just use this for testing or
    for quickly getting logs, but do not use this for your custom applications.
    """
    with Scrapli(**MY_DEVICE) as conn:
        print(conn.get_prompt())
        print(conn.send_command("show run | i hostname").result)


if __name__ == "__main__":
    main()
