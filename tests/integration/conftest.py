import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from scrapli.driver.core import (
    AsyncEOSDriver,
    AsyncIOSXEDriver,
    AsyncIOSXRDriver,
    AsyncJunosDriver,
    AsyncNXOSDriver,
    EOSDriver,
    IOSXEDriver,
    IOSXRDriver,
    JunosDriver,
    NXOSDriver,
)

from .run import sync_run_servers

DEVICES = {
    "common": {
        "host": "localhost",
        "auth_username": "scrapli",
        "auth_password": "scrapli",
        "auth_secondary": "scrapli",
        "auth_strict_key": False,
    },
    "cisco_iosxe": {
        "driver": IOSXEDriver,
        "async_driver": AsyncIOSXEDriver,
        "port": 2221,
    },
    "cisco_nxos": {
        "driver": NXOSDriver,
        "async_driver": AsyncNXOSDriver,
        "port": 2222,
    },
    "cisco_iosxr": {
        "driver": IOSXRDriver,
        "async_driver": AsyncIOSXRDriver,
        "port": 2223,
    },
    "arista_eos": {
        "driver": EOSDriver,
        "async_driver": AsyncEOSDriver,
        "port": 2224,
    },
    "juniper_junos": {
        "driver": JunosDriver,
        "async_driver": AsyncJunosDriver,
        "port": 2225,
    },
}


@pytest.fixture(scope="module", autouse=True)
def mock_ssh_servers():
    with ThreadPoolExecutor(max_workers=1) as pool:
        loop = asyncio.new_event_loop()
        pool.submit(sync_run_servers, loop)
        time.sleep(1)
        # yield to let all the tests run, then we can deal w/ cleaning up the thread/loop
        # we need to have this scoped to module so it starts/stops just for integration tests
        yield
        loop.call_soon_threadsafe(loop.stop)
    # seems a little sleep before and after starting/stopping makes things a little smoother...
    time.sleep(1)


@pytest.fixture(
    scope="function",
    params=["cisco_iosxe", "cisco_nxos", "cisco_iosxr", "arista_eos", "juniper_junos"],
)
def device_type(request):
    yield request.param


@pytest.fixture(scope="function", params=["system", "ssh2", "paramiko"])
def transport(request):
    yield request.param


@pytest.fixture(scope="function")
def sync_conn(device_type, transport):
    driver = DEVICES[device_type]["driver"]
    port = DEVICES[device_type]["port"]

    if transport == "telnet":
        port = port + 1

    conn = driver(
        port=port,
        transport=transport,
        **DEVICES["common"],
    )
    conn.open()
    yield conn
    conn.close()
