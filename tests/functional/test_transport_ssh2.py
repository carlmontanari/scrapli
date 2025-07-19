import pytest

from scrapli import (
    AuthOptions,
    Cli,
    LookupKeyValue,
    Netconf,
    SessionOptions,
    TransportSsh2Options,
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
def test_proxy_jump_ssh2(platform, input_, is_darwin, eos_available, cli_assert_result):
    if platform == "arista_eos":
        if eos_available is False:
            # because we cant have this publicly in ci afaik
            pytest.skip("eos not available, skipping...")

        definition_file_or_name = "arista_eos"

        transport_options = TransportSsh2Options(
            proxy_jump_host="172.20.20.17",
            proxy_jump_username="admin",
            proxy_jump_password="admin",
        )
    else:
        definition_file_or_name = "nokia_srlinux"

        transport_options = TransportSsh2Options(
            proxy_jump_host="172.20.20.16",
            proxy_jump_username="admin",
            proxy_jump_password="NokiaSrl1!",
        )

    cli = Cli(
        definition_file_or_name=definition_file_or_name,
        host="localhost" if is_darwin else "172.20.20.19",
        port=24022 if is_darwin else 22,
        auth_options=AuthOptions(
            # to the jumphost
            username="scrapli-pw",
            password="scrapli-123-pw",
            # we use the lookups from primary auth regardless
            lookups=[LookupKeyValue(key="enable", value="libscrapli")],
        ),
        session_options=SessionOptions(),
        transport_options=transport_options,
    )

    with cli as c:
        cli_assert_result(actual=c.send_input(input_=input_))


PROXY_JUMP_NETCONF_ARGNAMES = (
    "platform",
    "filter_",
)
PROXY_JUMP_NETCONF_ARGVALUES = (
    (
        "arista_eos",
        "<system><config><hostname></hostname></config></system>",
    ),
    (
        "nokia_srl",
        '<system xmlns="urn:nokia.com:srlinux:general:system"><ssh-server xmlns="urn:nokia.com:srlinux:linux:ssh"><name>mgmt</name></ssh-server></system>',
    ),
)
PROXY_JUMP_NETCONF_IDS = (
    "arista-eos-bin",
    "nokia_srl-bin",
)


@pytest.mark.parametrize(
    argnames=PROXY_JUMP_NETCONF_ARGNAMES,
    argvalues=PROXY_JUMP_NETCONF_ARGVALUES,
    ids=PROXY_JUMP_NETCONF_IDS,
)
def test_proxy_jump_netconf_ssh2(
    platform, filter_, is_darwin, eos_available, netconf_assert_result
):
    if platform == "arista_eos":
        if eos_available is False:
            # because we cant have this publicly in ci afaik
            pytest.skip("eos not available, skipping...")

        transport_options = TransportSsh2Options(
            proxy_jump_host="172.20.20.17",
            proxy_jump_port=830,
            proxy_jump_username="admin",
            proxy_jump_password="admin",
        )
    else:
        transport_options = TransportSsh2Options(
            proxy_jump_host="172.20.20.16",
            proxy_jump_port=830,
            proxy_jump_username="admin",
            proxy_jump_password="NokiaSrl1!",
        )

    netconf = Netconf(
        host="localhost" if is_darwin else "172.20.20.19",
        port=24022 if is_darwin else 22,
        auth_options=AuthOptions(
            # to the jumphost
            username="scrapli-pw",
            password="scrapli-123-pw",
            # we use the lookups from primary auth regardless
            lookups=[LookupKeyValue(key="enable", value="libscrapli")],
        ),
        session_options=SessionOptions(),
        transport_options=transport_options,
    )

    with netconf as n:
        netconf_assert_result(actual=n.get(filter_=filter_))
