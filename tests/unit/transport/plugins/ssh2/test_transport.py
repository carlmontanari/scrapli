import pytest

from scrapli.exceptions import ScrapliConnectionNotOpened


def test_open_channel_no_session(ssh2_transport):
    with pytest.raises(ScrapliConnectionNotOpened):
        assert ssh2_transport._open_channel()


def test_isalive_no_session(ssh2_transport):
    assert ssh2_transport.isalive() is False


def test_write_exception(ssh2_transport):
    with pytest.raises(ScrapliConnectionNotOpened):
        ssh2_transport.write("blah")
