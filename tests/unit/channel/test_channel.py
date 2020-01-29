from io import BytesIO
from threading import Lock
from typing import Optional

from nssh.channel import Channel
from nssh.transport.transport import Transport


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


class MockChannel(Channel):
    def __init__(self, comms_prompt_pattern, comms_return_char, comms_ansi, timeout_ops):
        transport = MockTransport("localhost")
        super().__init__(
            transport, comms_prompt_pattern, comms_return_char, comms_ansi, timeout_ops
        )


def test__restructure_output_no_strip_prompt():
    channel = MockChannel(r"^[a-z0-9.\-@()/:]{1,32}[#>$]$", "\n", False, timeout_ops=0.01)
    output = b"hostname 3560CX\r\n3560CX#"
    output = channel._restructure_output(output)
    assert output == b"hostname 3560CX\n3560CX#"


def test__restructure_output_strip_prompt():
    channel = MockChannel(r"^[a-z0-9.\-@()/:]{1,32}[#>$]$", "\n", False, timeout_ops=0.01)
    output = b"hostname 3560CX\r\n3560CX#"
    output = channel._restructure_output(output, strip_prompt=True)
    assert output == b"hostname 3560CX\n"


def test__read_until_prompt_regex_pattern():
    channel = MockChannel(r"^[a-z0-9.\-@()/:]{1,32}[#>$]$", "\n", False, timeout_ops=0.01)
    parse_output = b"!\r\nntp server 172.31.255.1 prefer\r\n!\r\nend\r\n\r\n3560CX#"
    output = channel._read_until_prompt(parse_output)
    assert output == b"!\n\nntp server 172.31.255.1 prefer\n\n!\n\nend\n\n\n\n3560CX#"


def test__read_until_prompt_string_pattern():
    channel = MockChannel("3560CX#", "\n", False, timeout_ops=0.01)
    parse_output = b"!\r\nntp server 172.31.255.1 prefer\r\n!\r\nend\r\n\r\n3560CX#"
    output = channel._read_until_prompt(parse_output)
    assert output == b"!\n\nntp server 172.31.255.1 prefer\n\n!\n\nend\n\n\n\n3560CX#"


def test__strip_ansi():
    def channel_read_mock():
        return b"[admin@CoolDevice.Sea1: \x1b[1m/\x1b[0;0m]$ ls -al"

    channel = MockChannel("3560CX#", "\n", True, timeout_ops=0.01)
    channel.transport.read = channel_read_mock
    output = channel._read_until_input(b"ls -al")
    assert output == b"[admin@CoolDevice.Sea1: /]$ ls -al"


def test__get_prompt():
    read_data = """
Hardware Board Revision Number  : 0x02


Switch Ports Model                     SW Version            SW Image
------ ----- -----                     ----------            ----------
*    1 12    WS-C3560CX-8PC-S          15.2(4)E7             C3560CX-UNIVERSALK9-M


Configuration register is 0xF

3560CX#
    """
    read_fd = BytesIO(initial_bytes=read_data.encode())
    write_fd = BytesIO()

    def mock_read():
        return read_fd.read(1024)

    def mock_write(channel_input):
        write_fd.write(channel_input.encode())

    transport = MockTransport("localhost")
    transport.read = mock_read
    transport.write = mock_write
    channel = Channel(transport, "3560CX#", "\n", False, timeout_ops=1)

    output = channel.get_prompt()
    assert output == "3560CX#"


def test__send_input():
    initial_bytes = b"3560CX#"
    fd = BytesIO(initial_bytes=initial_bytes)
    return_char = "\n"
    channel_input = "show ip access-lists"
    channel_output = """Extended IP access list ext_acl_fw
        10 deny ip 0.0.0.0 0.255.255.255 any
        20 deny ip 10.0.0.0 0.255.255.255 any
        30 deny ip 100.64.0.0 0.63.255.255 any (2 matches)
        40 deny ip 127.0.0.0 0.255.255.255 any
        50 deny ip 169.254.0.0 0.0.255.255 any
        60 deny ip 172.16.0.0 0.15.255.255 any
        70 deny ip 192.0.0.0 0.0.0.255 any
        80 deny ip 192.0.2.0 0.0.0.255 any
        90 deny ip 192.168.0.0 0.0.255.255 any
        100 deny ip 198.18.0.0 0.1.255.255 any
        110 deny ip 198.51.100.0 0.0.0.255 any
        120 deny ip 203.0.113.0 0.0.0.255 any
        130 deny ip 224.0.0.0 15.255.255.255 any
        140 deny ip 240.0.0.0 15.255.255.255 any
    3560CX#"""

    def mock_read():
        output = fd.read(1024)
        print(output)
        return output

    def mock_write(received_input):
        if received_input == channel_input:
            fd.write(channel_input.encode())
            fd.seek(0)
        elif received_input == "\n":
            fd.write(channel_output.encode())
            fd.seek(len(channel_input))

    transport = MockTransport("localhost")
    transport.read = mock_read
    transport.write = mock_write
    channel = Channel(transport, "3560CX#", return_char, False, timeout_ops=1)

    output, processed_output = channel._send_input(channel_input, strip_prompt=False)
    assert processed_output.decode() == channel_output


def test_send_inputs():
    initial_bytes = b"3560CX#"
    fd = BytesIO(initial_bytes=initial_bytes)
    return_char = "\n"
    channel_input = "show ip access-lists"
    channel_output = """Extended IP access list ext_acl_fw
    10 deny ip 0.0.0.0 0.255.255.255 any
    20 deny ip 10.0.0.0 0.255.255.255 any
    30 deny ip 100.64.0.0 0.63.255.255 any (2 matches)
    40 deny ip 127.0.0.0 0.255.255.255 any
    50 deny ip 169.254.0.0 0.0.255.255 any
    60 deny ip 172.16.0.0 0.15.255.255 any
    70 deny ip 192.0.0.0 0.0.0.255 any
    80 deny ip 192.0.2.0 0.0.0.255 any
    90 deny ip 192.168.0.0 0.0.255.255 any
    100 deny ip 198.18.0.0 0.1.255.255 any
    110 deny ip 198.51.100.0 0.0.0.255 any
    120 deny ip 203.0.113.0 0.0.0.255 any
    130 deny ip 224.0.0.0 15.255.255.255 any
    140 deny ip 240.0.0.0 15.255.255.255 any
3560CX#"""

    def mock_read():
        return fd.read(1024)

    def mock_write(received_input):
        if received_input == channel_input:
            fd.write(channel_input.encode())
            fd.seek(0)
        elif received_input == "\n":
            fd.write(channel_output.encode())
            fd.seek(len(channel_input))

    transport = MockTransport("localhost")
    transport.read = mock_read
    transport.write = mock_write
    channel = Channel(transport, "3560CX#", return_char, False, timeout_ops=1)

    output = channel.send_inputs(channel_input, strip_prompt=False)
    assert output[0].result == channel_output


def test_send_inputs_multiple():
    initial_bytes = b"3560CX#"
    fd = BytesIO(initial_bytes=initial_bytes)
    return_char = "\n"
    channel_input = "show ip access-lists"
    channel_output = """Extended IP access list ext_acl_fw
    10 deny ip 0.0.0.0 0.255.255.255 any
    20 deny ip 10.0.0.0 0.255.255.255 any
    30 deny ip 100.64.0.0 0.63.255.255 any (2 matches)
    40 deny ip 127.0.0.0 0.255.255.255 any
    50 deny ip 169.254.0.0 0.0.255.255 any
    60 deny ip 172.16.0.0 0.15.255.255 any
    70 deny ip 192.0.0.0 0.0.0.255 any
    80 deny ip 192.0.2.0 0.0.0.255 any
    90 deny ip 192.168.0.0 0.0.255.255 any
    100 deny ip 198.18.0.0 0.1.255.255 any
    110 deny ip 198.51.100.0 0.0.0.255 any
    120 deny ip 203.0.113.0 0.0.0.255 any
    130 deny ip 224.0.0.0 15.255.255.255 any
    140 deny ip 240.0.0.0 15.255.255.255 any
3560CX#"""
    channel_input_2 = "show ip prefix-list"
    channel_output_2 = """ip prefix-list pl_default: 1 entries
   seq 5 permit 0.0.0.0/0 le 32
3560CX#"""
    channel_ops = [(channel_input, channel_output), (channel_input_2, channel_output_2)]

    def mock_read():
        return fd.read1(1024)

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

    transport = MockTransport("localhost")
    transport.read = mock_read
    transport.write = mock_write
    channel = Channel(transport, "3560CX#", return_char, False, timeout_ops=1)

    output = channel.send_inputs((channel_input, channel_input_2), strip_prompt=False)
    assert output[0].result == channel_output
    assert output[1].result == channel_output_2


def test_send_inputs_interact():
    initial_bytes = b"3560CX#"
    fd = BytesIO(initial_bytes=initial_bytes)
    return_char = "\n"
    interact = ("clear logg", "Clear logging buffer [confirm]", "", "3560CX#")
    channel_ops = [(interact[0], interact[1]), (interact[2], interact[3])]

    def mock_read():
        return fd.read1(1024)

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

    transport = MockTransport("localhost")
    transport.read = mock_read
    transport.write = mock_write
    channel = Channel(transport, "3560CX#", return_char, False, timeout_ops=1)

    output = channel.send_inputs_interact(interact, hidden_response=False)
    assert output[0].result == "Clear logging buffer [confirm]\n3560CX#"


def test__send_return():
    write_fd = BytesIO()

    def mock_write(channel_input):
        write_fd.write(channel_input.encode())

    transport = MockTransport("localhost")
    transport.write = mock_write
    channel = Channel(transport, "3560CX#", "\n", False, timeout_ops=0.01)

    channel._send_return()
    sent_data = write_fd.getvalue()
    assert sent_data == b"\n"
