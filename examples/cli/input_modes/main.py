"""examples.cli.input_modes"""

import os
import sys

from scrapli import AuthOptions, Cli

IS_DARWIN = sys.platform == "darwin"
PLATFORM = os.getenv("SCRAPLI_PLATFORM", "nokia_srlinux")
HOST = os.getenv("SCRAPLI_HOST", "localhost" if IS_DARWIN else "172.20.20.16")
PORT = int(os.getenv("SCRAPLI_PORT") or 21022 if IS_DARWIN else 22)
USERNAME = os.getenv("SCRAPLI_USERNAME", "admin")
PASSWORD = os.getenv("SCRAPLI_USERNAME", "NokiaSrl1!")


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
        # you can manually request to "enter" a mode -- in this case we can go into configuration
        # mode. note that if you were to issue a subsequent send_input *without specifying*
        # configuration as the requested mode you would be "dropped" back into exec (the default
        # preferred mode)!
        c.enter_mode(
            requested_mode="configuration",
        )

        # note the "candidate private" -- we are in configuration mode
        print(c.get_prompt().result)

        # to illustrate that we auto try to send inputs from the default mode we can issue a show
        # version, retaining the trailing prompt to verify we are in fact no longer in config mode
        result = c.send_input(
            input_="show version",
            retain_trailing_prompt=True,
        )

        print(result.result)


if __name__ == "__main__":
    main()
