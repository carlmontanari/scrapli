from pathlib import Path

from scrapli import (
    AuthOptions,
    Cli,
    LookupKeyValue,
    Netconf,
    NetconfOptions,
    SessionOptions,
    TransportBinOptions,
    TransportSsh2Options,
)
from scrapli.netconf import Version


def test_auth_options(options_assert_result):
    c = Cli(
        host="1.2.3.4",
        auth_options=AuthOptions(
            username="foo",
            password="bar",
            private_key_path="secretpath",
            private_key_passphrase="secretpassphrase",
            lookups=[LookupKeyValue(key="baz", value="qux")],
            force_in_session_auth=True,
            username_pattern="usernamepattern",
            password_pattern="passwordpattern",
            private_key_passphrase_pattern="passphrasepattern",
        ),
    )

    actual = c._get_options()

    options_assert_result(actual=actual, f=f"{Path(__file__).parent}/golden/options/auth.json")


def test_cli_options(options_assert_result):
    c = Cli(
        host="1.2.3.4",
    )

    actual = c._get_options()

    options_assert_result(actual=actual, f=f"{Path(__file__).parent}/golden/options/cli.json")


def test_common_options(options_assert_result):
    c = Cli(
        host="1.2.3.4",
        port=1234,
    )

    actual = c._get_options()

    options_assert_result(actual=actual, f=f"{Path(__file__).parent}/golden/options/common.json")


def test_netconf_options(options_assert_result):
    n = Netconf(
        host="1.2.3.4",
        options=NetconfOptions(
            error_tag="<errrrrrro>",
            preferred_version=Version.VERSION_1_0,
            message_poll_interval_ns=999999,
        ),
    )

    actual = n._get_options()

    options_assert_result(actual=actual, f=f"{Path(__file__).parent}/golden/options/netconf.json")


def test_session_options(options_assert_result):
    c = Cli(
        host="1.2.3.4",
        session_options=SessionOptions(
            read_size=999,
            read_min_delay_ns=123,
            read_max_delay_ns=456,
            return_char="return",
            operation_timeout_s=3600,
            operation_timeout_ns=3600000,
            operation_max_search_depth=9876,
            recorder_path="recorderoutput",
        ),
    )

    actual = c._get_options()

    options_assert_result(actual=actual, f=f"{Path(__file__).parent}/golden/options/session.json")


def test_transport_bin_options(options_assert_result):
    c = Cli(
        host="1.2.3.4",
        transport_options=TransportBinOptions(
            bin="/myyyyy/bin",
            extra_open_args="-o ProxyCommand='foo' -P 1234",
            override_open_args="alll the args",
            ssh_config_path="the/config/file",
            known_hosts_path="the/known/hosts",
            enable_strict_key=True,
            term_height=123,
            term_width=456,
        ),
    )

    actual = c._get_options()

    options_assert_result(
        actual=actual, f=f"{Path(__file__).parent}/golden/options/transport_bin.json"
    )


def test_transport_ssh2_options(options_assert_result):
    c = Cli(
        host="1.2.3.4",
        transport_options=TransportSsh2Options(
            known_hosts_path="ssh2/known/hosts/path",
            libssh2_trace=True,
            proxy_jump_host="thisjumpyhost",
            proxy_jump_port=1234,
            proxy_jump_username="jumpuser",
            proxy_jump_password="jumppass",
            proxy_jump_private_key_path="jumpprivatekey",
            proxy_jump_private_key_passphrase="jumpprivatekeypassphrase",
            proxy_jump_libssh2_trace=True,
        ),
    )

    actual = c._get_options()

    options_assert_result(
        actual=actual, f=f"{Path(__file__).parent}/golden/options/transport_ssh2.json"
    )
