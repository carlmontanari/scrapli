import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

import scrapli
from scrapli.driver import AsyncGenericDriver, GenericDriver
from scrapli.driver.core import (
    AsyncIOSXEDriver,
    AsyncJunosDriver,
    AsyncNXOSDriver,
    IOSXEDriver,
    JunosDriver,
    NXOSDriver,
)

from ..mock_devices.run import run
from ..test_data.devices import DEVICES, ENCRYPTED_PRIVATE_KEY, PRIVATE_KEY

TEST_DATA_DIR = f"{Path(scrapli.__file__).parents[1]}/tests/test_data"
SERVER_KEY = f"{TEST_DATA_DIR}/files/vrnetlab_key"

SYNC_DRIVERS = {
    "cisco_iosxe": IOSXEDriver,
    "cisco_nxos": NXOSDriver,
    "juniper_junos": JunosDriver,
    "generic_driver": GenericDriver,
}
ASYNC_DRIVERS = {
    "cisco_iosxe": AsyncIOSXEDriver,
    "cisco_nxos": AsyncNXOSDriver,
    "juniper_junos": AsyncJunosDriver,
    "generic_driver": AsyncGenericDriver,
}


@pytest.fixture(scope="session", autouse=True)
def mock_ssh_server_cisco_iosxe():
    with ThreadPoolExecutor(max_workers=1) as pool:
        loop = asyncio.new_event_loop()
        pool.submit(run, SERVER_KEY, "cisco_iosxe", loop)
        # short sleep -- seems the servers want a quick second to "wake up"
        time.sleep(0.25)
        # yield to let all the tests run, then we can deal w/ cleaning up the thread/loop
        yield
        loop.call_soon_threadsafe(loop.stop)


@pytest.fixture(scope="session", autouse=True)
def mock_ssh_server_cisco_nxos():
    with ThreadPoolExecutor(max_workers=1) as pool:
        loop = asyncio.new_event_loop()
        pool.submit(run, SERVER_KEY, "cisco_nxos", loop)
        # short sleep -- seems the servers want a quick second to "wake up"
        time.sleep(0.25)
        # yield to let all the tests run, then we can deal w/ cleaning up the thread/loop
        yield
        loop.call_soon_threadsafe(loop.stop)


@pytest.fixture(scope="session", autouse=True)
def mock_ssh_server_juniper_junos():
    with ThreadPoolExecutor(max_workers=1) as pool:
        loop = asyncio.new_event_loop()
        pool.submit(run, SERVER_KEY, "juniper_junos", loop)
        # short sleep -- seems the servers want a quick second to "wake up"
        time.sleep(0.25)
        # yield to let all the tests run, then we can deal w/ cleaning up the thread/loop
        yield
        loop.call_soon_threadsafe(loop.stop)


@pytest.fixture(scope="function")
def sync_generic_driver_conn():
    device = DEVICES["mock_cisco_iosxe"].copy()
    device.pop("auth_secondary")
    driver = SYNC_DRIVERS["generic_driver"]
    conn = driver(**device)
    yield conn
    if conn.isalive():
        conn.close()


@pytest.fixture(scope="function")
async def async_generic_driver_conn():
    device = DEVICES["mock_cisco_iosxe"].copy()
    device.pop("auth_secondary")
    driver = ASYNC_DRIVERS["generic_driver"]
    conn = driver(transport="asyncssh", **device)
    yield conn
    if conn.isalive():
        await conn.close()


@pytest.fixture(scope="function", params=["password", "key"])
def sync_conn_auth_type(request):
    # fixture to ensue we use password and key based auth with SystemSSHTransport
    yield request.param


@pytest.fixture(scope="function")
def sync_cisco_iosxe_conn(sync_conn_auth_type):
    device = DEVICES["mock_cisco_iosxe"].copy()
    if sync_conn_auth_type == "key":
        device.pop("auth_password")
        device["auth_private_key"] = PRIVATE_KEY
    driver = SYNC_DRIVERS["cisco_iosxe"]
    conn = driver(**device)
    yield conn
    if conn.isalive():
        conn.close()


@pytest.fixture(scope="function")
def sync_cisco_iosxe_conn_encrypted_key():
    device = DEVICES["mock_cisco_iosxe"].copy()
    device.pop("auth_password")
    device["auth_private_key"] = ENCRYPTED_PRIVATE_KEY
    driver = SYNC_DRIVERS["cisco_iosxe"]
    conn = driver(**device)
    yield conn
    if conn.isalive():
        conn.close()


@pytest.fixture(scope="function")
async def async_cisco_iosxe_conn():
    device = DEVICES["mock_cisco_iosxe"]
    driver = ASYNC_DRIVERS["cisco_iosxe"]
    conn = driver(transport="asyncssh", **device)
    yield conn
    if conn.isalive():
        await conn.close()


@pytest.fixture(scope="function")
def sync_cisco_nxos_conn(sync_conn_auth_type):
    device = DEVICES["mock_cisco_nxos"].copy()
    if sync_conn_auth_type == "key":
        device.pop("auth_password")
        device["auth_private_key"] = PRIVATE_KEY
    driver = SYNC_DRIVERS["cisco_nxos"]
    conn = driver(**device)
    yield conn
    if conn.isalive():
        conn.close()


@pytest.fixture(scope="function")
async def async_cisco_nxos_conn():
    device = DEVICES["mock_cisco_nxos"]
    driver = ASYNC_DRIVERS["cisco_nxos"]
    conn = driver(transport="asyncssh", **device)
    yield conn
    if conn.isalive():
        await conn.close()


@pytest.fixture(scope="function")
def sync_juniper_junos_conn(sync_conn_auth_type):
    device = DEVICES["mock_juniper_junos"].copy()
    if sync_conn_auth_type == "key":
        device.pop("auth_password")
        device["auth_private_key"] = PRIVATE_KEY
    driver = SYNC_DRIVERS["juniper_junos"]
    conn = driver(**device)
    yield conn
    if conn.isalive():
        conn.close()


@pytest.fixture(scope="function")
async def async_juniper_junos_conn():
    device = DEVICES["mock_juniper_junos"]
    driver = ASYNC_DRIVERS["juniper_junos"]
    conn = driver(transport="asyncssh", **device)
    yield conn
    if conn.isalive():
        await conn.close()
