"""scrapli.transport.base_transport"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict

from scrapli.logging import get_instance_logger


@dataclass()
class BaseTransportArgs:
    transport_options: Dict[str, Any]
    host: str
    port: int = 22
    timeout_socket: float = 10.0
    timeout_transport: float = 30.0
    logging_uid: str = ""


@dataclass()
class BasePluginTransportArgs:
    pass


class BaseTransport(ABC):
    def __init__(self, base_transport_args: BaseTransportArgs) -> None:
        self._base_transport_args = base_transport_args

        self.logger = get_instance_logger(
            instance_name="scrapli.transport",
            host=self._base_transport_args.host,
            port=self._base_transport_args.port,
            uid=self._base_transport_args.logging_uid,
        )

    @abstractmethod
    def close(self) -> None:
        """
        Close the transport session

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """

    @abstractmethod
    def write(self, channel_input: bytes) -> None:
        """
        Write bytes into the transport session

        Args:
            channel_input: bytes to write to transport session

        Returns:
            None

        Raises:
            N/A

        """

    @abstractmethod
    def isalive(self) -> bool:
        """
        Check if transport is alive

        Args:
            N/A

        Returns:
            bool: True/False if transport is alive

        Raises:
            N/A

        """

    def _pre_open_closing_log(self, closing: bool = False) -> None:
        """
        Emit "pre open" log message for consistency between transports

        Args:
            closing: bool indicating if message is for closing not opening

        Returns:
            None

        Raises:
            N/A

        """
        operation = "closing" if closing else "opening"

        self.logger.debug(
            f"{operation} transport connection to '{self._base_transport_args.host}' on port "
            f"'{self._base_transport_args.port}'"
        )

    def _post_open_closing_log(self, closing: bool = False) -> None:
        """
        Emit "post open" log message for consistency between transports

        Args:
            closing: bool indicating if message is for closing not opening

        Returns:
            None

        Raises:
            N/A

        """
        operation = "closed" if closing else "opened"

        self.logger.debug(
            f"transport connection to '{self._base_transport_args.host}' on port "
            f"'{self._base_transport_args.port}' {operation} successfully"
        )
