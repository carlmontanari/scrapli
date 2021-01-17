"""scrapli.driver.generic"""
from scrapli.driver.generic.async_driver import AsyncGenericDriver
from scrapli.driver.generic.sync_driver import GenericDriver

__all__ = (
    "AsyncGenericDriver",
    "GenericDriver",
)
