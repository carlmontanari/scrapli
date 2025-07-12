"""examples.cli.logging_setup.main"""

import logging
import os
import sys

from scrapli import AuthOptions, Cli

IS_DARWIN = sys.platform == "darwin"
PLATFORM = os.getenv("SCRAPLI_PLATFORM", "nokia_srlinux")
HOST = os.getenv("SCRAPLI_HOST", "localhost" if IS_DARWIN else "172.20.20.16")
PORT = int(os.getenv("SCRAPLI_PORT") or 21022 if IS_DARWIN else 22)
USERNAME = os.getenv("SCRAPLI_USERNAME", "admin")
PASSWORD = os.getenv("SCRAPLI_USERNAME", "NokiaSrl1!")


# nothing special here at all, setup a logging handler just like normal python!
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")


def main() -> None:
    """A simple program to demonstration sending "configurations"."""
    cli = Cli(
        definition_file_or_name=PLATFORM,
        host=HOST,
        port=PORT,
        auth_options=AuthOptions(
            username=USERNAME,
            password=PASSWORD,
        ),
    )

    with cli as c:
        result = c.send_input(
            input_="show version",
            retain_trailing_prompt=True,
        )

        print(result.result)


if __name__ == "__main__":
    main()
