import pytest

from nssh.exceptions import NSSHTimeout
from nssh.transport.socket import Socket


def test_socket_open_success():
    sock = Socket("localhost", 22, 1)
    sock.socket_open()
    assert sock.socket_isalive() is True


def test_socket_open_failure_connection_refused():
    sock = Socket("localhost", 2222, 1)
    with pytest.raises(ConnectionRefusedError) as e:
        sock.socket_open()
    assert str(e.value) == "Connection refused trying to open socket to localhost on port 2222"


def test_socket_open_failure_timeout():
    sock = Socket("240.0.0.1", 22, 0.1)
    with pytest.raises(NSSHTimeout) as e:
        sock.socket_open()
    assert str(e.value) == "Timed out trying to open socket to 240.0.0.1 on port 22"


def test_socket_close_success():
    sock = Socket("localhost", 22, 1)
    sock.socket_open()
    assert sock.socket_isalive() is True
    sock.socket_close()
    assert sock.socket_isalive() is False


def test_socket_isalive_false():
    sock = Socket("localhost", 22, 1)
    assert sock.socket_isalive() is False
