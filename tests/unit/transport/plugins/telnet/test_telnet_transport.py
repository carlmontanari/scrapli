import time
from io import BytesIO

import pytest

from scrapli.exceptions import ScrapliConnectionNotOpened, ScrapliTimeout


def test_handle_control_characters_response_empty_control_buf_iac(telnet_transport):
    # lie to transport so socket is not None
    telnet_transport.socket = 1

    actual_control_buf = telnet_transport._handle_control_chars_response(
        control_buf=b"", c=bytes([255])
    )
    assert actual_control_buf == bytes([255])


def test_handle_control_characters_response_not_iac(telnet_transport):
    # lie to transport so socket is not None
    telnet_transport.socket = 1

    actual_control_buf = telnet_transport._handle_control_chars_response(control_buf=b"", c=b"X")
    assert telnet_transport._cooked_buf == b"X"
    assert actual_control_buf == b""


def test_handle_control_characters_response_second_char(telnet_transport):
    # lie to transport so socket is not None
    telnet_transport.socket = 1

    actual_control_buf = telnet_transport._handle_control_chars_response(
        control_buf=bytes([255]), c=bytes([253])
    )
    assert telnet_transport._cooked_buf == b""
    assert actual_control_buf == bytes([255, 253])


@pytest.mark.parametrize(
    "test_data",
    ((253, 252), (251, 253), (252, 254)),
    ids=("do-return-wont", "will-return-do", "wont-return-dont"),
)
def test_handle_control_characters_response_third_char(telnet_transport, test_data):
    control_buf_input, expected_output = test_data

    # lie to transport so socket is not None and give sock a thing to write to
    class Dummy: ...

    class DummySock:
        def __init__(self):
            self.buf = BytesIO()

        def send(self, channel_input):
            self.buf.write(channel_input)

    telnet_transport.socket = Dummy()
    telnet_transport.socket.sock = DummySock()

    actual_control_buf = telnet_transport._handle_control_chars_response(
        control_buf=bytes([255, control_buf_input]), c=bytes([1])
    )
    assert telnet_transport._cooked_buf == b""
    assert actual_control_buf == b""

    telnet_transport.socket.sock.buf.seek(0)
    # assert we get IAC, DONT, then whatever the command was
    assert telnet_transport.socket.sock.buf.read() == bytes([255, expected_output, 1])


def test_handle_control_characters_response_exception(telnet_transport):
    with pytest.raises(ScrapliConnectionNotOpened):
        telnet_transport._handle_control_chars_response(control_buf=b"", c=b"")


def test_handle_control_characters(monkeypatch, telnet_transport):
    # lie like connection is open
    class Dummy: ...

    class DummySock:
        def __init__(self):
            self.buf = BytesIO()

        def send(self, channel_input):
            self.buf.write(channel_input)

        def settimeout(self, t): ...

    telnet_transport.socket = Dummy()
    telnet_transport.socket.sock = DummySock()

    telnet_transport._raw_buf = bytes([253])
    telnet_transport._handle_control_chars()

    assert telnet_transport._cooked_buf == bytes([253])


def test_handle_control_characters_exception(telnet_transport):
    with pytest.raises(ScrapliConnectionNotOpened):
        telnet_transport._handle_control_chars()


def test_close(telnet_transport):
    # lie like connection is open
    class Dummy:
        def close(self): ...

    telnet_transport.socket = Dummy()

    telnet_transport.close()

    assert telnet_transport.socket is None


def test_isalive_no_session(telnet_transport):
    assert telnet_transport.isalive() is False


def test_isalive(telnet_transport):
    # lie like connection is open
    class Dummy:
        def isalive(self):
            return True

    telnet_transport.socket = Dummy()

    assert telnet_transport.isalive() is True


async def test_read(telnet_transport):
    # lie like connection is open
    class Dummy: ...

    class DummySock:
        def __init__(self):
            self.buf = BytesIO()

        def send(self, channel_input):
            self.buf.write(channel_input)

        def settimeout(self, t): ...

        def recv(self, n):
            self.buf.seek(0)
            return self.buf.read()

    telnet_transport.socket = Dummy()
    telnet_transport.socket.sock = DummySock()
    telnet_transport.socket.sock.buf.write(b"somebytes")

    assert telnet_transport.read() == b"somebytes"


def test_read_timeout(telnet_transport):
    # lie like connection is open
    class Dummy:
        def close(self): ...

    class DummySock:
        def __init__(self):
            self.buf = BytesIO()

        def send(self, channel_input):
            self.buf.write(channel_input)

        def recv(self, n):
            time.sleep(1)
            return self.buf.read()

        def settimeout(self, t): ...

    telnet_transport.socket = Dummy()
    telnet_transport.socket.sock = DummySock()
    telnet_transport._base_transport_args.timeout_transport = 0.1

    with pytest.raises(ScrapliTimeout):
        telnet_transport.read()


def test_write(telnet_transport):
    # lie like connection is open
    class Dummy:
        def close(self): ...

    class DummySock:
        def __init__(self):
            self.buf = BytesIO()

        def send(self, channel_input):
            self.buf.write(channel_input)

        def recv(self, n):
            time.sleep(1)
            return self.buf.read()

        def settimeout(self, t): ...

    telnet_transport.socket = Dummy()
    telnet_transport.socket.sock = DummySock()
    telnet_transport.write(b"blah")
    telnet_transport.socket.sock.buf.seek(0)

    assert telnet_transport.read() == b"blah"


def test_write_exception(telnet_transport):
    with pytest.raises(ScrapliConnectionNotOpened):
        telnet_transport.write("blah")
