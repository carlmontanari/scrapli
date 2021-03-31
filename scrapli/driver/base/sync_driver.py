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
        self.channel.open()

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

        self.transport.close()
        self.channel.close()

        self._post_open_closing_log(closing=True)

    def commandeer(self, conn: "Driver", execute_on_open: bool = True) -> None:
        """
        Commandeer an existing connection

        Used to "take over" or "commandeer" a connection. This method accepts a second scrapli conn
        object and "steals" the transport from this connection and uses it for the current instance.
        The primary reason you would want this is to use a `GenericDriver` to connect to a console
        server and then to "commandeer" that connection and convert it to a "normal" network driver
        connection type (i.e. Junos, EOS, etc.) once connected to the network device (via the
        console server)

        Args:
            conn: connection to commandeer
            execute_on_open: execute the `on_open` function of the current object once the existing
                connection has been commandeered

        Returns:
            None

        Raises:
            N/A

        """
        original_logger = conn.logger
        original_transport = conn.transport
        original_transport_logger = conn.transport.logger
        original_channel_logger = conn.channel.logger

        self.logger = original_logger
        self.channel.logger = original_channel_logger
        self.channel.transport = original_transport
        self.transport = original_transport
        self.transport.logger = original_transport_logger

        if execute_on_open is True and self.on_open is not None:
            self.on_open(self)
