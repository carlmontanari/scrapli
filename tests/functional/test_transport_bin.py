import pytest

from scrapli import (
    AuthOptions,
    Cli,
    LookupKeyValue,
    SessionOptions,
    TransportBinOptions,
)

PROXY_JUMP_ARGNAMES = (
    "platform",
    "input_",
)
PROXY_JUMP_ARGVALUES = (
    (
        "arista_eos",
        "show version | i Kernel",
    ),
    (
        "nokia_srl",
        "show version | grep OS",
    ),
)
PROXY_JUMP_IDS = (
    "arista-eos-bin",
    "nokia_srl-bin",
)


@pytest.mark.parametrize(
    argnames=PROXY_JUMP_ARGNAMES,
    argvalues=PROXY_JUMP_ARGVALUES,
    ids=PROXY_JUMP_IDS,
)
def test_proxy_jump(platform, input_, is_darwin, eos_available, cli_assert_result):
    if platform == "arista_eos":
        if eos_available is False:
            # because we cant have this publicly in ci afaik
            pytest.skip("eos not available, skipping...")

        definition_file_or_name = "arista_eos"
        # hosts are always the clab ip since its from perspective of jumper so even if running on
        # darwin we use the docker name (could use ip but we have the names in the ssh config file)
        host = "ceos"
        auth_options = AuthOptions(
            username="admin",
            password="admin",
            lookups=[LookupKeyValue(key="enable", value="libscrapli")],
        )
    else:
        definition_file_or_name = "nokia_srlinux"
        host = "srl"
        auth_options = AuthOptions(
            username="admin",
            password="NokiaSrl1!",
        )

    # different because darwin we have to deal w/ ports exposed on localhost vs linux
    # having the bridge directly available
    ssh_config_file_path_base = "tests/functional/fixtures/ssh_config"

    if is_darwin is True:
        ssh_config_path = ssh_config_file_path_base + "_darwin"
    else:
        ssh_config_path = ssh_config_file_path_base + "_linux"

    cli = Cli(
        definition_file_or_name=definition_file_or_name,
        host=host,
        auth_options=auth_options,
        session_options=SessionOptions(),
        transport_options=TransportBinOptions(
            ssh_config_path=ssh_config_path,
        ),
    )

    with cli as c:
        cli_assert_result(actual=c.send_input(input_=input_))
