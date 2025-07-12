"""examples.cli.handling_interactions.main"""

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
    """Show how we can 'interact' with prompts on a device"""
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
        # just using read to force an interactive-like prompt on our srlinux test box
        result = c.send_prompted_input(
            input_="read -p 'interactwithme: '",
            prompt="interactwithme",
            prompt_pattern="",
            response="foo",
            requested_mode="bash",
        )

        # just printing the full result so we can see the whole thing to see it worked
        print(result.result)


if __name__ == "__main__":
    main()
