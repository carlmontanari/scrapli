import os

import pytest
from napalm import get_network_driver

from .test_data.devices import DEVICES

NAPALM_DEVICE_TYPE_MAP = {
    "cisco_iosxe": "ios",
    "cisco_nxos": "nxos",
    "cisco_iosxr": "iosxr",
    "arista_eos": "eos",
    "juniper_junos": "junos",
}


@pytest.fixture(scope="session", autouse=True)
def prepare_device(request):
    if os.getenv("SCRAPLI_NO_SETUP", "").lower() == "true":
        return

    test_devices = []
    for test in request.node.items:
        # for linux testing we wont have a device_type to test against, and obviously dont need
        #  napalm to push configs!
        if "device_type" not in test.callspec.params:
            continue
        test_devices.append(test.callspec.params["device_type"])
    test_devices = set(test_devices)

    # push base config via napalm to ensure consistent testing experience
    for device in test_devices:
        base_config = DEVICES[device]["base_config"]

        napalm_device_type = NAPALM_DEVICE_TYPE_MAP.get(device)
        napalm_driver = get_network_driver(napalm_device_type)
        napalm_conn = napalm_driver(
            hostname=DEVICES[device]["host"],
            username=DEVICES[device]["auth_username"],
            password=DEVICES[device]["auth_password"],
        )
        napalm_conn.open()
        napalm_conn.load_replace_candidate(filename=base_config)
        napalm_conn.commit_config()
        napalm_conn.close()


# @pytest.fixture(scope="class", params=["cisco_iosxe", "cisco_nxos", "cisco_iosxr", "arista_eos", "juniper_junos"])
@pytest.fixture(
    scope="class",
    params=["cisco_iosxe", "cisco_nxos", "cisco_iosxr", "arista_eos", "juniper_junos"],
)
def device_type(request):
    yield request.param


# @pytest.fixture(scope="class", params=["system", "ssh2", "paramiko", "telnet"])
@pytest.fixture(scope="class", params=["system", "ssh2", "paramiko", "telnet"])
def transport(request):
    yield request.param


@pytest.fixture(scope="class")
def nix_conn(transport):
    if transport == "telnet":
        pytest.skip("skipping telnet for linux hosts")

    device = DEVICES["linux"].copy()
    driver = device.pop("driver")

    conn = driver(**device, transport=transport,)
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

    timeout_transport = 5
    timeout_ops = 5
    if device_type == "juniper_junos":
        # commits on vsrx take one whole eternity...
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
