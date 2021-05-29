import asyncio
from io import BytesIO

import pytest
from asyncssh.connection import SSHClientConnection
from asyncssh.stream import SSHReader

from scrapli.exceptions import ScrapliConnectionNotOpened, ScrapliTimeout


class DumbContainer:
    def __init__(self):
        self.preferred_auth = ()

    def __getattr__(self, item):
        # options has a billion attributes, just return None, doesnt matter for this test
        return None


def test_close(monkeypatch, asyncssh_transport):
    def _close(cls):
        pass

    monkeypatch.setattr(
        "asyncssh.connection.SSHClientConnection.close",
        _close,
    )

    # lie and pretend the session is already assigned
    options = DumbContainer()
    asyncssh_transport.session = SSHClientConnection(loop=asyncio.get_event_loop(), options=options)

    asyncssh_transport.close()

    assert asyncssh_transport.session is None
    assert asyncssh_transport.stdin is None
    assert asyncssh_transport.stdout is None


def test_close_catch_brokenpipe(monkeypatch, asyncssh_transport):
    def _close(cls):
        raise BrokenPipeError

    monkeypatch.setattr(
        "asyncssh.connection.SSHClientConnection.close",
        _close,
    )

    # lie and pretend the session is already assigned
    options = DumbContainer()
    asyncssh_transport.session = SSHClientConnection(loop=asyncio.get_event_loop(), options=options)

    asyncssh_transport.close()

    assert asyncssh_transport.session is None
    assert asyncssh_transport.stdin is None
    assert asyncssh_transport.stdout is None


def test_isalive_no_session(asyncssh_transport):
    assert asyncssh_transport.isalive() is False


def test_isalive(asyncssh_transport):
    # lie and pretend the session is already assigned
    options = DumbContainer()
    asyncssh_transport.session = SSHClientConnection(loop=asyncio.get_event_loop(), options=options)

    # lie and tell asyncssh auth is done
    asyncssh_transport.session._auth_complete = True

    # also have to lie and create a transport and have it return False when is_closing is called
    asyncssh_transport.session._transport = DumbContainer()
    asyncssh_transport.session._transport.is_closing = lambda: False

    assert asyncssh_transport.isalive() is True


def test_isalive_attribute_error(asyncssh_transport):
    # lie and pretend the session is already assigned
    options = DumbContainer()
    asyncssh_transport.session = SSHClientConnection(loop=asyncio.get_event_loop(), options=options)

    # lie and tell asyncssh auth is done
    asyncssh_transport.session._auth_complete = True

    assert asyncssh_transport.isalive() is False


@pytest.mark.asyncio
async def test_read(monkeypatch, asyncssh_transport):
    async def _read(cls, _):
        return b"somebytes"

    monkeypatch.setattr(
        "asyncssh.stream.SSHReader.read",
        _read,
    )

    # lie and pretend the session is already assigned/stdout is already a thing
    asyncssh_transport.stdout = SSHReader("", "")

    assert await asyncssh_transport.read() == b"somebytes"


@pytest.mark.asyncio
async def test_read_exception_not_open(asyncssh_transport):
    with pytest.raises(ScrapliConnectionNotOpened):
        await asyncssh_transport.read()


@pytest.mark.asyncio
async def test_read_exception_timeout(monkeypatch, asyncssh_transport):
    async def _read(cls, _):
        await asyncio.sleep(0.5)

    monkeypatch.setattr(
        "asyncssh.stream.SSHReader.read",
        _read,
    )

    # lie and pretend the session is already assigned/stdout is already a thing
    asyncssh_transport.stdout = SSHReader("", "")
    asyncssh_transport._base_transport_args.timeout_transport = 0.1

    with pytest.raises(ScrapliTimeout):
        await asyncssh_transport.read()


def test_write(asyncssh_transport):
    asyncssh_transport.stdin = BytesIO()
    asyncssh_transport.write(b"blah")
    asyncssh_transport.stdin.seek(0)
    assert asyncssh_transport.stdin.read() == b"blah"


def test_write_exception(asyncssh_transport):
    with pytest.raises(ScrapliConnectionNotOpened):
        asyncssh_transport.write("blah")
