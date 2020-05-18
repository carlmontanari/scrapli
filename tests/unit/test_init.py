from logging import LogRecord

from scrapli.__init__ import DuplicateFilter


def test_duplicate_filter():
    logger = DuplicateFilter()
    log_entry = LogRecord(
        name="scrapli_test",
        level="DEBUG",
        pathname="somepath",
        lineno=123,
        args=None,
        exc_info=(),
        msg="Fake as heck",
    )
    logger.last_log = log_entry
    assert logger.filter(record=log_entry) is True
    assert logger.filter(record=log_entry) is False
