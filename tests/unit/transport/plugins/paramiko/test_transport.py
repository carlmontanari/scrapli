from io import BytesIO
from socket import socket

import pytest
from paramiko.channel import Channel
from paramiko.transport import Transport

from scrapli.exceptions import ScrapliConnectionError, ScrapliConnectionNotOpened


def test_open_channel_no_session(paramiko_transport):
    with pytest.raises(ScrapliConnectionNotOpened):
        assert paramiko_transport._open_channel()


def test_close(monkeypatch, paramiko_transport):
    _close_called = False

    def _close(cls):
        nonlocal _close_called
        _close_called = True

    monkeypatch.setattr(
        "paramiko.channel.Channel.close",
        _close,
    )

    paramiko_transport.session = Transport(socket())
    paramiko_transport.session_channel = Channel(0)
    paramiko_transport.close()

    assert paramiko_transport.session is None
    assert paramiko_transport.session_channel is None
    assert _close_called is True


def test_isalive_no_session(paramiko_transport):
    assert paramiko_transport.isalive() is False


def test_isalive(monkeypatch, paramiko_transport):
    def _isalive(cls):
        return True

    monkeypatch.setattr(
        "paramiko.transport.Transport.is_alive",
        _isalive,
    )

    paramiko_transport.session = Transport(socket())
    assert paramiko_transport.isalive() is True


def test_read(monkeypatch, paramiko_transport):
    def _recv(cls, _):
        return b"somebytes"

    monkeypatch.setattr(
        "paramiko.channel.Channel.recv",
        _recv,
    )

    # lie and pretend the session is already assigned
    paramiko_transport.session_channel = Channel(0)

    assert paramiko_transport.read() == b"somebytes"


def test_read_exception_not_open(paramiko_transport):
    with pytest.raises(ScrapliConnectionNotOpened):
        paramiko_transport.read()


def test_read_exception(monkeypatch, paramiko_transport):
    def _recv(cls, _):
        raise Exception

    monkeypatch.setattr(
        "paramiko.channel.Channel.recv",
        _recv,
    )

    # lie and pretend the session is already assigned
    paramiko_transport.session_channel = Channel(0)

    with pytest.raises(ScrapliConnectionError):
        paramiko_transport.read()


def test_write(monkeypatch, paramiko_transport):
    _send_buf = BytesIO()

    def _send(cls, channel_input):
        nonlocal _send_buf
        _send_buf.write(channel_input)

    monkeypatch.setattr(
        "paramiko.channel.Channel.send",
        _send,
    )

    # lie and pretend the session is already assigned
    paramiko_transport.session_channel = Channel(0)

    paramiko_transport.write(b"blah")
    _send_buf.seek(0)
    assert _send_buf.read() == b"blah"


def test_write_exception(paramiko_transport):
    with pytest.raises(ScrapliConnectionNotOpened):
        paramiko_transport.write("blah")
