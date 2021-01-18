"""scrapli.driver.base.sync_driver"""
from types import TracebackType
from typing import Any, Optional, Type

from scrapli.channel import Channel
from scrapli.driver.base.base_driver import BaseDriver
from scrapli.exceptions import ScrapliValueError
from scrapli.transport import ASYNCIO_TRANSPORTS


class Driver(BaseDriver):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

        if self.transport_name in ASYNCIO_TRANSPORTS:
            raise ScrapliValueError(
                "provided transport is *not* an sync transport, must use an sync transport with"
                " the (sync)Driver(s)"
            )

        self.channel = Channel(
            transport=self.transport,
            base_channel_args=self._base_channel_args,
        )

    def __enter__(self) -> "Driver":
        """
        Enter method for context manager

        Args:
            N/A

        Returns:
            Driver: opened Driver object

        Raises:
            N/A

        """
        self.open()
        return self

    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """
        Exit method to cleanup for context manager

        Args:
            exception_type: exception type being raised
            exception_value: message from exception being raised
            traceback: traceback from exception being raised

        Returns:
            None

        Raises:
            N/A

        """
        self.close()

    def open(self) -> None:
        """
        Open the scrapli connection

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        self._pre_open_closing_log(closing=False)

        self.transport.open()

        if self.transport_name in ("system",) and not self.auth_bypass:
            self.channel.channel_authenticate_ssh(
                auth_password=self.auth_password,
                auth_private_key_passphrase=self.auth_private_key_passphrase,
            )
        if (
            self.transport_name
            in (
                "telnet",
                "asynctelnet",
            )
            and not self.auth_bypass
        ):
            self.channel.channel_authenticate_telnet(
                auth_username=self.auth_username, auth_password=self.auth_password
            )

        if self.on_open:
            self.on_open(self)

        self._post_open_closing_log(closing=False)

    def close(self) -> None:
        """
        Close the scrapli connection

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        self._pre_open_closing_log(closing=True)

        if self.on_close:
            self.on_close(self)

        if self.channel.channel_log:
            self.channel.channel_log.close()

        self.transport.close()

        self._post_open_closing_log(closing=True)
