import pytest

from scrapli.driver import GenericDriver

TIMEOUT_SOCKET = 10
TIMEOUT_TRANSPORT = 10
TIMEOUT_OPS = 30
TELNET_TRANSPORTS = (
    "telnet",
    "asynctelnet",
)


@pytest.fixture(scope="session")
def real_invalid_ssh_key_path(test_data_path):
    return f"{test_data_path}/files/invalid_key"


@pytest.fixture(scope="session")
def real_valid_ssh_key_path(test_data_path):
    return f"{test_data_path}/files/scrapli_key"


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
def nix_conn(test_devices_dict, transport):
    if transport in TELNET_TRANSPORTS:
        pytest.skip("skipping telnet for linux hosts")

    device = test_devices_dict["linux"].copy()
    driver = device.pop("driver")
    device.pop("async_driver")

    conn = driver(
        **device,
        transport=transport,
    )
    conn.open()
    return conn


@pytest.fixture(scope="class")
def nix_conn_generic(test_devices_dict, transport):
    if transport in TELNET_TRANSPORTS:
        pytest.skip("skipping telnet for linux hosts")

    device = test_devices_dict["linux"].copy()
    device.pop("driver")
    device.pop("async_driver")

    conn = GenericDriver(
        **device,
        transport=transport,
    )
    conn.open()
    return conn


@pytest.fixture(scope="class")
def conn(test_devices_dict, device_type, transport):
    device = test_devices_dict[device_type].copy()
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
async def async_conn(test_devices_dict, device_type, async_transport):
    device = test_devices_dict[device_type].copy()
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
def iosxe_conn(test_devices_dict, transport):
    device = test_devices_dict["cisco_iosxe"].copy()
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
def iosxr_conn(test_devices_dict, transport):
    device = test_devices_dict["cisco_iosxr"].copy()
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
def junos_conn(test_devices_dict, transport):
    device = test_devices_dict["juniper_junos"].copy()
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
def eos_conn(test_devices_dict, transport):
    device = test_devices_dict["arista_eos"].copy()
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
def nxos_conn(test_devices_dict, transport):
    device = test_devices_dict["cisco_nxos"].copy()
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
