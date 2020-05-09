import sys

import pytest

from scrapli.transport import SystemSSHTransport


def test_str():
    conn = SystemSSHTransport("localhost")
    assert str(conn) == "Transport Object for host localhost"


def test_repr():
    conn = SystemSSHTransport("localhost")
    assert (
        repr(conn)
        == "Transport {'host': 'localhost', 'port': 22, 'timeout_socket': 5, 'timeout_transport': 5, "
        "'timeout_exit': True, 'keepalive': False, 'keepalive_interval': 30, 'keepalive_type': '', "
        "'keepalive_pattern': '\\x05', 'session_lock': False, "
        "'auth_username': '', 'auth_private_key': '', 'auth_password': '********', "
        "'auth_strict_key': True, 'auth_bypass': False, '_timeout_ops': 10, '_comms_prompt_pattern': "
        "'^[a-z0-9.\\\\-@()/:]{1,32}[#>$]$', '_comms_return_char': '\\n', '_comms_ansi': False, "
        "'ssh_config_file': '', 'ssh_known_hosts_file': '', 'lib_auth_exception': <class "
        "'scrapli.exceptions.ScrapliAuthenticationFailed'>, '_isauthenticated': False, "
        "'transport_options': {}, 'open_cmd': ['ssh', 'localhost', '-p', '22', '-o', "
        "'ConnectTimeout=5', '-o', 'ServerAliveInterval=5', '-o', 'StrictHostKeyChecking=yes', '-F', "
        "'/dev/null'], '_stdin_fd': -1, '_stdout_fd': -1}"
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
    [["oKexAlgorithms=+diffie-hellman-group1-sha1"], "oKexAlgorithms=+diffie-hellman-group1-sha1",],
    ids=["user options list", "user options string",],
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
        (b"Host key verification failed", "Host key verification failed for host localhost",),
        (b"Operation timed out", "Timed out connecting to host localhost",),
        (b"Connection timed out", "Timed out connecting to host localhost",),
        (b"No route to host", "No route to host localhost",),
        (b"no matching cipher found", "No matching cipher found for host localhost",),
        (
            b"no matching cipher found, their offer: aes128-cbc,aes256-cbc",
            "No matching cipher found for host localhost, their offer: aes128-cbc,aes256-cbc",
        ),
        (
            b"blah blah blah",
            "Failed to open connection to host localhost. Do you need to disable `auth_strict_key`?",
        ),
    ],
    ids=[
        "host key verification",
        "operation time out",
        "connection time out",
        "no route to host",
        "no matching cipher",
        "no matching cipher found ciphers",
        "unknown reason",
    ],
)
def test_pty_authentication_error_messages(eof_msg):
    conn = SystemSSHTransport("localhost")
    error_msg = eof_msg[0]
    expected_msg = eof_msg[1]
    actual_msg = conn._pty_authentication_eof_handler(error_msg)
    assert actual_msg == expected_msg


@pytest.mark.skipif(sys.platform.startswith("win"), reason="systemssh not supported on windows")
def test_set_timeout():
    conn = SystemSSHTransport("localhost")
    assert conn.timeout_transport == 5
    conn.set_timeout(1000)
    assert conn.timeout_transport == 1000
    conn.timeout_transport = 9999
    conn.set_timeout()
    assert conn.timeout_transport == 9999
