from scrapli.transport import SSH2Transport


def test_creation():
    conn = SSH2Transport("localhost")
    assert conn.host == "localhost"
    assert conn.port == 22
