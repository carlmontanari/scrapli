import os
from pathlib import Path

import pytest

import scrapli
from scrapli import Scrape

UNIT_TEST_DIR = f"{Path(scrapli.__file__).parents[1]}/tests/unit/"


def test__str():
    conn = Scrape(host="myhost")
    assert str(conn) == "Scrape Object for host myhost"


def test__repr():
    conn = Scrape(host="myhost")
    assert (
        repr(conn)
        == "Scrape(host='myhost', port=22, auth_username='', auth_password='', auth_private_key=b'', "
        "auth_strict_key=True, timeout_socket=5, timeout_transport=5, timeout_ops=10, timeout_exit=True, "
        "keepalive=False, keepalive_interval=30, keepalive_type='network', keepalive_pattern='\\x05', "
        "comms_prompt_pattern='^[a-z0-9.\\\\-@()/:]{1,32}[#>$]\\\\s*$', comms_return_char='\\n', comms_ansi=False, "
        "ssh_config_file='', ssh_known_hosts_file='', on_open=None, on_close=None, transport='system')"
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
        ("timeout_exit", "notabool", TypeError, "`timeout_exit` should be bool, got <class 'str'>"),
        ("keepalive", "notabool", TypeError, "`keepalive` should be bool, got <class 'str'>"),
        (
            "keepalive_type",
            "notvalid",
            ValueError,
            "`notvalid` is an invalid keepalive_type; must be 'network' or 'standard'",
        ),
        (
            "comms_return_char",
            True,
            TypeError,
            "`comms_return_char` should be str, got <class 'bool'>",
        ),
        ("comms_ansi", "notabool", TypeError, "`comms_ansi` should be bool, got <class 'str'>"),
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
        (
            "transport",
            "notatransport",
            ValueError,
            "`transport` should be one of ssh2|paramiko|system|telnet, got `notatransport`",
        ),
    ],
    ids=[
        "host",
        "port",
        "auth_strict_key",
        "auth_private_key",
        "timeout_exit",
        "keepalive",
        "keepalive_type",
        "comms_return_char",
        "comms_ansi",
        "on_open",
        "on_close",
        "ssh_config_file",
        "ssh_known_hosts_file",
        "transport",
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
        ("auth_private_key", f"{UNIT_TEST_DIR}_ssh_config", f"{UNIT_TEST_DIR}_ssh_config".encode()),
        ("auth_strict_key", False, False),
        ("timeout_socket", 100, 100),
        ("timeout_transport", 100, 100),
        ("timeout_ops", 100, 100),
        ("timeout_exit", False, False),
        ("keepalive", True, True),
        ("keepalive_interval", 100, 100),
        ("keepalive_type", "standard", "standard"),
        ("keepalive_pattern", "tacocat", "tacocat"),
        ("comms_prompt_pattern", "tacocat", "tacocat"),
        ("comms_return_char", "tacocat", "tacocat"),
        ("comms_ansi", True, True),
        ("on_open", print, print),
        ("on_close", print, print),
        ("transport", "ssh2", "ssh2"),
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
        "auth_strict_key",
        "timeout_socket",
        "timeout_transport",
        "timeout_ops",
        "timeout_exit",
        "keepalive",
        "keepalive_interval",
        "keepalive_type",
        "keepalive_pattern",
        "comms_prompt_pattern",
        "comms_return_char",
        "comms_ansi",
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


def test_valid_private_key_file():
    auth_private_key = f"{UNIT_TEST_DIR}_ssh_private_key"
    conn = Scrape(host="myhost", auth_private_key=auth_private_key)
    assert (
        conn._initialization_args["auth_private_key"] == f"{UNIT_TEST_DIR}_ssh_private_key".encode()
    )


@pytest.mark.parametrize(
    "ssh_file",
    [
        ("ssh_config_file", True, "/etc/ssh/ssh_config", f"{UNIT_TEST_DIR}_ssh_config"),
        (
            "ssh_config_file",
            True,
            f"{os.path.expanduser('~')}/.ssh/config",
            f"{UNIT_TEST_DIR}_ssh_config",
        ),
        (
            "ssh_config_file",
            f"{UNIT_TEST_DIR}_ssh_known_hosts",
            f"{UNIT_TEST_DIR}_ssh_known_hosts",
            f"{UNIT_TEST_DIR}_ssh_config",
        ),
        (
            "ssh_known_hosts_file",
            True,
            "/etc/ssh/ssh_known_hosts",
            f"{UNIT_TEST_DIR}_ssh_known_hosts",
        ),
        (
            "ssh_known_hosts_file",
            True,
            f"{os.path.expanduser('~')}/.ssh/known_hosts",
            f"{UNIT_TEST_DIR}_ssh_known_hosts",
        ),
        (
            "ssh_known_hosts_file",
            f"{UNIT_TEST_DIR}_ssh_known_hosts",
            f"{UNIT_TEST_DIR}_ssh_known_hosts",
            f"{UNIT_TEST_DIR}_ssh_known_hosts",
        ),
    ],
    ids=[
        "config_file_etc",
        "config_file_user",
        "config_file_manual",
        "known_hosts_file_etc",
        "known_hosts_file_user",
        "known_hosts_file_manual",
    ],
)
def test_ssh_files(fs, ssh_file):
    attr_name = ssh_file[0]
    attr_value = ssh_file[1]
    attr_expected = ssh_file[2]
    attr_src = ssh_file[3]
    args = {attr_name: attr_value}

    fs.add_real_file(source_path=attr_src, target_path=attr_expected)

    conn = Scrape(host="myhost", **args)
    assert conn._initialization_args[attr_name] == attr_expected


def test_isalive(mocked_channel):
    # mocked channel always returns true so this is not a great test
    conn = mocked_channel([])
    conn.open()
    assert conn.isalive() is True
