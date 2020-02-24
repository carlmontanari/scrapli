import os
from pathlib import Path

import pytest

import scrapli
from scrapli import Scrape
from scrapli.transport import MikoTransport, SSH2Transport, SystemSSHTransport

UNIT_TEST_DIR = f"{Path(scrapli.__file__).parents[1]}/tests/unit/"


def test__str():
    conn = Scrape(host="myhost")
    assert str(conn) == "Scrape Object for host myhost"


def test__repr():
    conn = Scrape(host="myhost", ssh_known_hosts_file=False)
    assert (
        repr(conn)
        == "Scrape {'host': 'myhost', 'port': 22, 'auth_username': '', 'auth_password': '********', "
        "'auth_strict_key': True, 'auth_public_key': b'', 'timeout_socket': 5, 'timeout_transport': 5, "
        "'timeout_ops': 10, 'keepalive': False, 'keepalive_interval': 30, 'keepalive_type': 'network', "
        "'keepalive_pattern': '\\x05', 'comms_prompt_pattern': '^[a-z0-9.\\\\-@()/:]{1,32}[#>$]$', "
        "'comms_return_char': '\\n', 'comms_ansi': False, 'ssh_config_file': '', 'ssh_known_hosts_file': '', "
        "'transport_class': <class 'scrapli.transport.systemssh.SystemSSHTransport'>, 'transport_args': {'host': "
        "'myhost', 'port': 22, 'timeout_socket': 5, 'timeout_transport': 5, 'timeout_ops': 10, 'keepalive': False, "
        "'keepalive_interval': 30, 'keepalive_type': 'network', 'keepalive_pattern': '\\x05', 'auth_username': '', "
        "'auth_public_key': b'', 'auth_password': '', 'auth_strict_key': True, 'comms_prompt_pattern': '^["
        "a-z0-9.\\\\-@()/:]{1,32}[#>$]$', 'comms_return_char': '\\n', 'ssh_config_file': ''}, 'channel_args': {"
        "'comms_prompt_pattern': '^[a-z0-9.\\\\-@()/:]{1,32}[#>$]$', 'comms_return_char': '\\n', 'comms_ansi': "
        "False, 'timeout_ops': 10}}"
    )


def test_host():
    conn = Scrape(host="myhost")
    assert conn.host == "myhost"


def test_host_strip():
    conn = Scrape(host=" whitespace ")
    assert conn.host == "whitespace"


def test_port():
    conn = Scrape(port=123)
    assert conn.port == 123


def test_port_invalid():
    with pytest.raises(TypeError) as e:
        Scrape(port="notint")
    assert str(e.value) == "port should be int, got <class 'str'>"


def test_user():
    conn = Scrape(auth_username="scrapli")
    assert conn.auth_username == "scrapli"


def test_user_strip():
    conn = Scrape(auth_username=" scrapli ")
    assert conn.auth_username == "scrapli"


def test_user_invalid():
    with pytest.raises(AttributeError):
        Scrape(auth_username=1234)


def test_system_driver():
    conn = Scrape()
    assert conn.transport_class == SystemSSHTransport


def test_ssh2_driver():
    conn = Scrape(transport="ssh2")
    assert conn.transport_class == SSH2Transport


def test_paramiko_driver():
    conn = Scrape(transport="paramiko")
    assert conn.transport_class == MikoTransport


def test_invalid_driver():
    with pytest.raises(ValueError) as e:
        Scrape(transport="notreal")
    assert str(e.value) == "transport should be one of ssh2|paramiko|system|telnet, got notreal"


def test_auth_ssh_key_strip():
    conn = Scrape(auth_public_key="~/some_neat_path ")
    user_path = os.path.expanduser("~/")
    assert conn.auth_public_key == f"{user_path}some_neat_path".encode()


def test_invalid_ssh_config_file():
    with pytest.raises(TypeError) as e:
        Scrape(ssh_config_file=1)
    assert str(e.value) == "`ssh_config_file` should be str or bool, got <class 'int'>"


def test_valid_ssh_config_file_path():
    conn = Scrape(ssh_config_file=f"{UNIT_TEST_DIR}_ssh_config")
    assert conn.ssh_config_file == f"{UNIT_TEST_DIR}_ssh_config"


def test_ssh_config_file_path_system_no_file(fs):
    conn = Scrape(ssh_config_file=True)
    assert conn.ssh_config_file == ""


def test_invalid_ssh_known_hosts():
    with pytest.raises(TypeError) as e:
        Scrape(ssh_known_hosts_file=1)
    assert str(e.value) == "`ssh_known_hosts_file` should be str or bool, got <class 'int'>"


def test_valid_ssh_known_hosts_path():
    conn = Scrape(ssh_known_hosts_file=f"{UNIT_TEST_DIR}_ssh_known_hosts")
    assert conn.ssh_known_hosts_file == f"{UNIT_TEST_DIR}_ssh_known_hosts"


def test_ssh_known_hosts_file_path_false(fs):
    conn = Scrape(ssh_known_hosts_file=False)
    assert conn.ssh_known_hosts_file == ""


def test_ssh_known_hosts_path_system_no_file(fs):
    conn = Scrape(ssh_known_hosts_file=True)
    assert conn.ssh_config_file == ""


def test_auth_password_strip():
    conn = Scrape(auth_password=" password ")
    assert conn.auth_password == "password"


def test_auth_strict_key_invalid():
    with pytest.raises(TypeError) as e:
        Scrape(auth_strict_key="notreal")
    assert str(e.value) == "auth_strict_key should be bool, got <class 'str'>"


def test_valid_comms_return_char():
    conn = Scrape(comms_return_char="\rn")
    assert conn.comms_return_char == "\rn"


def test_invalid_comms_return_char():
    with pytest.raises(TypeError) as e:
        Scrape(comms_return_char=False)
    assert str(e.value) == "comms_return_char should be str, got <class 'bool'>"


def test_valid_comms_ansi():
    conn = Scrape(comms_ansi=True)
    assert conn.comms_ansi is True


def test_invalid_comms_ansi():
    with pytest.raises(TypeError) as e:
        Scrape(comms_ansi=123)
    assert str(e.value) == "comms_ansi should be bool, got <class 'int'>"


def test_valid_comms_prompt_pattern():
    conn = Scrape(comms_prompt_pattern="somestr")
    assert conn.comms_prompt_pattern == "somestr"


def test_invalid_comms_prompt_pattern():
    with pytest.raises(TypeError):
        Scrape(comms_prompt_pattern=123)


def test_isalive(mocked_channel):
    # mocked channel always returns true so this is not a great test
    conn = mocked_channel([])
    conn.open()
    assert conn.isalive() is True
