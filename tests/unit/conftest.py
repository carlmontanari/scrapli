import types
from io import BytesIO
from threading import Lock
from typing import Any, Callable, Dict, Optional, Tuple

import pytest

from scrapli.channel import Channel
from scrapli.driver import NetworkDriver, Scrape
from scrapli.driver.core.cisco_iosxe.driver import PRIVS
from scrapli.netmiko_compatability import (
    netmiko_find_prompt,
    netmiko_send_command,
    netmiko_send_command_timing,
    netmiko_send_config_set,
)
from scrapli.transport.transport import Transport


class MockNSSH(Scrape):
    def __init__(self, channel_ops, initial_bytes, *args, comms_ansi=False, **kwargs):
        self.channel_ops = channel_ops
        self.initial_bytes = initial_bytes
        self.comms_ansi = comms_ansi
        super().__init__(*args, comms_ansi=comms_ansi, **kwargs)

    def _transport_factory(self, transport: str) -> Tuple[Callable[..., Any], Dict[str, Any]]:
        """
        Private factory method to produce transport class

        Args:
            transport: string name of transport class to use

        Returns:
            Transport: initialized Transport class

        Raises:
            N/A  # noqa

        """
        transport_class = MockTransport
        required_transport_args = (
            "host",
            "port",
            "timeout_socket",
            "channel_ops",
            "comms_return_char",
            "initial_bytes",
        )

        transport_args = {}
        for arg in required_transport_args:
            transport_args[arg] = getattr(self, arg)
        return transport_class, transport_args


class MockNetworkDriver(MockNSSH, NetworkDriver):
    def __init__(self, channel_ops, initial_bytes, *args, comms_ansi=False, **kwargs):
        super().__init__(channel_ops, initial_bytes, *args, comms_ansi=comms_ansi, **kwargs)
        self.privs = PRIVS

    def open(self):
        # Overriding "normal" network driver open method as we don't need to worry about disable
        # paging or pre login handles; ignoring this makes the mocked file read/write pieces simpler
        self.transport = self.transport_class(**self.transport_args)
        self.transport.open()
        self.channel = Channel(self.transport, **self.channel_args)


class MockTransport(Transport):
    def __init__(self, host, port, timeout_socket, comms_return_char, initial_bytes, channel_ops):
        self.host = host
        self.port = port
        self.timeout_socket = timeout_socket
        self.comms_return_char = comms_return_char
        self.session_lock = Lock()
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

    def flush(self) -> None:
        return

    def set_timeout(self, timeout: Optional[int] = None) -> None:
        return

    def set_blocking(self, blocking: bool = False) -> None:
        return


@pytest.fixture(scope="module")
def mocked_channel():
    def _create_mocked_channel(
        test_operations,
        initial_bytes=b"3560CX#",
        comms_ansi=False,
        comms_prompt_pattern=r"^[a-z0-9.\-@()/:]{1,32}[#>$]$",
    ):
        conn = MockNSSH(
            host="localhost",
            port=22,
            timeout_socket=1,
            channel_ops=test_operations,
            initial_bytes=initial_bytes,
            comms_ansi=comms_ansi,
            comms_prompt_pattern=comms_prompt_pattern,
        )
        conn.open()
        return conn

    return _create_mocked_channel


@pytest.fixture(scope="module")
def mocked_network_driver():
    def _create_mocked_network_driver(
        test_operations,
        initial_bytes=b"3560CX#",
        comms_ansi=False,
        comms_prompt_pattern=r"^[a-z0-9.\-@()/:]{1,32}[#>$]$",
    ):
        conn = MockNetworkDriver(
            host="localhost",
            port=22,
            timeout_socket=1,
            channel_ops=test_operations,
            initial_bytes=initial_bytes,
            comms_ansi=comms_ansi,
            comms_prompt_pattern=comms_prompt_pattern,
        )
        conn.open()
        return conn

    return _create_mocked_network_driver


@pytest.fixture(scope="module")
def mocked_netmiko_driver():
    def _create_mocked_netmiko_driver(
        test_operations,
        initial_bytes=b"3560CX#",
        comms_ansi=False,
        comms_prompt_pattern=r"^[a-z0-9.\-@()/:]{1,32}[#>$]$",
    ):
        conn = MockNetworkDriver(
            host="localhost",
            port=22,
            timeout_socket=1,
            channel_ops=test_operations,
            initial_bytes=initial_bytes,
            comms_ansi=comms_ansi,
            comms_prompt_pattern=comms_prompt_pattern,
        )
        conn.open()
        conn.find_prompt = types.MethodType(netmiko_find_prompt, conn)
        conn.send_command = types.MethodType(netmiko_send_command, conn)
        conn.send_command_timing = types.MethodType(netmiko_send_command_timing, conn)
        conn.send_config_set = types.MethodType(netmiko_send_config_set, conn)
        return conn

    return _create_mocked_netmiko_driver
