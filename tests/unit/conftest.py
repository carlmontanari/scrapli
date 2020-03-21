from io import BytesIO
from typing import Any, Callable, Dict, Optional, Tuple

import pytest

from scrapli.channel import Channel
from scrapli.driver import NetworkDriver, Scrape
from scrapli.driver.core.cisco_iosxe.driver import PRIVS
from scrapli.transport.transport import Transport


class MockScrape(Scrape):
    def __init__(self, channel_ops, initial_bytes, *args, **kwargs):
        self.channel_ops = channel_ops
        self.initial_bytes = initial_bytes
        super().__init__(*args, **kwargs)

    def _transport_factory(self, transport: str) -> Tuple[Callable[..., Any], Dict[str, Any]]:
        """
        Private factory method to produce mock transport class

        Args:
            transport: string name of transport class to use

        Returns:
            Transport: initialized Transport class

        Raises:
            N/A  # noqa

        """
        transport_class = MockTransport
        required_transport_args = (
            "comms_return_char",
            "channel_ops",
            "initial_bytes",
        )
        transport_args = {}
        for arg in required_transport_args:
            transport_args[arg] = self._initialization_args.get(arg)
        transport_args["channel_ops"] = self.channel_ops
        transport_args["initial_bytes"] = self.initial_bytes
        return transport_class, transport_args


class MockTransport(Transport):
    def __init__(self, comms_return_char, initial_bytes, channel_ops):
        super().__init__()
        self.comms_return_char = comms_return_char
        self.channel_ops = channel_ops
        self.fd = BytesIO(initial_bytes=initial_bytes)
        self.input_counter = 0
        self.return_counter = 0

    def open(self) -> None:
        return

    def close(self) -> None:
        return

    def isalive(self) -> bool:
        return True

    def read(self) -> bytes:
        return self.fd.read(65535)

    def write(self, channel_input: str) -> None:
        if channel_input == self.comms_return_char:
            cur_input, cur_output = self.channel_ops[self.input_counter]
            self.input_counter += 1
            self.return_counter += 1

            self.fd.write(cur_output.encode())

            if self.return_counter == 1:
                self.return_counter = 0
                self.fd.seek(-len(cur_output) - 1, 1)
            else:
                self.fd.seek(len(cur_input) - 1)
        seek_offset = len(channel_input)
        self.fd.write(channel_input.encode())
        self.fd.seek(-seek_offset, 1)

    def set_timeout(self, timeout: Optional[int] = None) -> None:
        return

    def _keepalive_standard(self) -> None:
        return


class MockNetworkDriver(MockScrape, NetworkDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.privs = PRIVS
        self.auth_secondary = "password"

    def open(self):
        # Overriding "normal" network driver open method as we don't need to worry about disable
        # paging or pre login handles; ignoring this makes the mocked file read/write pieces simpler
        self.transport = self.transport_class(**self.transport_args)
        self.transport.open()
        self.channel = Channel(self.transport, **self.channel_args)


@pytest.fixture(scope="module")
def mocked_channel():
    def _create_mocked_channel(test_operations, initial_bytes=b"3560CX#", **kwargs):
        conn = MockScrape(
            host="localhost", channel_ops=test_operations, initial_bytes=initial_bytes, **kwargs
        )
        conn.open()
        return conn

    return _create_mocked_channel


@pytest.fixture(scope="module")
def mocked_network_driver():
    def _create_mocked_network_driver(test_operations, initial_bytes=b"3560CX#", **kwargs):
        conn = MockNetworkDriver(
            host="localhost", channel_ops=test_operations, initial_bytes=initial_bytes, **kwargs
        )
        conn.open()
        return conn

    return _create_mocked_network_driver
