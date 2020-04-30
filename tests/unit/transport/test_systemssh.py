import sys

import pytest

from scrapli.transport import SystemSSHTransport


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
def test_build_open_cmd_user_options():
    conn = SystemSSHTransport(
        "localhost", transport_options={"open_cmd": ["oKexAlgorithms=+diffie-hellman-group1-sha1"]}
    )
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
