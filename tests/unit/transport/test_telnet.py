from scrapli.transport import TelnetTransport


def test_creation():
    conn = TelnetTransport("localhost")
    assert conn.host == "localhost"
    assert conn.port == 23
    assert conn._isauthenticated is False
