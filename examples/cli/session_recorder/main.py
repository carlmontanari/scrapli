"""examples.cli.session_logging.main"""

import os
import sys
from pathlib import Path

from scrapli import AuthOptions, Cli, SessionOptions

IS_DARWIN = sys.platform == "darwin"
PLATFORM = os.getenv("SCRAPLI_PLATFORM", "nokia_srlinux")
HOST = os.getenv("SCRAPLI_HOST", "localhost" if IS_DARWIN else "172.20.20.16")
PORT = int(os.getenv("SCRAPLI_PORT") or 21022 if IS_DARWIN else 22)
USERNAME = os.getenv("SCRAPLI_USERNAME", "admin")
PASSWORD = os.getenv("SCRAPLI_USERNAME", "NokiaSrl1!")


def main() -> None:
    """A simple program demonstrate how to log the session input/output."""
    cli = Cli(
        definition_file_or_name=PLATFORM,
        host=HOST,
        port=PORT,
        auth_options=AuthOptions(
            username=USERNAME,
            password=PASSWORD,
        ),
        # to "record" the session (the reads/writes in the "session" -- this is the zig object that
        # is responsible for reading/writing to the underlying transport), we can simply point to
        # a path for the recorder to write to; note you will almost certainly miss the "exit" or
        # "quit" at the end as once the device closes the session the read loop will terminate and
        # that is where we snag the "stuff" to record.
        session_options=SessionOptions(
            recorder_path=f"{Path(__file__).resolve().parent}/session_record.log",
        ),
    )

    with cli as c:
        # we'll just send stuff to have something to look at
        result = c.send_input(input_="show version")

        print(result)


if __name__ == "__main__":
    main()
