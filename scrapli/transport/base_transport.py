"""scrapli.transport.base_transport"""
from abc import ABC, abstractmethod
from logging import getLogger

from scrapli.helper import attach_duplicate_log_filter


class TransportBase(ABC):
    def __init__(
        self,
        host: str = "",
        port: int = 22,
        timeout_socket: int = 5,
        timeout_transport: int = 5,
        timeout_exit: bool = True,
    ) -> None:
        r"""
        Transport Base Object

        Args:
            host: host ip/name to connect to
            port: port to connect to
            timeout_socket: timeout for establishing socket in seconds
            timeout_transport: timeout for ssh|telnet transport in seconds
            timeout_exit: True/False close transport if timeout encountered. If False and keepalives
                are in use, keepalives will prevent program from exiting so you should be sure to
                catch Timeout exceptions and handle them appropriately

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.logger = getLogger(f"scrapli.transport-{host}")
        attach_duplicate_log_filter(logger=self.logger)

        self.host: str = host
        self.port: int = port
        self.timeout_socket: int = timeout_socket
        self.timeout_transport: int = timeout_transport
        self.timeout_exit: bool = timeout_exit

    def __bool__(self) -> bool:
        """
        Magic bool method for Socket

        Args:
            N/A

        Returns:
            bool: True/False if socket is alive or not

        Raises:
            N/A

        """
        return self.isalive()

    def __str__(self) -> str:
        """
        Magic str method for Transport

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        return f"Transport Object for host {self.host}"

    def __repr__(self) -> str:
        """
        Magic repr method for Transport

        Args:
            N/A

        Returns:
            str: repr for class object

        Raises:
            N/A

        """
        class_dict = self.__dict__.copy()
        if "auth_password" in class_dict.keys():
            class_dict["auth_password"] = "********"
        if "auth_private_key_passphrase" in class_dict.keys():
            class_dict["auth_private_key_passphrase"] = "********"
        class_dict["logger"] = self.logger.name
        return f"Transport {class_dict}"

    @abstractmethod
    def close(self) -> None:
        """
        Close session and socket

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """

    @abstractmethod
    def isalive(self) -> bool:
        """
        Check if socket is alive and session is authenticated

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """

    @abstractmethod
    def set_timeout(self, timeout: int) -> None:
        """
        Set session timeout

        Args:
            timeout: timeout in seconds

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
