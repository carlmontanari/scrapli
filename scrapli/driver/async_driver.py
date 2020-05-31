"""scrapli.driver.async_driver"""
from types import TracebackType
from typing import Any, Optional, Type

from scrapli.channel import AsyncChannel
from scrapli.driver.base_driver import ScrapeBase


class AsyncScrape(ScrapeBase):
    def __init__(self, **kwargs: Any) -> None:
        """
        AsyncScrape Object

        AsyncScrape is the base class for AsyncNetworkDriver, and subsequent async platform specific
        drivers (i.e. AsyncIOSXEDriver). AsyncScrape can be used on its own and offers a
        semi-pexpect like experience in that it doesn't know or care about privilege levels,
        platform types, and things like that.

        *Note* most arguments passed to Scrape do not actually get assigned to the scrape object
        itself, but instead are used to construct the Transport and Channel classes that Scrape
        relies on, see Transport and Channel docs for details.

        Args:
            kwargs: Keyword arguments to pass to `ScrapeBase` -- see `ScrapeBase` for available args

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        super().__init__(**kwargs)
        self.channel = AsyncChannel(transport=self.transport, **self.channel_args)

    async def __aenter__(self) -> "AsyncScrape":
        """
        Enter method for context manager

        Args:
            N/A

        Returns:
            self: instance of self

        Raises:
            N/A

        """
        await self.open()
        return self

    async def __aexit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """
        Exit method to cleanup for context manager

        Args:
            exception_type: exception type being raised
            exception_value: message from exception being raised
            traceback: traceback from exception being raised

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        await self.close()

    async def open(self) -> None:
        """
        Open Transport (socket/session) and establish channel

        If on_open callable provided, execute that callable after opening connection

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.logger.info(f"Opening connection to {self._initialization_args['host']}")
        await self.transport.open()
        if self.on_open:
            await self.on_open(self)
        self.logger.info(f"Connection to {self._initialization_args['host']} opened successfully")

    async def close(self) -> None:
        """
        Close Transport (socket/session)

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.logger.info(f"Closing connection to {self._initialization_args['host']}")
        if self.on_close:
            await self.on_close(self)
        self.transport.close()
        self.logger.info(f"Connection to {self._initialization_args['host']} closed successfully")
