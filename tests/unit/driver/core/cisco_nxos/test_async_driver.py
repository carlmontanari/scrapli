import pytest


@pytest.mark.asyncio
async def test_nxos_open_close(async_cisco_nxos_conn):
    await async_cisco_nxos_conn.open()
    assert await async_cisco_nxos_conn.get_prompt() == "switch#"
    # "more" will show up if we haven't sent terminal length 0 to the mock nxos server
    response = await async_cisco_nxos_conn.send_command(command="show version")
    assert "more" not in response.result.lower()
    await async_cisco_nxos_conn.close()
