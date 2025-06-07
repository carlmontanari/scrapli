from copy import copy

import pytest

from scrapli.netconf import DatastoreType

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
    (
        """
        <system xmlns="urn:dummy:actions">
            <reboot>
                <delay>5</delay>
            </reboot>
        </system>
        """,
        "netopeer",
        "ssh2",
    ),
)
ACTION_IDS = (
    "netopeer-bin-simple",
    "netopeer-ssh2-simple",
)


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


CANCEL_COMMIT_ARGNAMES = (
    "platform",
    "transport",
)
CANCEL_COMMIT_ARGVALUES = (
    (
        "netopeer",
        "bin",
    ),
    (
        "netopeer",
        "ssh2",
    ),
)
CANCEL_COMMIT_IDS = (
    "netopeer-bin-simple",
    "netopeer-ssh2-simple",
)


@pytest.mark.parametrize(
    argnames=CANCEL_COMMIT_ARGNAMES,
    argvalues=CANCEL_COMMIT_ARGVALUES,
    ids=CANCEL_COMMIT_IDS,
)
def test_cancel_commit(netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.cancel_commit())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=CANCEL_COMMIT_ARGNAMES,
    argvalues=CANCEL_COMMIT_ARGVALUES,
    ids=CANCEL_COMMIT_IDS,
)
async def test_cancel_commit_async(netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.cancel_commit_async()

        netconf_assert_result(actual=actual)


CLOSE_SESSION_ARGNAMES = (
    "platform",
    "transport",
)
CLOSE_SESSION_ARGVALUES = (
    (
        "netopeer",
        "bin",
    ),
    (
        "netopeer",
        "ssh2",
    ),
)
CLOSE_SESSION_IDS = (
    "netopeer-bin-simple",
    "netopeer-ssh2-simple",
)


@pytest.mark.parametrize(
    argnames=CLOSE_SESSION_ARGNAMES,
    argvalues=CLOSE_SESSION_ARGVALUES,
    ids=CLOSE_SESSION_IDS,
)
def test_close_session(netconf, netconf_assert_result):
    netconf.open()
    netconf_assert_result(actual=netconf.close_session())
    netconf._free()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=CLOSE_SESSION_ARGNAMES,
    argvalues=CLOSE_SESSION_ARGVALUES,
    ids=CLOSE_SESSION_IDS,
)
async def test_close_session_async(netconf, netconf_assert_result):
    await netconf.open_async()
    actual = await netconf.close_session_async()
    netconf_assert_result(actual=actual)
    netconf._free()


COMMIT_ARGNAMES = (
    "platform",
    "transport",
)
COMMIT_ARGVALUES = (
    (
        "netopeer",
        "bin",
    ),
    (
        "netopeer",
        "ssh2",
    ),
)
COMMIT_IDS = (
    "netopeer-bin-simple",
    "netopeer-ssh2-simple",
)


@pytest.mark.parametrize(
    argnames=COMMIT_ARGNAMES,
    argvalues=COMMIT_ARGVALUES,
    ids=COMMIT_IDS,
)
def test_commit(netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.commit())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=COMMIT_ARGNAMES,
    argvalues=COMMIT_ARGVALUES,
    ids=COMMIT_IDS,
)
async def test_commit_async(netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.commit_async()

        netconf_assert_result(actual=actual)


COPY_CONFIG_ARGNAMES = (
    "platform",
    "transport",
)
COPY_CONFIG_ARGVALUES = (
    (
        "netopeer",
        "bin",
    ),
    (
        "netopeer",
        "ssh2",
    ),
)
COPY_CONFIG_IDS = (
    "netopeer-bin-simple",
    "netopeer-ssh2-simple",
)


@pytest.mark.parametrize(
    argnames=COPY_CONFIG_ARGNAMES,
    argvalues=COPY_CONFIG_ARGVALUES,
    ids=COPY_CONFIG_IDS,
)
def test_copy_config(netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.copy_config())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=COPY_CONFIG_ARGNAMES,
    argvalues=COPY_CONFIG_ARGVALUES,
    ids=COPY_CONFIG_IDS,
)
async def test_copy_config_async(netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.copy_config_async()

        netconf_assert_result(actual=actual)


DELETE_CONFIG_ARGNAMES = (
    "target",
    "platform",
    "transport",
)
DELETE_CONFIG_ARGVALUES = (
    (
        DatastoreType.STARTUP,
        "netopeer",
        "bin",
    ),
    (
        DatastoreType.STARTUP,
        "netopeer",
        "ssh2",
    ),
)
DELETE_CONFIG_IDS = (
    "netopeer-bin-simple",
    "netopeer-ssh2-simple",
)


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


DISCARD_ARGNAMES = (
    "platform",
    "transport",
)
DISCARD_ARGVALUES = (
    (
        "netopeer",
        "bin",
    ),
    (
        "netopeer",
        "ssh2",
    ),
)
DISCARD_IDS = (
    "netopeer-bin-simple",
    "netopeer-ssh2-simple",
)


@pytest.mark.parametrize(
    argnames=DISCARD_ARGNAMES,
    argvalues=DISCARD_ARGVALUES,
    ids=DISCARD_IDS,
)
def test_discard(netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.discard())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=DISCARD_ARGNAMES,
    argvalues=DISCARD_ARGVALUES,
    ids=DISCARD_IDS,
)
async def test_discard_async(netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.discard_async()

        netconf_assert_result(actual=actual)


EDIT_CONFIG_ARGNAMES = (
    "config",
    "platform",
    "transport",
)
EDIT_CONFIG_ARGVALUES = (
    (
        "",
        "netopeer",
        "bin",
    ),
    (
        "",
        "netopeer",
        "ssh2",
    ),
)
EDIT_CONFIG_IDS = (
    "netopeer-bin-simple",
    "netopeer-ssh2-simple",
)


@pytest.mark.parametrize(
    argnames=EDIT_CONFIG_ARGNAMES,
    argvalues=EDIT_CONFIG_ARGVALUES,
    ids=EDIT_CONFIG_IDS,
)
def test_edit_config(config, netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.edit_config(config=config))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=EDIT_CONFIG_ARGNAMES,
    argvalues=EDIT_CONFIG_ARGVALUES,
    ids=EDIT_CONFIG_IDS,
)
async def test_edit_config_async(config, netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.edit_config_async(config=config)

        netconf_assert_result(actual=actual)


EDIT_DATA_ARGNAMES = (
    "content",
    "platform",
    "transport",
)
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
        "netopeer",
        "bin",
    ),
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
        "netopeer",
        "ssh2",
    ),
)
EDIT_DATA_IDS = (
    "netopeer-bin-simple",
    "netopeer-ssh2-simple",
)


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


GET_CONFIG_ARGNAMES = (
    "platform",
    "transport",
)
GET_CONFIG_ARGVALUES = (
    (
        "netopeer",
        "bin",
    ),
    (
        "netopeer",
        "ssh2",
    ),
)
GET_CONFIG_IDS = (
    "netopeer-bin-simple",
    "netopeer-ssh2-simple",
)


@pytest.mark.parametrize(
    argnames=GET_CONFIG_ARGNAMES,
    argvalues=GET_CONFIG_ARGVALUES,
    ids=GET_CONFIG_IDS,
)
def test_get_config(netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.get_config())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=GET_CONFIG_ARGNAMES,
    argvalues=GET_CONFIG_ARGVALUES,
    ids=GET_CONFIG_IDS,
)
async def test_get_config_async(netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.get_config_async()

        netconf_assert_result(actual=actual)


GET_DATA_ARGNAMES = (
    "filter_",
    "platform",
    "transport",
)
GET_DATA_ARGVALUES = (
    (
        '<system xmlns="urn:some:data"></system>',
        "netopeer",
        "bin",
    ),
    (
        '<system xmlns="urn:some:data"></system>',
        "netopeer",
        "ssh2",
    ),
)
GET_DATA_IDS = (
    "netopeer-bin-simple",
    "netopeer-ssh2-simple",
)


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


GET_SCHEMA_ARGNAMES = (
    "identifier",
    "platform",
    "transport",
)
GET_SCHEMA_ARGVALUES = (
    (
        "ietf-yang-types",
        "netopeer",
        "bin",
    ),
    (
        "ietf-yang-types",
        "netopeer",
        "ssh2",
    ),
)
GET_SCHEMA_IDS = (
    "netopeer-bin-simple",
    "netopeer-ssh2-simple",
)


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


GET_ARGNAMES = (
    "filter_",
    "platform",
    "transport",
)
GET_ARGVALUES = (
    (
        "",
        "netopeer",
        "bin",
    ),
    (
        "",
        "netopeer",
        "ssh2",
    ),
    (
        "<interfaces><interface><name>Management0</name><state></state></interface></interfaces>",
        "netopeer",
        "bin",
    ),
    (
        "<interfaces><interface><name>Management0</name><state></state></interface></interfaces>",
        "netopeer",
        "ssh2",
    ),
)
GET_IDS = (
    "netopeer-bin-simple",
    "netopeer-ssh2-simple",
    "netopeer-bin-filtered",
    "netopeer-ssh2-filtered",
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


KILL_SESSION_ARGNAMES = (
    "platform",
    "transport",
)
KILL_SESSION_ARGVALUES = (
    (
        "nokia_srl",
        "bin",
    ),
    (
        "nokia_srl",
        "ssh2",
    ),
)
KILL_SESSION_IDS = (
    "nokia-srl-bin-simple",
    "nokia-srl-ssh2-simple",
)


@pytest.mark.parametrize(
    argnames=KILL_SESSION_ARGNAMES,
    argvalues=KILL_SESSION_ARGVALUES,
    ids=KILL_SESSION_IDS,
)
def test_kill_session(netconf, netconf_assert_result):
    # had some issues with (maybe my jank patch) netopeer -- it didnt wanna let me open two
    # connections at the same time and i never looked closer... so this is just tested with srl
    netconf_2 = copy(netconf)

    with netconf as n:
        # do not forget to free the killed coonnection otherwise we would end up SEGFAULT'ing when
        # the ffi driver tries to call logger functions and the logger will have already been gc'd
        # in python side (the n2 connection will eventually timeout and that will have happened
        # outside scope of this func so python will have gc'd, so when it tries to log the
        # warn/crit about going down thats where we would segfault)
        netconf_2.open()
        netconf_assert_result(actual=n.kill_session(session_id=netconf_2.session_id))
        netconf_2._free()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=KILL_SESSION_ARGNAMES,
    argvalues=KILL_SESSION_ARGVALUES,
    ids=KILL_SESSION_IDS,
)
async def test_kill_session_async(netconf, netconf_assert_result):
    netconf_2 = copy(netconf)

    async with netconf as n:
        await netconf_2.open_async()
        actual = await n.kill_session_async(session_id=netconf_2.session_id)
        netconf_2._free()

    netconf_assert_result(actual=actual)


LOCK_ARGNAMES = (
    "platform",
    "transport",
)
LOCK_ARGVALUES = (
    (
        "netopeer",
        "bin",
    ),
    (
        "netopeer",
        "ssh2",
    ),
)
LOCK_IDS = (
    "netopeer-bin-simple",
    "netopeer-ssh2-simple",
)


@pytest.mark.parametrize(
    argnames=LOCK_ARGNAMES,
    argvalues=LOCK_ARGVALUES,
    ids=LOCK_IDS,
)
def test_lock(netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.lock())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=LOCK_ARGNAMES,
    argvalues=LOCK_ARGVALUES,
    ids=LOCK_IDS,
)
async def test_lock_async(netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.lock_async()

        netconf_assert_result(actual=actual)


UNLOCK_ARGNAMES = (
    "platform",
    "transport",
)
UNLOCK_ARGVALUES = (
    (
        "netopeer",
        "bin",
    ),
    (
        "netopeer",
        "ssh2",
    ),
)
UNLOCK_IDS = (
    "netopeer-bin-simple",
    "netopeer-ssh2-simple",
)


@pytest.mark.parametrize(
    argnames=UNLOCK_ARGNAMES,
    argvalues=UNLOCK_ARGVALUES,
    ids=UNLOCK_IDS,
)
def test_unlock(netconf, netconf_assert_result):
    with netconf as n:
        n.lock()
        netconf_assert_result(actual=n.unlock())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=UNLOCK_ARGNAMES,
    argvalues=UNLOCK_ARGVALUES,
    ids=UNLOCK_IDS,
)
async def test_unlock_async(netconf, netconf_assert_result):
    async with netconf as n:
        await n.lock_async()
        actual = await n.unlock_async()

        netconf_assert_result(actual=actual)


RAW_RPC_ARGNAMES = (
    "payload",
    "platform",
    "transport",
)
RAW_RPC_ARGVALUES = (
    (
        "<get-config><source><running/></source></get-config>",
        "netopeer",
        "bin",
    ),
    (
        "<get-config><source><running/></source></get-config>",
        "netopeer",
        "ssh2",
    ),
)
RAW_RPC_IDS = (
    "netopeer-bin-simple",
    "netopeer-ssh2-simple",
)


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


RAW_RPC_CREATE_SUBSCRIPTION_ARGNAMES = (
    "payload",
    "platform",
    "transport",
)
RAW_RPC_CREATE_SUBSCRIPTION_ARGVALUES = (
    (
        """<create-subscription xmlns="urn:ietf:params:xml:ns:netconf:notification:1.0">
     <stream>NETCONF</stream>
     <filter type="subtree">
       <counter-update xmlns="urn:boring:counter"/>
     </filter>
   </create-subscription>""",
        "netopeer",
        "bin",
    ),
    (
        """<create-subscription xmlns="urn:ietf:params:xml:ns:netconf:notification:1.0">
         <stream>NETCONF</stream>
         <filter type="subtree">
           <counter-update xmlns="urn:boring:counter"/>
         </filter>
       </create-subscription>""",
        "netopeer",
        "ssh2",
    ),
)
RAW_RPC_CREATE_SUBSCRIPTION_IDS = (
    "netopeer-bin-simple",
    "netopeer-ssh2-simple",
)


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


VALIDATE_ARGNAMES = (
    "platform",
    "transport",
)
VALIDATE_ARGVALUES = (
    (
        "netopeer",
        "bin",
    ),
    (
        "netopeer",
        "ssh2",
    ),
)
VALIDATE_IDS = (
    "netopeer-bin-simple",
    "netopeer-ssh2-simple",
)


@pytest.mark.parametrize(
    argnames=VALIDATE_ARGNAMES,
    argvalues=VALIDATE_ARGVALUES,
    ids=VALIDATE_IDS,
)
def test_validate(netconf, netconf_assert_result):
    with netconf as n:
        netconf_assert_result(actual=n.validate())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=VALIDATE_ARGNAMES,
    argvalues=VALIDATE_ARGVALUES,
    ids=VALIDATE_IDS,
)
async def test_validate_async(netconf, netconf_assert_result):
    async with netconf as n:
        actual = await n.validate_async()

        netconf_assert_result(actual=actual)
