"""scrapli.transport.async_transport"""
from abc import ABC, abstractmethod

from scrapli.transport.base_transport import TransportBase


class AsyncTransport(TransportBase, ABC):
    @abstractmethod
    async def open(self) -> None:  # pylint: disable=W0236
        """
        Async open channel, acquire pty, request interactive shell

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """

    @abstractmethod
    async def read(self) -> bytes:  # pylint: disable=W0236
        """
        Async read data from the channel

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """

    @abstractmethod
    def write(self, channel_input: str) -> None:
        """
        Write data to the channel

        Args:
            channel_input: string to send to channel

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
