import sys

import pytest

from scrapli.transport import SSH2Transport


@pytest.mark.skipif(
    (sys.platform.startswith("win") and sys.version_info > (3, 7)),
    reason="ssh2 on pypi not built for python3.8 on windows",
)
def test_creation():
    conn = SSH2Transport("localhost")
    assert conn.host == "localhost"
    assert conn.port == 22
