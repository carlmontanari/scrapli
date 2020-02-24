"""scrapli.transport.transport"""
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from logging import getLogger
from threading import Lock
from typing import Dict, Optional, Union

LOG = getLogger("transport")


class Transport(ABC):
    @abstractmethod
    def __init__(self, *args: Union[str, int], **kwargs: Dict[str, Union[str, int]]) -> None:
        self.host: str = ""
        self.keepalive: bool = False
        self.keepalive_interval: int = 30
        self.keepalive_type: str = "network"
        self.keepalive_pattern: str = "\005"
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
            N/A

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
                        LOG.error(f"Keepalive thread missed {lock_counter} consecutive keepalives.")
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
