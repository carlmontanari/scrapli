"""scrapli.driver.generic"""

from scrapli.driver.generic.async_driver import AsyncGenericDriver
from scrapli.driver.generic.base_driver import ReadCallback
from scrapli.driver.generic.sync_driver import GenericDriver

__all__ = (
    "ReadCallback",
    "AsyncGenericDriver",
    "GenericDriver",
)
