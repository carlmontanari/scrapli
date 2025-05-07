import pytest


def test_get_config(netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=c.get_config())


@pytest.mark.asyncio
async def test_get_config_async(netconf, netconf_assert_result):
    with netconf as n:
        actual = await n.get_config_async()

        netconf_assert_result(actual=actual)
