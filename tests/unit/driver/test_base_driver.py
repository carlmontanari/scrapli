import logging
import os
import sys
from pathlib import Path

import pytest

import scrapli
from scrapli import Scrape
from scrapli.exceptions import UnsupportedPlatform

TEST_DATA_DIR = f"{Path(scrapli.__file__).parents[1]}/tests/test_data"


def test__str():
    conn = Scrape(host="myhost")
    assert str(conn) == "Scrape Object for host myhost"


def test__repr():
    conn = Scrape(host="myhost")
    assert (
        repr(conn)
        == "Scrape(host='myhost', port=22, auth_username='', auth_password='', auth_private_key='', "
        "auth_private_key_passphrase='', auth_strict_key=True, auth_bypass=False, timeout_socket=5, "
        "timeout_transport=10, timeout_ops=30.0, timeout_exit=True, comms_prompt_pattern='^[a-z0-9.\\\\-@()/:]{1,"
        "48}[#>$]\\\\s*$', comms_return_char='\\n', comms_ansi=False, ssh_config_file='', ssh_known_hosts_file='', "
        "on_init=None, on_open=None, on_close=None, transport='system', transport_options=None)"
    )


@pytest.mark.parametrize(
    "attr_setup",
    [
        ("host", "", ValueError, "`host` should be a hostname/ip address, got nothing!"),
        ("port", "notanint", TypeError, "`port` should be int, got <class 'str'>"),
        (
            "auth_strict_key",
            "notabool",
            TypeError,
            "`auth_strict_key` should be bool, got <class 'str'>",
        ),
        (
            "auth_private_key",
            "notafile",
            ValueError,
            "Provided public key `notafile` is not a file",
        ),
        (
            "auth_bypass",
            "notabool",
            TypeError,
            "`auth_bypass` should be bool, got <class 'str'>",
        ),
        ("timeout_exit", "notabool", TypeError, "`timeout_exit` should be bool, got <class 'str'>"),
        (
            "comms_return_char",
            True,
            TypeError,
            "`comms_return_char` should be str, got <class 'bool'>",
        ),
        ("comms_ansi", "notabool", TypeError, "`comms_ansi` should be bool, got <class 'str'>"),
        ("on_init", "notacallable", TypeError, "`on_init` must be a callable, got <class 'str'>"),
        ("on_open", "notacallable", TypeError, "`on_open` must be a callable, got <class 'str'>"),
        ("on_close", "notacallable", TypeError, "`on_close` must be a callable, got <class 'str'>"),
        (
            "ssh_config_file",
            None,
            TypeError,
            "`ssh_config_file` must be str or bool, got <class 'NoneType'>",
        ),
        (
            "ssh_known_hosts_file",
            None,
            TypeError,
            "`ssh_known_hosts_file` must be str or bool, got <class 'NoneType'>",
        ),
    ],
    ids=[
        "host",
        "port",
        "auth_strict_key",
        "auth_private_key",
        "auth_bypass",
        "timeout_exit",
        "comms_return_char",
        "comms_ansi",
        "on_init",
        "on_open",
        "on_close",
        "ssh_config_file",
        "ssh_known_hosts_file",
    ],
)
def test_exceptions_raised(attr_setup):
    attr_name = attr_setup[0]
    attr_value = attr_setup[1]
    attr_exc = attr_setup[2]
    attr_msg = attr_setup[3]
    args = {attr_name: attr_value}
    if attr_name != "host":
        args["host"] = "myhost"
    with pytest.raises(attr_exc) as exc:
        Scrape(**args)
    assert str(exc.value) == attr_msg


def test_unsupported_platform():
    original_platform = sys.platform
    sys.platform = "win32"
    with pytest.raises(UnsupportedPlatform) as exc:
        Scrape(host="localhost")
    assert (
        str(exc.value)
        == "`system` transport is not supported on Windows, please use a different transport"
    )
    sys.platform = original_platform


@pytest.mark.parametrize(
    "attr_setup",
    [
        ("host", "myhost", "myhost"),
        ("host", "myhost ", "myhost"),
        ("port", 123, 123),
        ("auth_username", "tacocat", "tacocat"),
        ("auth_username", "tacocat ", "tacocat"),
        ("auth_password", "tacocat", "tacocat"),
        ("auth_password", "tacocat ", "tacocat"),
        (
            "auth_private_key",
            f"{TEST_DATA_DIR}/files/_ssh_config",
            f"{TEST_DATA_DIR}/files/_ssh_config",
        ),
        ("auth_private_key_passphrase", "tacocat", "tacocat"),
        ("auth_private_key_passphrase", "tacocat ", "tacocat"),
        ("auth_strict_key", False, False),
        ("timeout_socket", 100, 100),
        ("timeout_transport", 100, 100),
        ("timeout_ops", 100, 100),
        ("timeout_exit", False, False),
        ("comms_prompt_pattern", "tacocat", "tacocat"),
        ("comms_return_char", "tacocat", "tacocat"),
        ("comms_ansi", True, True),
        ("on_init", print, print),
        ("on_open", print, print),
        ("on_close", print, print),
        ("transport", "telnet", "telnet"),
    ],
    ids=[
        "host",
        "host_strip",
        "port",
        "auth_username",
        "auth_username_strip",
        "auth_password",
        "auth_password_strip",
        "auth_private_key",
        "auth_private_key_passphrase",
        "auth_private_key_passphrase_strip",
        "auth_strict_key",
        "timeout_socket",
        "timeout_transport",
        "timeout_ops",
        "timeout_exit",
        "comms_prompt_pattern",
        "comms_return_char",
        "comms_ansi",
        "on_init",
        "on_open",
        "on_close",
        "transport",
    ],
)
def test_attr_assignment(attr_setup):
    attr_name = attr_setup[0]
    attr_value = attr_setup[1]
    attr_expected = attr_setup[2]
    args = {attr_name: attr_value}
    if attr_name != "host":
        args["host"] = "myhost"
    conn = Scrape(**args)
    if attr_name == "transport":
        conn.transport_class == attr_expected
    else:
        assert conn._initialization_args.get(attr_name) == attr_expected


def test_log_non_core_transport(caplog):
    with caplog.at_level(logging.INFO):
        Scrape(host="myhost", transport="paramiko")
    assert "Non-core transport `paramiko` selected" in caplog.text


def test_transport_options():
    conn = Scrape(host="localhost", transport_options={"someoption": "somethingneat"})
    assert conn.transport_args["transport_options"] == {"someoption": "somethingneat"}


def test_valid_private_key_file():
    auth_private_key = f"{TEST_DATA_DIR}/files/_ssh_private_key"
    conn = Scrape(host="myhost", auth_private_key=auth_private_key)
    assert (
        conn._initialization_args["auth_private_key"] == f"{TEST_DATA_DIR}/files/_ssh_private_key"
    )


@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="not currently testing ssh file resolution on windows"
)
@pytest.mark.parametrize(
    "ssh_file",
    [
        ("ssh_config_file", True, "/etc/ssh/ssh_config", f"{TEST_DATA_DIR}/files/_ssh_config"),
        (
            "ssh_config_file",
            True,
            f"{os.path.expanduser('~')}/.ssh/config",
            f"{TEST_DATA_DIR}/files/_ssh_config",
        ),
        (
            "ssh_config_file",
            f"{TEST_DATA_DIR}/files/_ssh_known_hosts",
            f"{TEST_DATA_DIR}/files/_ssh_known_hosts",
            f"{TEST_DATA_DIR}/files/_ssh_config",
        ),
        (
            "ssh_config_file",
            "",
            "",
            "",
        ),
        (
            "ssh_known_hosts_file",
            True,
            "/etc/ssh/ssh_known_hosts",
            f"{TEST_DATA_DIR}/files/_ssh_known_hosts",
        ),
        (
            "ssh_known_hosts_file",
            True,
            f"{os.path.expanduser('~')}/.ssh/known_hosts",
            f"{TEST_DATA_DIR}/files/_ssh_known_hosts",
        ),
        (
            "ssh_known_hosts_file",
            f"{TEST_DATA_DIR}/files/_ssh_known_hosts",
            f"{TEST_DATA_DIR}/files/_ssh_known_hosts",
            f"{TEST_DATA_DIR}/files/_ssh_known_hosts",
        ),
        (
            "ssh_known_hosts_file",
            "",
            "",
            "",
        ),
    ],
    ids=[
        "config_file_etc",
        "config_file_user",
        "config_file_manual",
        "config_file_not_found",
        "known_hosts_file_etc",
        "known_hosts_file_user",
        "known_hosts_file_manual",
        "known_hosts_file_not_found",
    ],
)
def test_ssh_files(fs, ssh_file):
    attr_name = ssh_file[0]
    attr_value = ssh_file[1]
    attr_expected = ssh_file[2]
    attr_src = ssh_file[3]
    args = {attr_name: attr_value}

    if attr_src and attr_expected:
        fs.add_real_file(source_path=attr_src, target_path=attr_expected)

    conn = Scrape(host="myhost", **args)
    assert conn._initialization_args[attr_name] == attr_expected


def test_isalive_no_transport():
    # test to ensure we handle attribute error to show that scrape is not alive if transport does
    # not exist yet
    conn = Scrape(host="myhost")
    assert conn.isalive() is False
