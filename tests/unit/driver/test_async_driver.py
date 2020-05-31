import sys

import pytest

from scrapli.driver.core import AsyncIOSXEDriver

from ...test_data.devices import DEVICES


# very unclear why this needs to be skipped with the module level skip...?
@pytest.mark.skipif(sys.platform == "win32", reason="no asyncssh on windows")
@pytest.mark.asyncio
async def test_context_manager():
    device = DEVICES["mock_cisco_iosxe"].copy()
    async with AsyncIOSXEDriver(transport="asyncssh", **device) as conn:
        assert conn.isalive() is True
    assert conn.isalive() is False


# very unclear why this needs to be skipped with the module level skip...?
@pytest.mark.skipif(sys.platform == "win32", reason="no asyncssh on windows")
@pytest.mark.asyncio
async def test_transport_bool(async_cisco_iosxe_conn):
    await async_cisco_iosxe_conn.open()
    assert bool(async_cisco_iosxe_conn.transport) is True
    await async_cisco_iosxe_conn.close()
    assert bool(async_cisco_iosxe_conn.transport) is False
