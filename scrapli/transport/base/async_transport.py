"""scrapli.transport.async_transport"""
from abc import ABC, abstractmethod

from scrapli.transport.base.base_transport import BaseTransport


class AsyncTransport(BaseTransport, ABC):
    @abstractmethod
    async def open(self) -> None:
        """
        Open the transport session

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """

    @abstractmethod
    async def read(self) -> bytes:
        """
        Read data from the transport session

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
