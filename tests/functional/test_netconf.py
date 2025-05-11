import pytest

ACTION_ARGNAMES = (
    "action",
    "platform",
    "transport",
)
ACTION_ARGVALUES = (
    (
        """
        <system xmlns="urn:dummy:actions">
            <reboot>
                <delay>5</delay>
            </reboot>
        </system>
        """,
        "netopeer",
        "bin",
    ),
)
ACTION_IDS = ("simple",)


@pytest.mark.parametrize(
    argnames=ACTION_ARGNAMES,
    argvalues=ACTION_ARGVALUES,
    ids=ACTION_IDS,
)
def test_action(action, netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.action(action=action))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=ACTION_ARGNAMES,
    argvalues=ACTION_ARGVALUES,
    ids=ACTION_IDS,
)
async def test_action_async(action, netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.action_async(action=action)

        netconf_assert_result(actual=actual)
