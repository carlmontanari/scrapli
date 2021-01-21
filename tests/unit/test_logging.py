import logging
import re
from pathlib import Path

from scrapli.logging import (
    ScrapliFileHandler,
    ScrapliFormatter,
    ScrapliLogRecord,
    enable_basic_logging,
    logger,
)


def test_scrapli_formatter():
    formatter = ScrapliFormatter(log_header=True, caller_info=True)
    record = ScrapliLogRecord(
        name="test_log",
        level=20,
        pathname="somepath",
        lineno=999,
        msg="thisisalogmessage!",
        args=None,
        exc_info=None,
        func="coolfunc",
        message_id=1,
    )
    record.uid = "UID"
    record.host = "scrapli"
    record.port = "22"
    formatted_record = formatter.format(record=record)
    assert (
        re.sub(
            string=formatted_record,
            pattern=r"\d{4}-\d{2}\-\d{2} \d{2}:\d{2}:\d{2},\d{3}",
            repl="_TIMESTMAMP__TIMESTAMP_",
        )
        == "ID    | TIMESTAMP               | LEVEL    | (UID:)HOST:PORT           | MODULE               | FUNCNAME  "
        "           | LINE  | MESSAGE\n1     | _TIMESTMAMP__TIMESTAMP_ | INFO     | UID:scrapli:22            | "
        "somepath             | coolfunc             | 999   | thisisalogmessage!"
    )


def test_scrapli_filehandler():
    pass


def test_enable_basic_logging(fs):
    assert Path("scrapli.log").is_file() is False
    enable_basic_logging(file=True, level="debug")
    scrapli_logger = logging.getLogger("scrapli")

    assert scrapli_logger.level == 10
    assert isinstance(scrapli_logger.handlers[1], ScrapliFileHandler)
    assert isinstance(scrapli_logger.handlers[1].formatter, ScrapliFormatter)
    assert scrapli_logger.propagate is False

    assert Path("scrapli.log").is_file() is True

    # reset the main logger to propagate and delete the file handler so caplog works!
    logger.propagate = True
    del logger.handlers[1]


def test_enable_basic_logging_no_buffer(fs):
    assert Path("mylog.log").is_file() is False

    enable_basic_logging(file="mylog.log", level="debug", buffer_log=False, caller_info=True)
    scrapli_logger = logging.getLogger("scrapli")

    assert scrapli_logger.level == 10
    assert isinstance(scrapli_logger.handlers[1], logging.FileHandler)
    assert isinstance(scrapli_logger.handlers[1].formatter, ScrapliFormatter)
    assert scrapli_logger.propagate is False

    assert Path("mylog.log").is_file() is True

    # reset the main logger to propagate and delete the file handler so caplog works!
    logger.propagate = True
    del logger.handlers[1]
