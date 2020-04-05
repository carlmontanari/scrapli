import sys

import pytest

from scrapli.transport import SystemSSHTransport


@pytest.mark.skipif(sys.platform.startswith("win"), reason="systemssh not supported on windows")
def test_creation():
    conn = SystemSSHTransport("localhost")
    assert conn.host == "localhost"
    assert conn.port == 22
    assert conn._isauthenticated is False
