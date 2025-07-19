"""examples.cli.misc_options.main"""

import os
import sys

from scrapli import AuthOptions, Cli
from scrapli.cli import InputHandling
from scrapli.exceptions import OperationException
from scrapli.helper import second_to_nano

IS_DARWIN = sys.platform == "darwin"
PLATFORM = os.getenv("SCRAPLI_PLATFORM", "nokia_srlinux")
HOST = os.getenv("SCRAPLI_HOST", "localhost" if IS_DARWIN else "172.20.20.16")
PORT = int(os.getenv("SCRAPLI_PORT") or 21022 if IS_DARWIN else 22)
USERNAME = os.getenv("SCRAPLI_USERNAME", "admin")
PASSWORD = os.getenv("SCRAPLI_USERNAME", "NokiaSrl1!")


def main() -> None:
    """A simple program to demonstration a few "miscellaneous" send options."""
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
        # retain_trailing_promtp will... retain the prompt after the output from the command you
        # send. this is False by default since normally you'd want just the commands output but
        # obviously sometimes you may want to see the prompt too
        result = c.send_input(
            input_="show version",
            retain_trailing_prompt=True,
        )

        print(result.result)

        # just so output is more clear
        print()

        # we can also retain the input
        result = c.send_input(
            input_="show version",
            retain_input=True,
        )

        print(result.result)

        print()

        # and of course these can be combined
        result = c.send_input(
            input_="show version",
            retain_input=True,
            retain_trailing_prompt=True,
        )

        print(result.result)

        # if you have a super long running command and the default timeout is not long enough,
        # you can crank it up on a per operation basis like so. note that the timeout is in ns --
        # there is a oneliner helper func in the helper package to convert seconds to ns
        _ = c.send_input(
            input_="show version",
            operation_timeout_ns=second_to_nano(d=30),
        )

        # and to show this raising a timeout...
        try:
            _ = c.send_input(
                input_="show version",
                # dont think any input would ever complete in 30ns :)
                operation_timeout_ns=30,
            )
        except OperationException as exc:
            if "TimeoutExceeded" not in str(exc):
                # wasn't the timeout we were expecting...
                raise exc

        # the last option is "input handling" -- there are a few options here:
        # - Exact
        # - Fuzzy
        # - Ignore
        # the gist here is that scrapli "looks" for your inputs before sending the return --
        # historically scrapli has looked for the *exact* input. this is *usually* good, but there
        # are some places where the input you send is not what is reflected in the session; things
        # like banners or "vi-like" input modes, or when a device writes \x08 (backspaces) when your
        # input is going lonver than the terminal width. so, nowadays scrapli "fuzzily" matches the
        # input -- meaning that as long as all the characters you send are in the output in the same
        # order (but if you send "foo" then "f X o X o" would be allowed). lastly, you can *ignore*
        # the input... but you shouldnt do this. this is really just used in netconf operations.
        _ = c.send_input(
            input_="show version",
            input_handling=InputHandling.EXACT,
        )


if __name__ == "__main__":
    main()
