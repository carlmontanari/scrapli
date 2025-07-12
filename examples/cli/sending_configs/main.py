"""examples.cli.sending_configs.main"""

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
        # in scrapli (now, not historically) there is really no such thing as a "config" --
        # everything is simply inputs that we send to the device, maybe at different "modes" -- the
        # "mode" possibly being something like "configuration" mode (i.e. the "mode" you get into by
        # doing "config t"). when requesting a different mode, you need to make sure the "mode"
        # exists on the platform definition (see: scrapli_definitions) then entering/exiting modes
        # will be handled for you.
        result = c.send_input(
            input_="show version",
            requested_mode="configuration",
            retain_trailing_prompt=True,
        )

        # above we simply sent a "show version", but we did it in the "configuration" mode -- we
        # also added the `retain_trailing_prompt` flag to retain... the trailing prompt -- just so
        # you can see that we are in fact in "config" mode ("enter candidate private" in srlinux).
        print(result.result)

        # if we want to send a "regular" input again, scrapli will automatically do so from the
        # default mode, which is usually exec/privileged_exec. once again, we retain the trailing
        # prompt so you can confirm/see this. note that *how* you "leave" the config mode varies
        # depending on the platform, so check the definition. in this case its "discard now".
        result = c.send_input(
            input_="show version",
            retain_trailing_prompt=True,
        )

        print(result.result)

        # if you want to actually commit/save (obv depending on your device if that is required)
        # you need to actually send the commit/save command yourself
        _ = c.send_inputs(
            inputs=["set system name host-name foo", "commit now"],
            requested_mode="configuration",
        )

        # and just to confirm for our sanity that it worked...
        result = c.send_input(
            input_="info system name host-name",
            retain_trailing_prompt=True,
        )

        print(result.result)

        # finally, we'll just put that back how we found it...
        _ = c.send_inputs(
            inputs=["set system name host-name srl", "commit now"],
            requested_mode="configuration",
        )


if __name__ == "__main__":
    main()
