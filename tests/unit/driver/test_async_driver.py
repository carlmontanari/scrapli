import pytest

from scrapli.driver.core import AsyncIOSXEDriver
from scrapli.exceptions import TransportPluginError

from ...test_data.devices import DEVICES


@pytest.mark.asyncio
async def test_context_manager():
    device = DEVICES["mock_cisco_iosxe"].copy()
    async with AsyncIOSXEDriver(transport="asyncssh", **device) as conn:
        assert conn.isalive() is True
    assert conn.isalive() is False


@pytest.mark.asyncio
async def test_transport_bool(async_cisco_iosxe_conn):
    await async_cisco_iosxe_conn.open()
    assert bool(async_cisco_iosxe_conn.transport) is True
    await async_cisco_iosxe_conn.close()
    assert bool(async_cisco_iosxe_conn.transport) is False


@pytest.mark.asyncio
async def test_non_async_transport():
    device = DEVICES["mock_cisco_iosxe"].copy()
    with pytest.raises(TransportPluginError) as exc:
        AsyncIOSXEDriver(transport="system", **device)
    assert (
        str(exc.value)
        == "Attempting to use transport type system with an asyncio driver, must use one of ['asyncssh'] transports"
    )
