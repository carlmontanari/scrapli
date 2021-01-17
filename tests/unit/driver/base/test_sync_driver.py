from io import BytesIO

import pytest

from scrapli.driver.base.sync_driver import Driver
from scrapli.exceptions import ScrapliValueError


def test_async_transport_exception():
    """Assert we raise ScrapliValueError if an async transport is provided to the sync driver"""
    with pytest.raises(ScrapliValueError):
        Driver(host="localhost", transport="asynctelnet")


def test_context_manager(monkeypatch):
    """Asserts context manager properly opens/closes"""
    channel_ssh_auth_called = False

    def _channel_ssh_auth(cls, auth_password, auth_private_key_passphrase):
        nonlocal channel_ssh_auth_called
        channel_ssh_auth_called = True

    monkeypatch.setattr(
        "scrapli.transport.plugins.system.transport.SystemTransport.open", lambda x: None
    )
    monkeypatch.setattr(
        "scrapli.channel.sync_channel.Channel.channel_authenticate_ssh", _channel_ssh_auth
    )

    with Driver(host="localhost") as conn:
        pass

    assert channel_ssh_auth_called is True


def test_open_ssh_channel_auth(monkeypatch, sync_driver):
    """Test patched ssh channel auth -- asserts methods get called where they should"""
    on_open_called = False
    channel_ssh_auth_called = False

    def _on_open(cls):
        nonlocal on_open_called
        on_open_called = True

    def _channel_ssh_auth(cls, auth_password, auth_private_key_passphrase):
        nonlocal channel_ssh_auth_called
        channel_ssh_auth_called = True

    sync_driver.on_open = _on_open

    monkeypatch.setattr(
        "scrapli.transport.plugins.system.transport.SystemTransport.open", lambda x: None
    )
    monkeypatch.setattr(
        "scrapli.channel.sync_channel.Channel.channel_authenticate_ssh", _channel_ssh_auth
    )

    sync_driver.open()

    assert on_open_called is True
    assert channel_ssh_auth_called is True


def test_open_telnet_channel_auth(monkeypatch, sync_driver_telnet):
    """Test patched telnet channel auth -- asserts methods get called where they should"""
    on_open_called = False
    channel_telnet_auth_called = False

    def _on_open(cls):
        nonlocal on_open_called
        on_open_called = True

    def _channel_telnet_auth(cls, auth_username, auth_password):
        nonlocal channel_telnet_auth_called
        channel_telnet_auth_called = True

    sync_driver_telnet.on_open = _on_open

    monkeypatch.setattr(
        "scrapli.transport.plugins.telnet.transport.TelnetTransport.open", lambda x: None
    )
    monkeypatch.setattr(
        "scrapli.channel.sync_channel.Channel.channel_authenticate_telnet", _channel_telnet_auth
    )

    sync_driver_telnet.open()

    assert on_open_called is True
    assert channel_telnet_auth_called is True


def test_close(sync_driver):
    """
    Test unit-testable driver close

    Asserts on_close gets called and channel log gets closed
    """
    on_close_called = False

    def _on_close(cls):
        nonlocal on_close_called
        on_close_called = True

    sync_driver.on_close = _on_close
    sync_driver.channel.channel_log = BytesIO()
    assert sync_driver.channel.channel_log.closed is False

    # close will basically do nothing as no transport is open, so no need to mock/patch
    sync_driver.close()

    assert on_close_called is True
    assert sync_driver.channel.channel_log.closed is True
