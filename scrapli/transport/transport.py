"""scrapli.transport.transport"""
import atexit
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from scrapli.exceptions import ScrapliKeepaliveFailure
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

        def kill_transport() -> None:
            if self.isalive():
                self.close()

        # ensure the transport is closed so keepalive can terminate if main thread tries to exit
        atexit.register(kill_transport)

        lock_counter = 0
        last_keepalive = datetime.now()
        while True:
            if not self.isalive():
                return
            diff = datetime.now() - last_keepalive
            if diff.seconds >= self.keepalive_interval:
                if not self.session_lock.locked():
                    self.logger.debug(
                        f"Sending 'network' keepalive with pattern {repr(self.keepalive_pattern)}."
                    )
                    lock_counter = 0
                    self.session_lock.acquire()
                    self.write(channel_input=self.keepalive_pattern)
                    self.session_lock.release()
                    last_keepalive = datetime.now()
                else:
                    lock_counter += 1
                    if lock_counter >= 3:
                        self.logger.info(
                            f"Keepalive thread missed {lock_counter} consecutive keepalives."
                        )
            if diff.seconds > self.keepalive_interval * 3:
                msg = (
                    "Keepalive thread has failed to send a keepalive in greater than three "
                    "times the keepalive interval!"
                )
                self.logger.critical(msg)
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
