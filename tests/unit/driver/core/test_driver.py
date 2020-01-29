from io import BytesIO
from threading import Lock
from typing import Optional

import pytest

from nssh.channel import Channel
from nssh.driver.core.cisco_iosxe.driver import PRIVS
from nssh.driver.core.driver import NetworkDriver
from nssh.exceptions import UnknownPrivLevel
from nssh.transport import Transport


class MockTransport(Transport):
    def __init__(self, host):
        self.host = host
        self.session_lock = Lock()

    def open(self) -> None:
        return

    def close(self) -> None:
        return

    def isalive(self) -> bool:
        return True

    def read(self) -> bytes:
        return b""

    def write(self, channel_input: str) -> None:
        return

    def flush(self) -> None:
        return

    def set_timeout(self, timeout: Optional[int] = None) -> None:
        return

    def set_blocking(self, blocking: bool = False) -> None:
        return


class MockNetworkDriver(NetworkDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transport = MockTransport("localhost")
        self.channel = Channel(self.transport, "3560CX#", "\n", False, timeout_ops=1)
        self.privs = PRIVS


IOS_ARP = """Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  172.31.254.1            -   0000.0c07.acfe  ARPA   Vlan254
Internet  172.31.254.2            -   c800.84b2.e9c2  ARPA   Vlan254
"""


def test__determine_current_priv():
    base_driver = NetworkDriver()
    base_driver.privs = PRIVS
    current_priv = base_driver._determine_current_priv("execprompt>")
    assert current_priv.name == "exec"


def test__determine_current_priv_unknown():
    base_driver = NetworkDriver()
    base_driver.privs = PRIVS
    with pytest.raises(UnknownPrivLevel):
        base_driver._determine_current_priv("!!!!thisissoooowrongggg!!!!!!?!")


def test_textfsm_parse_output():
    base_driver = NetworkDriver()
    base_driver.textfsm_platform = "cisco_ios"
    result = base_driver.textfsm_parse_output("show ip arp", IOS_ARP)
    assert isinstance(result, list)
    assert result[0] == ["Internet", "172.31.254.1", "-", "0000.0c07.acfe", "ARPA", "Vlan254"]


def test__escalate():
    initial_bytes = b"3560CX#"
    fd = BytesIO(initial_bytes=initial_bytes)
    return_char = "\n"
    channel_output = """Hardware Board Revision Number  : 0x02


Switch Ports Model                     SW Version            SW Image
------ ----- -----                     ----------            ----------
*    1 12    WS-C3560CX-8PC-S          15.2(4)E7             C3560CX-UNIVERSALK9-M


Configuration register is 0xF

3560CX#"""
    channel_input_2 = "configure terminal"
    channel_output_2 = """Enter configuration commands, one per line.  End with CNTL/Z.
3560CX(config)#"""
    channel_ops = [(None, channel_output), (channel_input_2, channel_output_2)]

    def mock_read():
        return fd.read(1024)

    input_counter = 0
    return_counter = 0

    def mock_write(received_input):
        nonlocal input_counter, return_counter
        if received_input == return_char:
            cur_input, cur_output = channel_ops[input_counter]
            input_counter += 1
            return_counter += 1

            fd.write(cur_output.encode())

            if return_counter == 1:
                return_counter = 0
                fd.seek(-len(cur_output) - 1, 1)
            else:
                fd.seek(len(cur_input) - 1)

        seek_offset = len(received_input)
        fd.write(received_input.encode())
        fd.seek(-seek_offset, 1)

    conn_args = {"host": "localhost", "port": 22}
    conn = MockNetworkDriver(**conn_args)
    conn.transport.read = mock_read
    conn.transport.write = mock_write

    conn._escalate()
