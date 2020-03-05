"""scrapli.transport.transport"""
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from logging import getLogger
from threading import Lock
from typing import Optional

from scrapli.exceptions import ScrapliKeepaliveFailure

LOG = getLogger("transport")


class Transport(ABC):
    def __init__(
        self,
        host: str = "",
        port: int = 22,
        timeout_socket: int = 5,
        timeout_transport: int = 5,
        timeout_exit: bool = True,
        keepalive: bool = False,
        keepalive_interval: int = 30,
        keepalive_type: str = "network",
        keepalive_pattern: str = "\005",
    ) -> None:
        """
        Transport Base Object

        Args:
            host: host ip/name to connect to
            port: port to connect to
            timeout_socket: timeout for establishing socket in seconds
            timeout_transport: timeout for ssh|telnet transport in seconds
            timeout_exit: True/False close transport if timeout encountered. If False and keepalives
                are in use, keepalives will prevent program from exiting so you should be sure to
                catch Timeout exceptions and handle them appropriately
            keepalive: whether or not to try to keep session alive
            keepalive_interval: interval to use for session keepalives
            keepalive_type: network|standard -- 'network' sends actual characters over the
                transport channel. This is useful for network-y type devices that may not support
                'standard' keepalive mechanisms. 'standard' attempts to use whatever 'standard'
                keepalive mechanisms are available in the selected transport mechanism. Check the
                transport documentation for details on what is supported and/or how it is
                implemented for any given transport driver
            keepalive_pattern: pattern to send to keep network channel alive. Default is
                u'\005' which is equivalent to 'ctrl+e'. This pattern moves cursor to end of the
                line which should be an innocuous pattern. This will only be entered *if* a lock
                can be acquired. This is only applicable if using keepalives and if the keepalive
                type is 'network'

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.host: str = host
        self.port: int = port
        self.timeout_socket: int = timeout_socket
        self.timeout_transport: int = timeout_transport
        self.timeout_exit: bool = timeout_exit
        self.keepalive: bool = keepalive
        self.keepalive_interval: int = keepalive_interval
        self.keepalive_type: str = keepalive_type
        self.keepalive_pattern: str = keepalive_pattern

        self.session_lock: Lock = Lock()

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
        class_dict["auth_password"] = "********"
        return f"Transport {class_dict}"

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

    @abstractmethod
    def set_timeout(self, timeout: Optional[int] = None) -> None:
        """
        Set session timeout

        Args:
            timeout: timeout in seconds

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """

    def _session_keepalive(self) -> None:
        """
        Spawn keepalive thread for transport session

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        if not self.keepalive:
            return
        pool = ThreadPoolExecutor()
        if self.keepalive_type == "network":
            pool.submit(self._keepalive_network)
        else:
            pool.submit(self._keepalive_standard)

    def _keepalive_network(self) -> None:
        """
        Send "in band" keepalives to devices.

        Generally used with "network" devices which do not have native keepalive support. This will
        try to acquire a session lock and send an innocuous character -- such as CTRL+E -- to keep
        the device "exec-timeout" (in network-y words) from expiring.

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            ScrapliKeepaliveFailure: if scrapli cant unlock and send keepalive in less than 3 *
                the keepalive_interval

        """
        lock_counter = 0
        last_keepalive = datetime.now()
        while True:
            if not self.isalive():
                return
            diff = datetime.now() - last_keepalive
            if diff.seconds >= self.keepalive_interval:
                if not self.session_lock.locked():
                    LOG.debug(
                        f"Sending 'network' keepalive with pattern {repr(self.keepalive_pattern)}."
                    )
                    lock_counter = 0
                    self.session_lock.acquire()
                    self.write(self.keepalive_pattern)
                    self.session_lock.release()
                    last_keepalive = datetime.now()
                else:
                    lock_counter += 1
                    if lock_counter >= 3:
                        LOG.info(f"Keepalive thread missed {lock_counter} consecutive keepalives.")
            if diff.seconds > self.keepalive_interval * 3:
                msg = (
                    "Keepalive thread has failed to send a keepalive in greater than three "
                    "times the keepalive interval!"
                )
                LOG.critical(msg)
                raise ScrapliKeepaliveFailure(msg)
            time.sleep(self.keepalive_interval / 10)

    @abstractmethod
    def _keepalive_standard(self) -> None:
        """
        Send "out of band" (protocol level) keepalives to devices.

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
