"""examples.cli.custom_definition.main"""

import os
import sys
from pathlib import Path

from scrapli import AuthOptions, Cli

IS_DARWIN = sys.platform == "darwin"
HOST = os.getenv("SCRAPLI_HOST", "localhost" if IS_DARWIN else "172.20.20.16")
PORT = int(os.getenv("SCRAPLI_PORT") or 21022 if IS_DARWIN else 22)
USERNAME = os.getenv("SCRAPLI_USERNAME", "admin")
PASSWORD = os.getenv("SCRAPLI_USERNAME", "NokiaSrl1!")


def main() -> None:
    """Demonstrate using a custom platform definition"""
    cli = Cli(
        # this is exactly the same as the upstream definition but just doing this to show that
        # you can load up any yaml definition and dont necessarily need to rely on the upstream
        # stuff in scrapli_definitions
        definition_file_or_name=f"{Path(__file__).resolve().parent}/foo_bar.yaml",
        host=HOST,
        port=PORT,
        auth_options=AuthOptions(
            username=USERNAME,
            password=PASSWORD,
        ),
    )

    with cli as c:
        # we'll just send stuff to have something to look at
        result = c.send_input(input_="show version")

        print(result)


if __name__ == "__main__":
    main()
