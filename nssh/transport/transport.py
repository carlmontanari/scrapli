"""nssh.transport.transport"""
from abc import ABC, abstractmethod
from threading import Lock
from typing import Dict, Optional, Union


class Transport(ABC):
    @abstractmethod
    def __init__(self, *args: Union[str, int], **kwargs: Dict[str, Union[str, int]]) -> None:
        self.host: str = ""
        self.session_lock: Lock = Lock()

    def __bool__(self) -> bool:
        """
        Magic bool method for Socket

        Args:
            N/A  # noqa

        Returns:
            bool: True/False if socket is alive or not

        Raises:
            N/A  # noqa

        """
        return self.isalive()

    def __str__(self) -> str:
        """
        Magic str method for Transport

        Args:
            N/A  # noqa

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa

        """
        return f"Transport Object for host {self.host}"

    def __repr__(self) -> str:
        """
        Magic repr method for Transport

        Args:
            N/A  # noqa

        Returns:
            repr: repr for class object

        Raises:
            N/A  # noqa

        """
        class_dict = self.__dict__.copy()
        class_dict["auth_password"] = "********"
        return f"Transport {class_dict}"

    @abstractmethod
    def open(self) -> None:
        """
        Open channel, acquire pty, request interactive shell

        Args:
            N/A  # noqa

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa

        """

    @abstractmethod
    def close(self) -> None:
        """
        Close session and socket

        Args:
            N/A  # noqa

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa

        """

    @abstractmethod
    def isalive(self) -> bool:
        """
        Check if socket is alive and session is authenticated

        Args:
            N/A  # noqa

        Returns:
            bool: True if socket is alive and session authenticated, else False

        Raises:
            N/A  # noqa

        """

    @abstractmethod
    def read(self) -> bytes:
        """
        Read data from the channel

        Args:
            N/A  # noqa

        Returns:
            output: bytes output as read from channel

        Raises:
            N/A  # noqa

        """

    @abstractmethod
    def write(self, channel_input: str) -> None:
        """
        Write data to the channel

        Args:
            channel_input: string to send to channel

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa

        """

    @abstractmethod
    def flush(self) -> None:
        """
        Flush channel stdout stream

        Args:
            N/A  # noqa

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa

        """

    @abstractmethod
    def set_timeout(self, timeout: Optional[int] = None) -> None:
        """
        Set session timeout

        Args:
            timeout: timeout in seconds

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa

        """

    @abstractmethod
    def set_blocking(self, blocking: bool = False) -> None:
        """
        Set session blocking configuration

        Args:
            blocking: True/False set session to blocking

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa

        """
