import pytest

from scrapli.driver import GenericDriver

from .test_data.devices import DEVICES

TIMEOUT_SOCKET = 10
TIMEOUT_TRANSPORT = 10
TIMEOUT_OPS = 30
TELNET_TRANSPORTS = (
    "telnet",
    "asynctelnet",
)


@pytest.fixture(
    scope="class",
    params=["cisco_iosxe", "cisco_nxos", "cisco_iosxr", "arista_eos", "juniper_junos"],
)
def device_type(request):
    yield request.param


@pytest.fixture(scope="class", params=["system", "ssh2", "paramiko", "telnet"])
def transport(request):
    yield request.param


@pytest.fixture(scope="function", params=["asyncssh", "asynctelnet"])
def async_transport(request):
    yield request.param


@pytest.fixture(scope="class")
def nix_conn(transport):
    if transport in TELNET_TRANSPORTS:
        pytest.skip("skipping telnet for linux hosts")

    device = DEVICES["linux"].copy()
    driver = device.pop("driver")
    device.pop("async_driver")

    conn = driver(
        **device,
        transport=transport,
    )
    conn.open()
    return conn


@pytest.fixture(scope="class")
def nix_conn_generic(transport):
    if transport in TELNET_TRANSPORTS:
        pytest.skip("skipping telnet for linux hosts")

    device = DEVICES["linux"].copy()
    device.pop("driver")
    device.pop("async_driver")

    conn = GenericDriver(
        **device,
        transport=transport,
    )
    conn.open()
    return conn


@pytest.fixture(scope="class")
def conn(device_type, transport):
    device = DEVICES[device_type].copy()
    driver = device.pop("driver")
    device.pop("base_config")
    device.pop("async_driver")

    port = device.pop("port")
    if transport in TELNET_TRANSPORTS:
        port = port + 1

    conn = driver(
        **device,
        port=port,
        transport=transport,
        timeout_socket=TIMEOUT_SOCKET,
        timeout_transport=TIMEOUT_TRANSPORT,
        timeout_ops=TIMEOUT_OPS,
    )
    conn.open()
    return conn


# scoping to function is probably dumb but dont have to screw around with which event loop is what this way
@pytest.fixture(scope="function")
async def async_conn(device_type, async_transport):
    device = DEVICES[device_type].copy()
    driver = device.pop("async_driver")
    device.pop("base_config")
    device.pop("driver")

    port = device.pop("port")
    if async_transport in TELNET_TRANSPORTS:
        port = port + 1

    async_conn = driver(
        **device,
        port=port,
        transport=async_transport,
        timeout_socket=TIMEOUT_SOCKET,
        timeout_transport=TIMEOUT_TRANSPORT,
        timeout_ops=TIMEOUT_OPS,
    )
    await async_conn.open()
    # yield then ensure we close since we are not persisting connections between tests for now
    yield async_conn
    if async_conn.isalive():
        await async_conn.close()


@pytest.fixture(scope="class")
def iosxe_conn(transport):
    device = DEVICES["cisco_iosxe"].copy()
    driver = device.pop("driver")
    device.pop("base_config")
    device.pop("async_driver")

    port = device.pop("port")
    if transport in TELNET_TRANSPORTS:
        port = port + 1

    iosxe_conn = driver(
        **device,
        port=port,
        transport=transport,
        timeout_socket=TIMEOUT_SOCKET,
    )
    iosxe_conn.open()
    return iosxe_conn


@pytest.fixture(scope="class")
def iosxr_conn(transport):
    device = DEVICES["cisco_iosxr"].copy()
    driver = device.pop("driver")
    device.pop("base_config")
    device.pop("async_driver")

    port = device.pop("port")
    if transport in TELNET_TRANSPORTS:
        port = port + 1

    conn = driver(
        **device,
        port=port,
        transport=transport,
        timeout_socket=TIMEOUT_SOCKET,
        timeout_transport=TIMEOUT_TRANSPORT,
        timeout_ops=TIMEOUT_OPS,
    )
    conn.open()
    return conn


@pytest.fixture(scope="class")
def junos_conn(transport):
    device = DEVICES["juniper_junos"].copy()
    driver = device.pop("driver")
    device.pop("base_config")
    device.pop("async_driver")

    port = device.pop("port")
    if transport in TELNET_TRANSPORTS:
        port = port + 1

    conn = driver(
        **device,
        port=port,
        transport=transport,
        timeout_socket=TIMEOUT_SOCKET,
        timeout_transport=TIMEOUT_TRANSPORT,
        timeout_ops=TIMEOUT_OPS,
    )
    conn.open()
    return conn


@pytest.fixture(scope="class")
def eos_conn(transport):
    device = DEVICES["arista_eos"].copy()
    driver = device.pop("driver")
    device.pop("base_config")
    device.pop("async_driver")

    port = device.pop("port")
    if transport in TELNET_TRANSPORTS:
        port = port + 1

    conn = driver(
        **device,
        port=port,
        transport=transport,
        timeout_socket=TIMEOUT_SOCKET,
    )
    conn.open()
    return conn


@pytest.fixture(scope="class")
def nxos_conn(transport):
    device = DEVICES["cisco_nxos"].copy()
    driver = device.pop("driver")
    device.pop("base_config")
    device.pop("async_driver")

    port = device.pop("port")
    if transport in TELNET_TRANSPORTS:
        port = port + 1

    conn = driver(
        **device,
        port=port,
        transport=transport,
        timeout_socket=TIMEOUT_SOCKET,
    )
    conn.open()
    return conn
