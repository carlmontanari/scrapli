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


def test_timeout_ops_property(async_cisco_iosxe_conn):
    # note that there is "sync" and "async" version of this test as the property setter/getter lives
    # in the sync and async drivers -- didnt want to deal w/ having the property in the base driver
    # and having to deal w/ _get_timeout_ops/_set_timeout_ops methods to get overridden by the sync
    # and async drivers
    assert async_cisco_iosxe_conn.timeout_ops == 30
    assert async_cisco_iosxe_conn.channel.timeout_ops == 30
    async_cisco_iosxe_conn.timeout_ops = 5
    assert async_cisco_iosxe_conn.timeout_ops == 5
    assert async_cisco_iosxe_conn.channel.timeout_ops == 5
