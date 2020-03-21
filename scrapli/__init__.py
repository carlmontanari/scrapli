"""scrapli network ssh client library"""
import logging
from logging import NullHandler
from typing import Optional, Tuple

from scrapli.driver import Scrape

__version__ = "2020.03.21"
__all__ = ("Scrape",)


class DuplicateFilter(logging.Filter):
    def __init__(self) -> None:
        """
        Remove duplicates from log

        Thank you to our lord and savior, StackOverflow... src:
        https://stackoverflow.com/questions/44691558/suppress-multiple-messages-with-same-content- \
        in-python-logging-module-aka-log-co

        """
        super().__init__()
        self.last_log: Optional[Tuple[str, int, str]] = None

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter duplicate entries in logs

        Fields to compare to previous log entry if these fields match; skip log entry

        Args:
            record: log record to check

        Returns:
            bool: filter or not

        Raises:
            N/A  # noqa

        """
        current_log = (record.module, record.levelno, record.msg)
        if current_log != getattr(self, "last_log", None):
            self.last_log = current_log
            return True
        return False


# Setup channel logger
TRANSPORT_LOG = logging.getLogger("channel")
# Add duplicate filter to channel log
TRANSPORT_LOG.addFilter(DuplicateFilter())
logging.getLogger("channel").addHandler(NullHandler())
