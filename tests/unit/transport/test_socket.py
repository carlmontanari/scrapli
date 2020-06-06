import sys

import pytest

from scrapli.exceptions import ScrapliTimeout
from scrapli.transport.socket import Socket


@pytest.mark.skipif(sys.platform.startswith("win"), reason="not testing windows")
def test_socket_open_success():
    sock = Socket("localhost", 22, 1)
    sock.socket_open()
    assert sock.socket_isalive() is True


@pytest.mark.skipif(sys.platform.startswith("win"), reason="not testing windows")
def test_socket_open_failure_connection_refused():
    sock = Socket("localhost", 2222, 1)
    with pytest.raises(ConnectionRefusedError) as e:
        sock.socket_open()
    assert str(e.value) == "Connection refused trying to open socket to localhost on port 2222"


@pytest.mark.skipif(sys.platform.startswith("win"), reason="not testing windows")
def test_socket_open_failure_timeout():
    sock = Socket("240.0.0.1", 22, 0.1)
    with pytest.raises(ScrapliTimeout) as e:
        sock.socket_open()
    assert str(e.value) == "Timed out trying to open socket to 240.0.0.1 on port 22"


@pytest.mark.skipif(sys.platform.startswith("win"), reason="not testing windows")
def test_socket_close_success():
    sock = Socket("localhost", 22, 1)
    sock.socket_open()
    assert sock.socket_isalive() is True
    sock.socket_close()
    assert sock.socket_isalive() is False


def test_socket_isalive_false():
    sock = Socket("localhost", 22, 1)
    assert sock.socket_isalive() is False


def test__str():
    sock = Socket("localhost", 22, 1)
    assert str(sock) == "Socket Object for host localhost"


def test__repr():
    sock = Socket("localhost", 22, 1)
    assert (
        repr(sock)
        == "Socket {'logger': 'scrapli.socket-localhost', 'host': 'localhost', 'port': 22, 'timeout': "
        "1, 'sock': None}"
    )


def test__bool():
    sock = Socket("localhost", 22, 1)
    assert bool(sock) is False
