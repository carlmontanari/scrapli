"""scrapli.transport.base.socket"""
import socket
from typing import Optional

from scrapli.exceptions import ScrapliConnectionNotOpened
from scrapli.logging import get_instance_logger


class Socket:
    def __init__(self, host: str, port: int, timeout: float):
        """
        Socket object

        Args:
            host: host to connect to
            port: port to connect to
            timeout: timeout in seconds

        Returns:
            None

        Raises:
            N/A

        """
        self.logger = get_instance_logger(instance_name="scrapli.socket", host=host, port=port)

        self.host = host
        self.port = port
        self.timeout = timeout

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
        return self.isalive()

    def open(self) -> None:
        """
        Open underlying socket

        Args:
            N/A

        Returns:
            None

        Raises:
            ScrapliConnectionNotOpened: if cant fetch socket addr info
            ScrapliConnectionNotOpened: if socket refuses connection
            ScrapliConnectionNotOpened: if socket connection times out

        """
        self.logger.debug(f"opening socket connection to '{self.host}' on port '{self.port}'")

        socket_af = None
        try:
            sock_host = socket.gethostbyname(self.host)
            sock_info = socket.getaddrinfo(sock_host, self.port)
            if sock_info:
                socket_af = sock_info[0][0]
        except socket.gaierror:
            pass

        if not socket_af:
            # this will likely need to be clearer just dont know what failure scenarios exist for
            # this yet...
            raise ScrapliConnectionNotOpened("failed to determine socket address family for host")

        if not self.isalive():
            self.sock = socket.socket(socket_af, socket.SOCK_STREAM)
            self.sock.settimeout(self.timeout)

            try:
                self.sock.connect((sock_host, self.port))
            except ConnectionRefusedError as exc:
                raise ScrapliConnectionNotOpened(
                    f"connection refused trying to open socket to {self.host} on port {self.port}"
                ) from exc
            except socket.timeout as exc:
                raise ScrapliConnectionNotOpened(
                    f"timed out trying to open socket to {self.host} on port {self.port}"
                ) from exc

        self.logger.debug(
            f"opened socket connection to '{self.host}' on port '{self.port}' successfully"
        )

    def close(self) -> None:
        """
        Close socket

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        self.logger.debug(f"closing socket connection to '{self.host}' on port '{self.port}'")

        if self.isalive() and isinstance(self.sock, socket.socket):
            self.sock.close()

        self.logger.debug(
            f"closed socket connection to '{self.host}' on port '{self.port}' successfully"
        )

    def isalive(self) -> bool:
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
