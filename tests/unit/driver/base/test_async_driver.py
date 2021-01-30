from io import BytesIO

import pytest

from scrapli.driver.base.async_driver import AsyncDriver
from scrapli.exceptions import ScrapliValueError


def test_sync_transport_exception():
    """Assert we raise ScrapliValueError if a sync transport is provided to the async driver"""
    with pytest.raises(ScrapliValueError):
        AsyncDriver(host="localhost", transport="system")


@pytest.mark.asyncio
async def test_context_manager(monkeypatch):
    """Asserts context manager properly opens/closes"""
    channel_telnet_auth_called = False

    async def _open(cls):
        pass

    async def _channel_telnet_auth(cls, auth_username, auth_password):
        nonlocal channel_telnet_auth_called
        channel_telnet_auth_called = True

    monkeypatch.setattr(
        "scrapli.transport.plugins.asynctelnet.transport.AsynctelnetTransport.open", _open
    )
    monkeypatch.setattr(
        "scrapli.channel.async_channel.AsyncChannel.channel_authenticate_telnet",
        _channel_telnet_auth,
    )

    async with AsyncDriver(host="localhost", transport="asynctelnet") as conn:
        pass

    assert channel_telnet_auth_called is True


@pytest.mark.asyncio
async def test_open_telnet_channel_auth(monkeypatch, async_driver):
    """Test patched telnet channel auth -- asserts methods get called where they should"""
    on_open_called = False
    channel_telnet_auth_called = False

    async def _on_open(cls):
        nonlocal on_open_called
        on_open_called = True

    async def _open(cls):
        pass

    async def _channel_telnet_auth(cls, auth_username, auth_password):
        nonlocal channel_telnet_auth_called
        channel_telnet_auth_called = True

    async_driver.on_open = _on_open

    monkeypatch.setattr(
        "scrapli.transport.plugins.asynctelnet.transport.AsynctelnetTransport.open", _open
    )
    monkeypatch.setattr(
        "scrapli.channel.async_channel.AsyncChannel.channel_authenticate_telnet",
        _channel_telnet_auth,
    )

    await async_driver.open()

    assert on_open_called is True
    assert channel_telnet_auth_called is True


@pytest.mark.asyncio
async def test_close(async_driver):
    """
    Test unit-testable driver close

    Asserts on_close gets called and channel log gets closed
    """
    on_close_called = False

    async def _on_close(cls):
        nonlocal on_close_called
        on_close_called = True

    async_driver.on_close = _on_close
    async_driver.channel.channel_log = BytesIO()
    assert async_driver.channel.channel_log.closed is False

    # close will basically do nothing as no transport is open, so no need to mock/patch
    await async_driver.close()

    assert on_close_called is True
    assert async_driver.channel.channel_log.closed is True
