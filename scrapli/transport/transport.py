"""scrapli.transport.transport"""
from abc import ABC, abstractmethod
from select import select

from scrapli.transport.base_transport import TransportBase


class Transport(TransportBase, ABC):
    @abstractmethod
    def open(self) -> None:
        """
        Open channel, acquire pty, request interactive shell

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """

    @abstractmethod
    def read(self) -> bytes:
        """
        Read data from the channel

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

    def _wait_for_session_fd_ready(self, fd: int) -> None:
        """
        Wait for a session fd to be ready to read

        Only applicable for "core" transports system/telnet

        Args:
            fd: fd id to check on

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        while True:
            fd_ready, _, _ = select([fd], [], [], 0)
            if fd in fd_ready:
                break
            self.logger.debug("Session fd not ready yet...")
