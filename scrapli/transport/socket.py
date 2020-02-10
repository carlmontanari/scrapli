"""scrapli.transport.socket"""
import logging
import socket
from typing import Optional

from scrapli.exceptions import ScrapliTimeout

LOG = logging.getLogger("transport")


class Socket:
    def __init__(self, host: str, port: int, timeout: int):
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
        return f"Socket {self.__dict__}"

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
            except ConnectionRefusedError:
                LOG.critical(
                    f"Connection refused trying to open socket to {self.host} on port {self.port}"
                )
                raise ConnectionRefusedError(
                    f"Connection refused trying to open socket to {self.host} on port {self.port}"
                )
            except socket.timeout:
                LOG.critical(f"Timed out trying to open socket to {self.host} on port {self.port}")
                raise ScrapliTimeout(
                    f"Timed out trying to open socket to {self.host} on port {self.port}"
                )
            LOG.debug(f"Socket to host {self.host} opened")

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
            LOG.debug(f"Socket to host {self.host} closed")

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
            LOG.debug(f"Socket to host {self.host} is not alive")
            return False
        return False
