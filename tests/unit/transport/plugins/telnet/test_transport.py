from io import BytesIO
from telnetlib import Telnet

import pytest

from scrapli.exceptions import ScrapliConnectionError, ScrapliConnectionNotOpened
from scrapli.transport.plugins.telnet.transport import ScrapliTelnet


def test_scrapli_telnet_type():
    # connection error will get raised because 23 shouldnt be open for most devices running the test
    with pytest.raises(ConnectionError):
        conn = ScrapliTelnet("localhost", 23, 100)
        assert conn.host == "localhost"
        assert conn.port == 23
        assert conn.timeout == 100


def test_close(monkeypatch, telnet_transport):
    def _close(cls):
        pass

    monkeypatch.setattr(
        "telnetlib.Telnet.close",
        _close,
    )

    telnet_transport.session = Telnet()
    telnet_transport.close()

    assert telnet_transport.session is None


def test_isalive_no_session(telnet_transport):
    assert telnet_transport.isalive() is False


def test_isalive(telnet_transport):
    telnet_transport.session = Telnet()
    assert telnet_transport.isalive() is True


def test_read(monkeypatch, telnet_transport):
    def _read(cls):
        return b"somebytes"

    monkeypatch.setattr(
        "telnetlib.Telnet.read_eager",
        _read,
    )

    # lie and pretend the session is already assigned
    telnet_transport.session = Telnet()

    assert telnet_transport.read() == b"somebytes"


def test_read_exception_not_open(telnet_transport):
    with pytest.raises(ScrapliConnectionNotOpened):
        telnet_transport.read()


def test_read_exception_eof(monkeypatch, telnet_transport):
    def _read(cls):
        raise EOFError

    monkeypatch.setattr(
        "telnetlib.Telnet.read_eager",
        _read,
    )

    # lie and pretend the session is already assigned
    telnet_transport.session = Telnet()

    with pytest.raises(ScrapliConnectionError):
        telnet_transport.read()


def test_write(telnet_transport):
    telnet_transport.session = BytesIO()
    telnet_transport.write(b"blah")
    telnet_transport.session.seek(0)
    assert telnet_transport.session.read() == b"blah"


def test_write_exception(telnet_transport):
    with pytest.raises(ScrapliConnectionNotOpened):
        telnet_transport.write("blah")
