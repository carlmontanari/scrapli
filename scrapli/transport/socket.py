"""scrapli.transport.socket"""
import socket
from logging import getLogger
from typing import Optional

from scrapli.exceptions import ScrapliTimeout


class Socket:
    def __init__(self, host: str, port: int, timeout: int):
        """
        Socket object

        Args:
            host: host to connect to
            port: port to connect to
            timeout: timeout in seconds

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.logger = getLogger(f"scrapli.socket-{host}")
        self.host: str = host
        self.port: int = port
        self.timeout: int = timeout
        self.sock: Optional[socket.socket] = None

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
        return self.socket_isalive()

    def __str__(self) -> str:
        """
        Magic str method for Socket

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        return f"Socket Object for host {self.host}"

    def __repr__(self) -> str:
        """
        Magic repr method for Socket

        Args:
            N/A

        Returns:
            str: repr for class object

        Raises:
            N/A

        """
        class_dict = self.__dict__.copy()
        class_dict["logger"] = self.logger.name
        return f"Socket {class_dict}"

    def socket_open(self) -> None:
        """
        Open underlying socket

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            ConnectionRefusedError: if socket refuses connection
            ScrapliTimeout: if socket connection times out

        """
        if not self.socket_isalive():
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)
            try:
                self.sock.connect((self.host, self.port))
            except ConnectionRefusedError as exc:
                self.logger.critical(
                    f"Connection refused trying to open socket to {self.host} on port {self.port}"
                )
                raise ConnectionRefusedError(
                    f"Connection refused trying to open socket to {self.host} on port {self.port}"
                ) from exc
            except socket.timeout as exc:
                self.logger.critical(
                    f"Timed out trying to open socket to {self.host} on port {self.port}"
                )
                raise ScrapliTimeout(
                    f"Timed out trying to open socket to {self.host} on port {self.port}"
                ) from exc
            self.logger.debug(f"Socket to host {self.host} opened")

    def socket_close(self) -> None:
        """
        Close socket

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        if self.socket_isalive() and isinstance(self.sock, socket.socket):
            self.sock.close()
            self.logger.debug(f"Socket to host {self.host} closed")

    def socket_isalive(self) -> bool:
        """
        Check if socket is alive

        Args:
            N/A

        Returns:
            bool True/False if socket is alive

        Raises:
            N/A

        """
        try:
            if isinstance(self.sock, socket.socket):
                self.sock.send(b"")
                return True
        except OSError:
            self.logger.debug(f"Socket to host {self.host} is not alive")
            return False
        return False
