"""examples.cli.output_parsing.main"""

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
        result = c.send_input(input_="show version")

        print(
            # for platforms that have a "textfsm_platform" field, and where ntctemplates are
            # installed, the template will be looked up automatically based on the platform and
            # input. there arent templates for srlinux so we just have a down and dirty one that
            # we can pass here to prove it out. obviously this means you can provide your own
            # templates too if your platform/input is not represented in ntctemplates
            result.textfsm_parse(
                template=f"{Path(__file__).resolve().parent}/nokia_srlinux_show_version.tpl",
            )
        )

        print(
            result.textfsm_parse(
                template=f"{Path(__file__).resolve().parent}/nokia_srlinux_show_version.tpl",
                # normally we convert the output to a dict, but you can skip that if you want
                to_dict=False,
            )
        )

        # parsing works on results that are plural too
        results = c.send_inputs(inputs=["show system lldp neighbor", "show version"])

        print(
            results.textfsm_parse(
                # first-ith input/result to parse, defaults to 0, so set accordingly ofc
                index=1,
                template=f"{Path(__file__).resolve().parent}/nokia_srlinux_show_version.tpl",
                # normally we convert the output to a dict, but you can skip that if you want
                to_dict=False,
            )
        )

        # some platforms will also support genie parsing, but... do yourself a favor and dont
        # use that unless you want to install 90129481092480192 more packages :)


if __name__ == "__main__":
    main()
