import pytest

from scrapli.driver.core.cisco_iosxe.driver import IOSXEDriver


def test_init():
    conn = IOSXEDriver(auth_secondary="enable-pass")
    assert conn.auth_secondary == "enable-pass"


def test_valid_on_connect_func():
    def on_open_func():
        pass

    conn = IOSXEDriver(on_open=on_open_func)
    assert callable(conn.on_open)


def test_invalid_on_connect_func():
    with pytest.raises(TypeError) as e:
        IOSXEDriver(on_open="not a callable")
    assert str(e.value) == "on_open must be a callable, got <class 'str'>"
