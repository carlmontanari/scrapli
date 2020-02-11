from scrapli.transport import MikoTransport


def test_creation():
    conn = MikoTransport("localhost")
    assert conn.host == "localhost"
    assert conn.port == 22
