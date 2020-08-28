import pytest

from scrapli.driver import GenericDriver

from .test_data.devices import DEVICES


@pytest.fixture(
    scope="class",
    params=["cisco_iosxe", "cisco_nxos", "cisco_iosxr", "arista_eos", "juniper_junos"],
)
def device_type(request):
    yield request.param


@pytest.fixture(scope="class", params=["system", "ssh2", "paramiko", "telnet"])
def transport(request):
    yield request.param


@pytest.fixture(scope="function", params=["asyncssh"])
def async_transport(request):
    yield request.param


@pytest.fixture(scope="class")
def nix_conn(transport):
    if transport == "telnet":
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
    if transport == "telnet":
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
    if device_type == "arista_eos" and transport == "ssh2":
        pytest.skip(
            "SSH2 (on pypi) doesn't support keyboard interactive auth, skipping ssh2 for arista_eos testing"
        )

    device = DEVICES[device_type].copy()
    driver = device.pop("driver")
    device.pop("base_config")
    device.pop("async_driver")

    timeout_transport = 5
    timeout_ops = 5
    if device_type == "juniper_junos" or device_type == "cisco_iosxr":
        # commits on vsrx take one whole eternity... and iosxr container is just flakey
        timeout_transport = 30
        timeout_ops = 30

    port = 22
    if transport == "telnet":
        port = 23

    conn = driver(
        **device,
        port=port,
        transport=transport,
        timeout_socket=5,
        timeout_transport=timeout_transport,
        timeout_ops=timeout_ops,
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

    timeout_transport = 5
    timeout_ops = 5
    if device_type == "juniper_junos" or device_type == "cisco_iosxr":
        # commits on vsrx take one whole eternity... and iosxr container is just flakey
        timeout_transport = 30
        timeout_ops = 30

    async_conn = driver(
        **device,
        port=22,
        transport=async_transport,
        timeout_socket=5,
        timeout_transport=timeout_transport,
        timeout_ops=timeout_ops,
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

    port = 22
    if transport == "telnet":
        port = 23

    iosxe_conn = driver(
        **device,
        port=port,
        transport=transport,
        timeout_socket=5,
    )
    iosxe_conn.open()
    return iosxe_conn


@pytest.fixture(scope="class")
def iosxr_conn(transport):
    device = DEVICES["cisco_iosxr"].copy()
    driver = device.pop("driver")
    device.pop("base_config")
    device.pop("async_driver")

    timeout_transport = 30
    timeout_ops = 30

    port = 22
    if transport == "telnet":
        port = 23

    conn = driver(
        **device,
        port=port,
        transport=transport,
        timeout_socket=5,
        timeout_transport=timeout_transport,
        timeout_ops=timeout_ops,
    )
    conn.open()
    return conn


@pytest.fixture(scope="class")
def junos_conn(transport):
    device = DEVICES["juniper_junos"].copy()
    driver = device.pop("driver")
    device.pop("base_config")
    device.pop("async_driver")

    timeout_transport = 30
    timeout_ops = 30

    port = 22
    if transport == "telnet":
        port = 23

    conn = driver(
        **device,
        port=port,
        transport=transport,
        timeout_socket=5,
        timeout_transport=timeout_transport,
        timeout_ops=timeout_ops,
    )
    conn.open()
    return conn


@pytest.fixture(scope="class")
def eos_conn(transport):
    if transport == "ssh2":
        pytest.skip(
            "SSH2 (on pypi) doesn't support keyboard interactive auth, skipping ssh2 for arista_eos testing"
        )
    device = DEVICES["arista_eos"].copy()
    driver = device.pop("driver")
    device.pop("base_config")
    device.pop("async_driver")

    port = 22
    if transport == "telnet":
        port = 23

    conn = driver(
        **device,
        port=port,
        transport=transport,
        timeout_socket=5,
    )
    conn.open()
    return conn


@pytest.fixture(scope="class")
def nxos_conn(transport):
    device = DEVICES["cisco_nxos"].copy()
    driver = device.pop("driver")
    device.pop("base_config")
    device.pop("async_driver")

    port = 22
    if transport == "telnet":
        port = 23

    conn = driver(
        **device,
        port=port,
        transport=transport,
        timeout_socket=5,
    )
    conn.open()
    return conn
