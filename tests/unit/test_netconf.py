import pytest

from scrapli.netconf import DatastoreType


def test_session_id(netconf):
    with netconf as n:
        assert n.session_id is not None
        assert n.session_id != 0


ACTION_ARGNAMES = ("action",)
ACTION_ARGVALUES = (
    (
        """
        <system xmlns="urn:dummy:actions">
            <reboot>
                <delay>5</delay>
            </reboot>
        </system>
        """,
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


def test_cancel_commit(netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.cancel_commit())


@pytest.mark.asyncio
async def test_cancel_commit_async(netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.cancel_commit_async()

        netconf_assert_result(actual=actual)


def test_close_session(netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.close_session())


@pytest.mark.asyncio
async def test_close_session_async(netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.close_session_async()

        netconf_assert_result(actual=actual)


def test_commit(netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.commit())


@pytest.mark.asyncio
async def test_commit_async(netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.commit_async()

        netconf_assert_result(actual=actual)


def test_copy_config(netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.copy_config())


@pytest.mark.asyncio
async def test_copy_config_async(netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.copy_config_async()

        netconf_assert_result(actual=actual)


DELETE_CONFIG_ARGNAMES = ("target",)
DELETE_CONFIG_ARGVALUES = ((DatastoreType.CANDIDATE,),)
DELETE_CONFIG_IDS = ("simple",)


@pytest.mark.parametrize(
    argnames=DELETE_CONFIG_ARGNAMES,
    argvalues=DELETE_CONFIG_ARGVALUES,
    ids=DELETE_CONFIG_IDS,
)
def test_delete_config(target, netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.delete_config(target=target))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=DELETE_CONFIG_ARGNAMES,
    argvalues=DELETE_CONFIG_ARGVALUES,
    ids=DELETE_CONFIG_IDS,
)
async def test_delete_config_async(target, netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.delete_config_async(target=target)

        netconf_assert_result(actual=actual)


def test_discard(netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.discard())


@pytest.mark.asyncio
async def test_discard_async(netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.discard_async()

        netconf_assert_result(actual=actual)


EDIT_CONFIG_ARGNAMES = (
    "config",
    "target",
)
EDIT_CONFIG_ARGVALUES = (
    (
        "",
        DatastoreType.CANDIDATE,
    ),
)
EDIT_CONFIG_IDS = ("simple",)


@pytest.mark.parametrize(
    argnames=EDIT_CONFIG_ARGNAMES,
    argvalues=EDIT_CONFIG_ARGVALUES,
    ids=EDIT_CONFIG_IDS,
)
def test_edit_config(config, target, netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.edit_config(config=config, target=target))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=EDIT_CONFIG_ARGNAMES,
    argvalues=EDIT_CONFIG_ARGVALUES,
    ids=EDIT_CONFIG_IDS,
)
async def test_edit_config_async(config, target, netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.edit_config_async(config=config, target=target)

        netconf_assert_result(actual=actual)


EDIT_DATA_ARGNAMES = ("content",)
EDIT_DATA_ARGVALUES = (
    (
        """
        <system xmlns="urn:some:data">
            <hostname>my-router</hostname>
            <interfaces>
                <name>eth0</name>
                <enabled>true</enabled>
            </interfaces>
            <interfaces>
                <name>eth1</name>
                <enabled>false</enabled>
            </interfaces>
        </system>
        """,
    ),
)
EDIT_DATA_IDS = ("simple",)


@pytest.mark.parametrize(
    argnames=EDIT_DATA_ARGNAMES,
    argvalues=EDIT_DATA_ARGVALUES,
    ids=EDIT_DATA_IDS,
)
def test_edit_data(content, netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.edit_data(content=content))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=EDIT_DATA_ARGNAMES,
    argvalues=EDIT_DATA_ARGVALUES,
    ids=EDIT_DATA_IDS,
)
async def test_edit_data_async(content, netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.edit_data_async(content=content)

        netconf_assert_result(actual=actual)


def test_get_config(netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.get_config())


@pytest.mark.asyncio
async def test_get_config_async(netconf, netconf_assert_result):
    with netconf as n:
        actual = await n.get_config_async()

        netconf_assert_result(actual=actual)


GET_DATA_ARGNAMES = ("filter_",)
GET_DATA_ARGVALUES = (('<system xmlns="urn:some:data"></system>',),)
GET_DATA_IDS = ("simple",)


@pytest.mark.parametrize(
    argnames=GET_DATA_ARGNAMES,
    argvalues=GET_DATA_ARGVALUES,
    ids=GET_DATA_IDS,
)
def test_get_data(filter_, netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.get_data(filter_=filter_))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=GET_DATA_ARGNAMES,
    argvalues=GET_DATA_ARGVALUES,
    ids=GET_DATA_IDS,
)
async def test_get_data_async(filter_, netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.get_data_async(filter_=filter_)

        netconf_assert_result(actual=actual)


GET_SCHEMA_ARGNAMES = ("identifier",)
GET_SCHEMA_ARGVALUES = (("ietf-yang-types",),)
GET_SCHEMA_IDS = ("simple",)


@pytest.mark.parametrize(
    argnames=GET_SCHEMA_ARGNAMES,
    argvalues=GET_SCHEMA_ARGVALUES,
    ids=GET_SCHEMA_IDS,
)
def test_get_schema(identifier, netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.get_schema(identifier=identifier))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=GET_SCHEMA_ARGNAMES,
    argvalues=GET_SCHEMA_ARGVALUES,
    ids=GET_SCHEMA_IDS,
)
async def test_get_schema_async(identifier, netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.get_schema_async(identifier=identifier)

        netconf_assert_result(actual=actual)


GET_ARGNAMES = ("filter_",)
GET_ARGVALUES = (
    ("",),
    ("<interfaces><interface><name>Management0</name><state></state></interface></interfaces>",),
)
GET_IDS = (
    "simple",
    "filtered",
)


@pytest.mark.parametrize(
    argnames=GET_ARGNAMES,
    argvalues=GET_ARGVALUES,
    ids=GET_IDS,
)
def test_get(filter_, netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.get(filter_=filter_))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=GET_ARGNAMES,
    argvalues=GET_ARGVALUES,
    ids=GET_IDS,
)
async def test_get_async(filter_, netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.get_async(filter_=filter_)

        netconf_assert_result(actual=actual)


def test_lock(netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.lock())


@pytest.mark.asyncio
async def test_lock_async(netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.lock_async()

        netconf_assert_result(actual=actual)


def test_unlock(netconf, netconf_assert_result):
    with netconf as n:
        n.lock()
        netconf_assert_result(actual=n.unlock())


@pytest.mark.asyncio
async def test_unlock_async(netconf, netconf_assert_result):
    async with netconf as n:
        await n.lock_async()
        actual = await n.unlock_async()

        netconf_assert_result(actual=actual)


RAW_RPC_ARGNAMES = ("payload",)
RAW_RPC_ARGVALUES = (("<get-config><source><running/></source></get-config>",),)
RAW_RPC_IDS = ("simple",)


@pytest.mark.parametrize(
    argnames=RAW_RPC_ARGNAMES,
    argvalues=RAW_RPC_ARGVALUES,
    ids=RAW_RPC_IDS,
)
def test_raw_rpc(payload, netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.raw_rpc(payload=payload))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=RAW_RPC_ARGNAMES,
    argvalues=RAW_RPC_ARGVALUES,
    ids=RAW_RPC_IDS,
)
async def test_raw_rpc_async(payload, netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.raw_rpc_async(payload=payload)

        netconf_assert_result(actual=actual)


def test_validate(netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.validate())


@pytest.mark.asyncio
async def test_validate_async(netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.validate_async()

        netconf_assert_result(actual=actual)
