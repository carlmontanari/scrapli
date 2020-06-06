import logging
from logging import LogRecord


def test_duplicate_filter():
    logger = logging.getLogger("scrapli")
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
