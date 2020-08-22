import pytest


@pytest.mark.asyncio
async def test_junos_open_close(async_juniper_junos_conn):
    await async_juniper_junos_conn.open()
    assert await async_juniper_junos_conn.get_prompt() == "vrnetlab>"
    # "more" will show up if we haven't sent terminal length 0 to the mock nxos server
    response = await async_juniper_junos_conn.send_command(command="show version")
    assert "more" not in response.result.lower()
    await async_juniper_junos_conn.close()
