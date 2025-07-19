from copy import copy
from time import sleep

import pytest

from scrapli import (
    AuthOptions,
    Netconf,
    SessionOptions,
    TransportBinOptions,
    TransportTestOptions,
)
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
    netconf.open()
    netconf_assert_result(actual=netconf.close_session())


@pytest.mark.asyncio
async def test_close_session_async(netconf, netconf_assert_result):
    await netconf.open_async()
    actual = await netconf.close_session_async()
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


def test_kill_session(netconf_srl, netconf_assert_result):
    n1 = copy(netconf_srl)
    n2 = copy(netconf_srl)

    n1.open()
    n2.open()

    actual = n1.kill_session(session_id=n2.session_id)

    n1.close()

    netconf_assert_result(actual=actual)

    n2._free()


@pytest.mark.asyncio
async def test_kill_session_async(netconf_srl, netconf_assert_result):
    n1 = copy(netconf_srl)
    n2 = copy(netconf_srl)

    await n1.open_async()
    await n2.open_async()

    actual = await n1.kill_session_async(session_id=n2.session_id)

    await n1.close_async()

    netconf_assert_result(actual=actual)

    n2._free()


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


RAW_RPC_ARGNAMES = ("payload", "extra_namespaces")
RAW_RPC_ARGVALUES = (
    (
        "<get-config><source><running/></source></get-config>",
        None,
    ),
    (
        "<get-config><source><running/></source></get-config>",
        [("foo", "bar"), ("baz", "qux")],
    ),
)
RAW_RPC_IDS = (
    "simple",
    "simple-extra-namespaces",
)


@pytest.mark.parametrize(
    argnames=RAW_RPC_ARGNAMES,
    argvalues=RAW_RPC_ARGVALUES,
    ids=RAW_RPC_IDS,
)
def test_raw_rpc(payload, extra_namespaces, netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.raw_rpc(payload=payload, extra_namespaces=extra_namespaces))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=RAW_RPC_ARGNAMES,
    argvalues=RAW_RPC_ARGVALUES,
    ids=RAW_RPC_IDS,
)
async def test_raw_rpc_async(payload, extra_namespaces, netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.raw_rpc_async(payload=payload, extra_namespaces=extra_namespaces)

        netconf_assert_result(actual=actual)


RAW_RPC_CREATE_SUBSCRIPTION_ARGNAMES = ("payload",)
RAW_RPC_CREATE_SUBSCRIPTION_ARGVALUES = (
    (
        """<create-subscription xmlns="urn:ietf:params:xml:ns:netconf:notification:1.0">
         <stream>NETCONF</stream>
         <filter type="subtree">
           <counter-update xmlns="urn:boring:counter"/>
         </filter>
       </create-subscription>""",
    ),
)
RAW_RPC_CREATE_SUBSCRIPTION_IDS = ("simple",)


@pytest.mark.parametrize(
    argnames=RAW_RPC_CREATE_SUBSCRIPTION_ARGNAMES,
    argvalues=RAW_RPC_CREATE_SUBSCRIPTION_ARGVALUES,
    ids=RAW_RPC_CREATE_SUBSCRIPTION_IDS,
)
def test_raw_rpc_create_subscription(payload, netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.raw_rpc(payload=payload))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=RAW_RPC_CREATE_SUBSCRIPTION_ARGNAMES,
    argvalues=RAW_RPC_CREATE_SUBSCRIPTION_ARGVALUES,
    ids=RAW_RPC_CREATE_SUBSCRIPTION_IDS,
)
async def test_raw_rpc_create_subscription_async(payload, netconf, netconf_assert_result):
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


def test_get_next_notification(request, netconf):
    with netconf as n:
        _ = n.raw_rpc(
            payload="""
<create-subscription xmlns="urn:ietf:params:xml:ns:netconf:notification:1.0">
    <stream>NETCONF</stream>
    <filter type="subtree">
        <counter-update xmlns="urn:boring:counter"/>
    </filter>
</create-subscription>"""
        )

        if request.config.getoption("--record"):
            # boring counter updates every 3s; only when recording fixture ofc
            sleep(4)
        else:
            # just to ensure the background thread has read the notificaiton... important
            # because in unit tests we are literally reading 1 char at a time and ci has
            # slow compute :)
            sleep(1)

        actual = n.get_next_notification()

        assert actual is not None


def test_get_next_subscription(request):
    filename = request.node.originalname.removeprefix("test_").replace("_", "-")
    fixture_dir = f"{request.node.path.parent}/fixtures/netconf"
    f = f"{fixture_dir}/{filename}"

    if request.config.getoption("--record"):
        pytest.fail(
            "are you really sure? this is not using the clab setup, "
            "make sure you have either cisco sandbox or something else "
            "handy to re-record this test fixture",
        )

        session_options = SessionOptions(
            recorder_path=f,
        )
        transport_options = TransportBinOptions()
    else:
        session_options = SessionOptions(read_size=1, operation_max_search_depth=32)
        transport_options = TransportTestOptions(f=f)

    netconf = Netconf(
        # you may want to use: devnetsandboxiosxe.cisco.com -- have to login to get creds
        host="SETME",
        port=830,
        auth_options=AuthOptions(
            username="SETME",
            password="SETME",
        ),
        session_options=session_options,
        transport_options=transport_options,
    )

    with netconf as n:
        r = n.raw_rpc(
            payload="""
<establish-subscription xmlns="urn:ietf:params:xml:ns:yang:ietf-event-notifications" xmlns:yp="urn:ietf:params:xml:ns:yang:ietf-yang-push">
    <stream>yp:yang-push</stream>
    <yp:xpath-filter>/mdt-oper:mdt-oper-data/mdt-subscriptions</yp:xpath-filter>
    <yp:period>1000</yp:period>
</establish-subscription>"""
        )

        if request.config.getoption("--record"):
            # only when recording fixture ofc
            sleep(10)
        else:
            # just to ensure the background thread has read the notificaiton... important
            # because in unit tests we are literally reading 1 char at a time and ci has
            # slow compute :)
            sleep(1)

        actual = n.get_next_subscription(subscription_id=n.get_subscription_id(r.result))

        assert actual is not None
