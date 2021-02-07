import pytest

from scrapli.exceptions import ScrapliConnectionNotOpened


def test_connection_not_opened_message():
    with pytest.raises(ScrapliConnectionNotOpened) as exc:
        raise ScrapliConnectionNotOpened()
    assert "connection not opened, but attempting to call a method that requires an open" in str(
        exc.value
    )
