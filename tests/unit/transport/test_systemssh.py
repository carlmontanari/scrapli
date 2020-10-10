import os
import sys
from pathlib import Path

import pytest

import scrapli
from scrapli.exceptions import ConnectionNotOpened, ScrapliAuthenticationFailed
from scrapli.transport import SystemSSHTransport

TEST_DATA_DIR = f"{Path(scrapli.__file__).parents[1]}/tests/test_data"


def test_str():
    conn = SystemSSHTransport("localhost")
    assert str(conn) == "Transport Object for host localhost"


def test_repr():
    conn = SystemSSHTransport("localhost")
    assert (
        repr(conn)
        == "Transport {'logger': 'scrapli.transport-localhost', 'host': 'localhost', 'port': 22, 'timeout_socket': 5, "
        "'timeout_transport': 5, 'timeout_exit': True, 'auth_username': '', "
        "'auth_private_key': '', 'auth_private_key_passphrase': '********', 'auth_password': '********', "
        "'auth_strict_key': True, 'auth_bypass': False, '_timeout_ops': 10, '_comms_prompt_pattern': '^["
        "a-z0-9.\\\\-@()/:]{1,32}[#>$]$', '_comms_return_char': '\\n', '_comms_ansi': False, 'ssh_config_file': "
        "'', 'ssh_known_hosts_file': '', 'lib_auth_exception': <class "
        "'scrapli.exceptions.ScrapliAuthenticationFailed'>, '_isauthenticated': False, 'transport_options': {}, "
        "'open_cmd': ['ssh', 'localhost', '-p', '22', '-o', 'ConnectTimeout=5', '-o', 'ServerAliveInterval=5', "
        "'-o', 'StrictHostKeyChecking=yes', '-F', '/dev/null']}"
    )


@pytest.mark.skipif(sys.platform.startswith("win"), reason="systemssh not supported on windows")
def test_creation():
    conn = SystemSSHTransport("localhost")
    assert conn.host == "localhost"
    assert conn.port == 22
    assert conn._isauthenticated is False


@pytest.mark.skipif(sys.platform.startswith("win"), reason="systemssh not supported on windows")
def test_build_open_cmd():
    conn = SystemSSHTransport("localhost")
    assert conn.open_cmd == [
        "ssh",
        "localhost",
        "-p",
        "22",
        "-o",
        "ConnectTimeout=5",
        "-o",
        "ServerAliveInterval=5",
        "-o",
        "StrictHostKeyChecking=yes",
        "-F",
        "/dev/null",
    ]


@pytest.mark.skipif(sys.platform.startswith("win"), reason="systemssh not supported on windows")
@pytest.mark.parametrize(
    "user_options",
    [
        ["oKexAlgorithms=+diffie-hellman-group1-sha1"],
        "oKexAlgorithms=+diffie-hellman-group1-sha1",
    ],
    ids=[
        "user options list",
        "user options string",
    ],
)
def test_build_open_cmd_user_options(user_options):
    conn = SystemSSHTransport("localhost", transport_options={"open_cmd": user_options})
    assert conn.open_cmd == [
        "ssh",
        "localhost",
        "-p",
        "22",
        "-o",
        "ConnectTimeout=5",
        "-o",
        "ServerAliveInterval=5",
        "-o",
        "StrictHostKeyChecking=yes",
        "-F",
        "/dev/null",
        "oKexAlgorithms=+diffie-hellman-group1-sha1",
    ]


@pytest.mark.skipif(sys.platform.startswith("win"), reason="systemssh not supported on windows")
@pytest.mark.parametrize(
    "eof_msg",
    [
        (
            b"Host key verification failed",
            "Host key verification failed for host localhost",
        ),
        (
            b"Operation timed out",
            "Timed out connecting to host localhost",
        ),
        (
            b"Connection timed out",
            "Timed out connecting to host localhost",
        ),
        (
            b"No route to host",
            "No route to host localhost",
        ),
        (
            b"no matching key exchange found.",
            "No matching key exchange found for host localhost",
        ),
        (
            b"no matching key exchange found. Their offer: diffie-hellman-group-exchange-sha1,diffie-hellman-group14-sha1",
            "No matching key exchange found for host localhost, their offer: diffie-hellman-group-exchange-sha1,diffie-hellman-group14-sha1",
        ),
        (
            b"no matching cipher found",
            "No matching cipher found for host localhost",
        ),
        (
            b"no matching cipher found, their offer: aes128-cbc,aes256-cbc",
            "No matching cipher found for host localhost, their offer: aes128-cbc,aes256-cbc",
        ),
        (
            b"command-line: line 0: Bad configuration option: ciphers+",
            "Bad SSH configuration option(s) for host localhost, bad option(s): ciphers+",
        ),
        (
            b"WARNING: UNPROTECTED PRIVATE KEY FILE!",
            # note: empty quotes in the middle is where private key filename would be
            "Permissions for private key `` are too open, authentication failed!",
        ),
        (
            b"Could not resolve hostname BLAH: No address associated with hostname",
            # note: empty quotes in the middle is where private key filename would be
            "Could not resolve address for host `localhost`",
        ),
    ],
    ids=[
        "host key verification",
        "operation time out",
        "connection time out",
        "no route to host",
        "no matching key exchange",
        "no matching key exchange found key exchange",
        "no matching cipher",
        "no matching cipher found ciphers",
        "bad configuration option",
        "unprotected key",
        "could not resolve host",
    ],
)
def test_ssh_message_handler(eof_msg):
    conn = SystemSSHTransport("localhost")
    error_msg = eof_msg[0]
    expected_msg = eof_msg[1]
    with pytest.raises(ScrapliAuthenticationFailed) as exc:
        conn._ssh_message_handler(error_msg)
    assert str(exc.value) == expected_msg


@pytest.mark.skipif(sys.platform.startswith("win"), reason="systemssh not supported on windows")
def test_set_timeout():
    conn = SystemSSHTransport("localhost")
    assert conn.timeout_transport == 5
    conn.set_timeout(1000)
    assert conn.timeout_transport == 1000
    conn.timeout_transport = 9999


@pytest.mark.skipif(sys.platform.startswith("win"), reason="systemssh not supported on windows")
@pytest.mark.parametrize(
    "method_name",
    ["read", "write"],
    ids=["read", "write"],
)
def test_requires_open(method_name):
    conn = SystemSSHTransport("localhost")
    method = getattr(conn, method_name)
    with pytest.raises(ConnectionNotOpened):
        if method_name == "write":
            method("blah")
        else:
            method()
