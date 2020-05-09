import pytest

from scrapli.exceptions import ScrapliAuthenticationFailed
from scrapli.transport import TelnetTransport
from scrapli.transport.telnet import ScrapliTelnet


def test_scrapli_telnet_type():
    # connection error will get raised because 23 shouldnt be open for most devices running the test
    with pytest.raises(ConnectionError):
        conn = ScrapliTelnet("localhost", 23, 100)
        assert conn.host == "localhost"
        assert conn.port == 23
        assert conn.timeout == 100


def test_creation():
    conn = TelnetTransport("localhost")
    assert conn.host == "localhost"
    assert conn.port == 23
    assert conn._isauthenticated is False


def test_open_failure():
    conn = TelnetTransport("localhost", port=23)
    with pytest.raises(ScrapliAuthenticationFailed) as exc:
        conn.open()
    assert str(exc.value) == "Failed to open telnet session to host localhost, connection refused"


def test_keepalive_standard():
    conn = TelnetTransport("localhost")
    with pytest.raises(NotImplementedError) as exc:
        conn._keepalive_standard()
    assert str(exc.value) == "No 'standard' keepalive mechanism for telnet."
