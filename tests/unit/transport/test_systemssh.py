from scrapli.transport import SystemSSHTransport


def test_creation():
    conn = SystemSSHTransport("localhost")
    assert conn.host == "localhost"
    assert conn.port == 22
    assert conn._isauthenticated is False
