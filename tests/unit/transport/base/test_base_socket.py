import pytest

from scrapli.exceptions import ScrapliConnectionNotOpened


def test_socket_open_close_isalive(socket_transport):
    """Test socket initialization/opening"""
    assert socket_transport.host == "localhost"
    assert socket_transport.port == 22
    assert socket_transport.timeout == 10.0

    socket_transport.open()

    assert socket_transport.isalive() is True

    socket_transport.close()

    assert socket_transport.isalive() is False


def test_socket_open_cant_determine_address_family(socket_transport):
    """Test socket initialization/opening with failure to determine address family"""

    # should not be able to figure out address family for "Ž" character because...
    # what would that possibly be? :D
    socket_transport.host = "Ž"
    socket_transport.port = -1
    socket_transport.timeout = 0.1

    with pytest.raises(ScrapliConnectionNotOpened) as exc:
        socket_transport.open()

    assert "failed to determine socket address family" in str(exc.value)


def test_socket_open_connection_not_opened(socket_transport):
    """Test socket initialization/opening with failure to open connection (timeout)"""

    # 2222 should *probably* not be listening/open on the localhost
    socket_transport.host = "localhost"
    socket_transport.port = 2222
    socket_transport.timeout = 0.1

    with pytest.raises(ScrapliConnectionNotOpened) as exc:
        socket_transport.open()

    assert "connection refused" in str(exc.value)


def test_socket_open_connection_refused(socket_transport):
    """Test socket initialization/opening with failure to open connection (refused)"""

    # google public dns wont let us connect but it will resolve
    socket_transport.host = "8.8.8.8"
    socket_transport.port = 2222
    socket_transport.timeout = 0.1

    with pytest.raises(ScrapliConnectionNotOpened) as exc:
        socket_transport.open()

    assert "timed out" in str(exc.value)


def test_socket_bool(socket_transport):
    """Test socket magic bool method"""
    assert bool(socket_transport) is False
    socket_transport.open()
    assert bool(socket_transport) is True
