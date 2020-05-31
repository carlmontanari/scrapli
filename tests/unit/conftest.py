import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import asyncssh
import pytest

import scrapli
from scrapli.driver import AsyncGenericDriver, GenericDriver
from scrapli.driver.core import AsyncIOSXEDriver, IOSXEDriver

from ..test_data.devices import DEVICES, PRIVATE_KEY
from .mock_cisco_iosxe_server import IOSXEServer

TEST_DATA_DIR = f"{Path(scrapli.__file__).parents[1]}/tests/test_data"

SERVERS = {"cisco_iosxe": {"server": IOSXEServer, "port": 2211}}
SYNC_DRIVERS = {"cisco_iosxe": IOSXEDriver, "generic_driver": GenericDriver}
ASYNC_DRIVERS = {"cisco_iosxe": AsyncIOSXEDriver, "generic_driver": AsyncGenericDriver}

SERVER_LOOP = asyncio.new_event_loop()


async def _start_server(server_name: str):
    server = SERVERS.get(server_name).get("server")
    port = SERVERS.get(server_name).get("port")
    await asyncssh.create_server(
        server, "localhost", port, server_host_keys=[f"{TEST_DATA_DIR}/files/vrnetlab_key"]
    )


def start_server(server_name: str):
    try:
        SERVER_LOOP.run_until_complete(_start_server(server_name=server_name))
    except (OSError, asyncssh.Error) as exc:
        sys.exit(f"Error starting server {server_name}; Exception: {str(exc)}")

    SERVER_LOOP.run_forever()


@pytest.fixture(scope="session", autouse=True)
def mock_cisco_iosxe_server():
    pool = ThreadPoolExecutor(max_workers=1)
    pool.submit(start_server, "cisco_iosxe")
    # yield to let all the tests run, then we can deal w/ cleaning up the thread/loop
    yield
    SERVER_LOOP.call_soon_threadsafe(SERVER_LOOP.stop())
    pool.shutdown()


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


@pytest.fixture(scope="session", params=["password", "key"])
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
async def async_cisco_iosxe_conn():
    device = DEVICES["mock_cisco_iosxe"]
    driver = ASYNC_DRIVERS["cisco_iosxe"]
    conn = driver(transport="asyncssh", **device)
    yield conn
    if conn.isalive():
        await conn.close()
