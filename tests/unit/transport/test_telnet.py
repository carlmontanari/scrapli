import sys

import pytest

from scrapli.exceptions import ConnectionNotOpened
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


@pytest.mark.skipif(sys.platform.startswith("win"), reason="skipping on windows")
def test_open_failure():
    conn = TelnetTransport("localhost", port=23)
    with pytest.raises(ConnectionNotOpened) as exc:
        conn.open()
    assert str(exc.value) == "Failed to open telnet session to host localhost, connection refused"


@pytest.mark.parametrize(
    "method_name",
    ["read", "write", "set_timeout"],
    ids=["read", "write", "set_timeout"],
)
def test_requires_open(method_name):
    conn = TelnetTransport("localhost")
    method = getattr(conn, method_name)
    with pytest.raises(ConnectionNotOpened):
        if method_name == "read":
            method()
        else:
            method("blah")
