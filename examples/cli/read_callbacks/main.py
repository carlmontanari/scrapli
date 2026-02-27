"""examples.cli.read_callbacks.main"""

import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from scrapli import AuthOptions, Cli
from scrapli.cli import InputHandling, ReadCallback

IS_DARWIN = sys.platform == "darwin"
PLATFORM = os.getenv("SCRAPLI_PLATFORM", "nokia_srlinux")
HOST = os.getenv("SCRAPLI_HOST", "localhost" if IS_DARWIN else "172.20.20.16")
PORT = int(os.getenv("SCRAPLI_PORT") or 21022 if IS_DARWIN else 22)
USERNAME = os.getenv("SCRAPLI_USERNAME", "admin")
PASSWORD = os.getenv("SCRAPLI_USERNAME", "NokiaSrl1!")

CTRL_C = "\x03"


def logged_in_callback(_: Cli, __: str, ___: str) -> None:
    """A callback to print a message when a user logs in"""
    print("a user has logged in!")


def logged_out_callback(c: Cli, _: str, __: str) -> None:
    """A callback to print a message when a user logs out, also cancels tailing logs"""
    print("a user has logged out!")

    # the callbacks are given as the only parameter a handle to the Cli object, so... with that
    # you can basically do anything ya need. in this case we will send -- ignoring the input, and
    # at the bash mode -- a CTRL+C
    c.send_input(
        input_=CTRL_C,
        input_handling=InputHandling.IGNORE,
        requested_mode="bash",
    )


def callbacks_thread() -> str:
    """A function to run the read_with_callbacks stuff in parallel to a user logging in"""
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
        c.enter_mode(requested_mode="bash")

        # note: many real world use cases of this you would want to include a timeout of 0 here
        # so that you *never* actually timeout and instead rely on your callbacks to know when to
        # stop reading from the device
        result = c.read_with_callbacks(
            # an (optional) initial input to kick off this read+callback operation
            initial_input="tail -f /var/log/messages",
            # a list of "callbacks" which is really more a list of things that *include* a callback
            # and the criteria for triggering that callback
            callbacks=[
                ReadCallback(
                    name="user-logged-in",
                    contains="Starting session",
                    callback=logged_in_callback,
                    # only run this callback *one time*
                    once=True,
                ),
                ReadCallback(
                    name="user-logged-out",
                    contains="disconnected by user",
                    callback=logged_out_callback,
                    once=True,
                    # if this callback is triggered, it means we are "done" with the
                    # `read_with_callbacks` operation
                    completes=True,
                ),
            ],
        )

        return result.result


def trigger_thread() -> str:
    """A function to trigger some log messages by logging in/out"""
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
        # we really just wanna log in/out but we may as well do something while we are in there
        result = c.send_input(input_="show version")

        return result.result


def main() -> None:
    """A simple program to demonstration sending "configurations"."""
    with ThreadPoolExecutor(max_workers=2) as executor:
        # spawn a thread to start doing tail -f on /var/log/messages, then another to log in
        # which will cause some messages to happen
        futures = [executor.submit(callbacks_thread), executor.submit(trigger_thread)]

        for future in as_completed(futures):
            print(future.result())


if __name__ == "__main__":
    main()
