import asyncio
from io import BytesIO

import pytest

from scrapli.exceptions import ScrapliConnectionNotOpened, ScrapliTimeout


def test_handle_control_characters_response_empty_control_buf_iac(asynctelnet_transport):
    asynctelnet_transport.stdin = BytesIO()
    actual_control_buf = asynctelnet_transport._handle_control_chars_response(
        control_buf=b"", c=bytes([255])
    )
    assert actual_control_buf == bytes([255])


def test_handle_control_characters_response_not_iac(asynctelnet_transport):
    asynctelnet_transport.stdin = BytesIO()
    actual_control_buf = asynctelnet_transport._handle_control_chars_response(
        control_buf=b"", c=b"X"
    )
    assert asynctelnet_transport._initial_buf == b"X"
    assert actual_control_buf == b""


def test_handle_control_characters_response_second_char(asynctelnet_transport):
    asynctelnet_transport.stdin = BytesIO()
    actual_control_buf = asynctelnet_transport._handle_control_chars_response(
        control_buf=bytes([255]), c=bytes([253])
    )
    assert asynctelnet_transport._initial_buf == b""
    assert actual_control_buf == bytes([255, 253])


@pytest.mark.parametrize(
    "test_data", ((253, 252), (251, 254)), ids=("do-return-wont", "will-return-dont")
)
def test_handle_control_characters_response_third_char(asynctelnet_transport, test_data):
    control_buf_input, expected_output = test_data

    asynctelnet_transport.stdin = BytesIO()
    actual_control_buf = asynctelnet_transport._handle_control_chars_response(
        control_buf=bytes([255, control_buf_input]), c=bytes([1])
    )
    assert asynctelnet_transport._initial_buf == b""
    assert actual_control_buf == b""

    asynctelnet_transport.stdin.seek(0)
    # assert we get IAC, DONT, then whatever the command was
    assert asynctelnet_transport.stdin.read() == bytes([255, expected_output, 1])


def test_handle_control_characters_response_exception(asynctelnet_transport):
    with pytest.raises(ScrapliConnectionNotOpened):
        asynctelnet_transport._handle_control_chars_response(control_buf=b"", c=b"")


@pytest.mark.asyncio
async def test_handle_control_characters(monkeypatch, asynctelnet_transport):
    _read_called = 0

    async def _read(cls, _):
        nonlocal _read_called

        if _read_called == 0:
            _read_called += 1
            return bytes([255])

        await asyncio.sleep(0.5)

    monkeypatch.setattr(
        "asyncio.StreamReader.read",
        _read,
    )

    monkeypatch.setattr(
        "scrapli.transport.plugins.asynctelnet.transport.AsynctelnetTransport._handle_control_chars_response",
        lambda cls, **kwargs: None,
    )

    # lie like connection is open
    asynctelnet_transport.stdout = asyncio.StreamReader()
    asynctelnet_transport._base_transport_args.timeout_socket = 0.4

    await asynctelnet_transport._handle_control_chars()


@pytest.mark.asyncio
async def test_handle_control_characters_exception(asynctelnet_transport):
    with pytest.raises(ScrapliConnectionNotOpened):
        await asynctelnet_transport._handle_control_chars()


def test_close(asynctelnet_transport):
    # lie like connection is open
    asynctelnet_transport.stdout = asyncio.StreamReader()
    # make a stupid streamwriter... just enough to instantiate a real one :)
    asynctelnet_transport.stdin = asyncio.StreamWriter(
        BytesIO(), "", None, asyncio.get_event_loop()
    )

    asynctelnet_transport.close()

    assert asynctelnet_transport.stdout is None
    assert asynctelnet_transport.stdin is None


def test_isalive_no_session(asynctelnet_transport):
    assert asynctelnet_transport.isalive() is False


def test_isalive(asynctelnet_transport):
    # lie like connection is open
    asynctelnet_transport.stdout = asyncio.StreamReader()
    # make a stupid streamwriter... just enough to instantiate a real one :)
    asynctelnet_transport.stdin = asyncio.StreamWriter(
        BytesIO(), "", None, asyncio.get_event_loop()
    )
    assert asynctelnet_transport.isalive() is True


@pytest.mark.asyncio
async def test_read(asynctelnet_transport):
    # lie like connection is open
    asynctelnet_transport.stdout = asyncio.StreamReader()
    asynctelnet_transport.stdout.feed_data(b"somebytes\x00")

    assert await asynctelnet_transport.read() == b"somebytes"


@pytest.mark.asyncio
async def test_read_timeout(asynctelnet_transport):
    # lie like connection is open
    asynctelnet_transport.stdout = asyncio.StreamReader()
    asynctelnet_transport._base_transport_args.timeout_transport = 0.1

    with pytest.raises(ScrapliTimeout):
        await asynctelnet_transport.read()


def test_write(asynctelnet_transport):
    asynctelnet_transport.stdin = BytesIO()
    asynctelnet_transport.write(b"blah")
    asynctelnet_transport.stdin.seek(0)
    assert asynctelnet_transport.stdin.read() == b"blah"


def test_write_exception(asynctelnet_transport):
    with pytest.raises(ScrapliConnectionNotOpened):
        asynctelnet_transport.write("blah")
