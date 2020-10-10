"""scrapli network ssh client library"""
import logging
from logging import getLogger
from typing import Optional, Tuple

from scrapli.driver import AsyncScrape, Scrape
from scrapli.factory import AsyncScrapli, Scrapli

__version__ = "2020.10.10"
__all__ = ("AsyncScrape", "Scrape", "AsyncScrapli", "Scrapli")


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


SCRAPLI_LOG = getLogger("scrapli")
SCRAPLI_LOG.addFilter(DuplicateFilter())
