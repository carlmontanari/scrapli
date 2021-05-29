import sys

import pytest

from scrapli.exceptions import ScrapliConnectionNotOpened


@pytest.mark.skipif(sys.version_info >= (3, 10), reason="skipping ssh2 on 3.10")
def test_open_channel_no_session(ssh2_transport):
    with pytest.raises(ScrapliConnectionNotOpened):
        assert ssh2_transport._open_channel()


@pytest.mark.skipif(sys.version_info >= (3, 10), reason="skipping ssh2 on 3.10")
def test_isalive_no_session(ssh2_transport):
    assert ssh2_transport.isalive() is False


@pytest.mark.skipif(sys.version_info >= (3, 10), reason="skipping ssh2 on 3.10")
def test_write_exception(ssh2_transport):
    with pytest.raises(ScrapliConnectionNotOpened):
        ssh2_transport.write("blah")
