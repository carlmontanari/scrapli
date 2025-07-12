"""examples.cli.sending_inputs.main"""

import os
import sys
from pathlib import Path

from scrapli import AuthOptions, Cli

IS_DARWIN = sys.platform == "darwin"
PLATFORM = os.getenv("SCRAPLI_PLATFORM", "nokia_srlinux")
HOST = os.getenv("SCRAPLI_HOST", "localhost" if IS_DARWIN else "172.20.20.16")
PORT = int(os.getenv("SCRAPLI_PORT") or 21022 if IS_DARWIN else 22)
USERNAME = os.getenv("SCRAPLI_USERNAME", "admin")
PASSWORD = os.getenv("SCRAPLI_USERNAME", "NokiaSrl1!")


def main() -> None:
    """A simple program to use various input sending methods for demonstration."""
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
        # send a single "input" at the "default mode" (normally privileged exec or similar)
        result = c.send_input(input_="show version")

        # the result object returned holds info about the operation -- start/end/duration, the
        # input(s) sent, the result, the raw result (as in before ascii/ansii cleaning), and a few
        # other things. it has a reasonable __str__ method, so printing it should give you some
        # something to look at
        print(result)

        # but if you want to just see the result itself you can do like so:
        print(result.result)

        # theres a plural method for... sending multiple inputs, shock!
        results = c.send_inputs(inputs=["show version", "show version"])

        # result will print a joined result
        print(results.result)

        # there is also a from_file method to send inputs from a file if you want
        results_from_file = c.send_inputs_from_file(
            f=f"{Path(__file__).resolve().parent}/inputs_to_send",
        )

        print(results_from_file)


if __name__ == "__main__":
    main()
