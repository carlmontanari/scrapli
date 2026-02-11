"""examples.cli.proxy_jump_cli.main"""

import os
import sys
from pathlib import Path

from scrapli import AuthOptions, Cli, TransportBinOptions, TransportSsh2Options

IS_DARWIN = sys.platform == "darwin"
PLATFORM = os.getenv("SCRAPLI_PLATFORM", "nokia_srlinux")

# in this case host is only used w/ ssh2, and its going to the "jumper" host; same deal for port
HOST = os.getenv("SCRAPLI_HOST", "localhost" if IS_DARWIN else "172.20.20.19")
PORT = int(os.getenv("SCRAPLI_PORT") or 24022 if IS_DARWIN else 22)

USERNAME = os.getenv("SCRAPLI_USERNAME", "admin")
PASSWORD = os.getenv("SCRAPLI_USERNAME", "NokiaSrl1!")

JUMPER_USERNAME = os.getenv("SCRAPLI_USERNAME_JUMPHOST", "scrapli-pw")
JUMPER_PASSWORD = os.getenv("SCRAPLI_USERNAME_JUMPHOST", "scrapli-123-pw")


def main() -> None:
    """A simple program to show proxy-jumping with bin or ssh2 transports."""
    # for proxy-jumping with the bin transport (meaning /bin/ssh literally) we just do
    # normal proxyjump stuff in a config file, then ensure we pass that file. we pick
    # based on linux/darwin here since in darwin we'll hit the exposed ports vs being able to
    # go straight to the ips on the bridge on a linux box
    ssh_config_file_path_base = f"{Path(__file__).resolve().parent}/ssh_config"

    if IS_DARWIN is True:
        ssh_config_path = ssh_config_file_path_base + "_darwin"
    else:
        ssh_config_path = ssh_config_file_path_base + "_linux"

    # NOTE: make sure you:
    # chmod 600 tests/functional/fixtures/libscrapli_test_ssh_key
    # chmod 600 tests/functional/fixtures/libscrapli_test_ssh_key_passphrase
    # chmod 600 tests/functional/fixtures/scrapli-jumper-key
    # since git wont track those permissions; this is handled in the test suite w/ a pytest hook
    # but you'll need to do it if you want to test this
    bin_cli = Cli(
        definition_file_or_name=PLATFORM,
        # unlike other examples going by name since we have the config file here
        host="srl",
        auth_options=AuthOptions(
            username=USERNAME,
            password=PASSWORD,
        ),
        transport_options=TransportBinOptions(
            ssh_config_path=ssh_config_path,
        ),
    )

    with bin_cli as c:
        result = c.send_input(input_="show version")

        print(result)

    # libssh2 is a little different -- we setup the connection to the *bastion host* like how we
    # normally setup the connection, then under the transport options you can specify how to connect
    # to the final host
    ssh2_cli = Cli(
        definition_file_or_name=PLATFORM,
        host=HOST,
        port=PORT,
        auth_options=AuthOptions(
            username=JUMPER_USERNAME,
            password=JUMPER_PASSWORD,
        ),
        transport_options=TransportSsh2Options(
            # will always be the docker ip of the srl box on darwin or linux (assumes using the
            # scrapli_clab setup)
            proxy_jump_host="172.20.20.16",
            proxy_jump_username=USERNAME,
            proxy_jump_password=PASSWORD,
            # you can also use a local key to auth to the final host, set that under the
            # appropriately named "proxy_jump_private_key_path" setting
        ),
    )

    with ssh2_cli as c:
        result = c.send_input(input_="show version")

        print(result)


if __name__ == "__main__":
    main()
