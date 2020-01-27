from typing import Optional

from nssh.channel import Channel
from nssh.transport.transport import Transport


class MockTransport(Transport):
    def __init__(self, host):
        self.host = host

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
    channel = MockChannel("^[a-z0-9.\-@()/:]{1,32}[#>$]$", "\n", False, timeout_ops=0.01)
    output = b"hostname 3560CX\r\n3560CX#"
    output = channel._restructure_output(output)
    assert output == b"hostname 3560CX\n3560CX#"


def test__restructure_output_strip_prompt():
    channel = MockChannel("^[a-z0-9.\-@()/:]{1,32}[#>$]$", "\n", False, timeout_ops=0.01)
    output = b"hostname 3560CX\r\n3560CX#"
    output = channel._restructure_output(output, strip_prompt=True)
    assert output == b"hostname 3560CX\n"


def test__read_until_prompt_regex_pattern():
    channel = MockChannel(r"^[a-z0-9.\-@()/:]{1,32}[#>$]$", "\n", False, timeout_ops=0.01)
    parse_output = b"!\r\nntp server 172.31.255.1 prefer\r\n!\r\nend\r\n\r\n3560CX#"
    output = channel._read_until_prompt(parse_output)
    assert output == b"!\r\nntp server 172.31.255.1 prefer\r\n!\r\nend\r\n\r\n3560CX#"


def test__read_until_prompt_string_pattern():
    channel = MockChannel("3560CX#", "\n", False, timeout_ops=0.01)
    parse_output = b"!\r\nntp server 172.31.255.1 prefer\r\n!\r\nend\r\n\r\n3560CX#"
    output = channel._read_until_prompt(parse_output)
    assert output == b"!\r\nntp server 172.31.255.1 prefer\r\n!\r\nend\r\n\r\n3560CX#"
