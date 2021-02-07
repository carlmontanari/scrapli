import os
from pathlib import Path

import scrapli
from scrapli import AsyncDriver, Driver
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

TEST_DATA_PATH = f"{Path(scrapli.__file__).parents[1]}/tests/functional/test_data"

USERNAME = "vrnetlab"
PASSWORD = "VR-netlab9"
PRIVATE_KEY = f"{TEST_DATA_PATH}/vrnetlab_key"
INVALID_PRIVATE_KEY = f"{TEST_DATA_PATH}/__init__.py"
VROUTER_MODE = bool(os.environ.get("SCRAPLI_VROUTER", False))

DEVICES = {
    "cisco_iosxe": {
        "driver": IOSXEDriver,
        "async_driver": AsyncIOSXEDriver,
        "auth_username": USERNAME,
        "auth_password": PASSWORD,
        "auth_secondary": PASSWORD,
        "auth_strict_key": False,
        "host": "localhost" if VROUTER_MODE else "172.18.0.11",
        "port": 21022 if VROUTER_MODE else 22,
        "base_config": f"{TEST_DATA_PATH}/base_configs/cisco_iosxe",
    },
    "cisco_nxos": {
        "driver": NXOSDriver,
        "async_driver": AsyncNXOSDriver,
        "auth_username": USERNAME,
        "auth_password": PASSWORD,
        "auth_secondary": PASSWORD,
        "auth_strict_key": False,
        "host": "localhost" if VROUTER_MODE else "172.18.0.12",
        "port": 22022 if VROUTER_MODE else 22,
        "base_config": f"{TEST_DATA_PATH}/base_configs/cisco_nxos",
    },
    "cisco_iosxr": {
        "driver": IOSXRDriver,
        "async_driver": AsyncIOSXRDriver,
        "auth_username": USERNAME,
        "auth_password": PASSWORD,
        "auth_secondary": PASSWORD,
        "auth_strict_key": False,
        "host": "localhost" if VROUTER_MODE else "172.18.0.13",
        "port": 23022 if VROUTER_MODE else 22,
        "base_config": f"{TEST_DATA_PATH}/base_configs/cisco_iosxr",
    },
    "arista_eos": {
        "driver": EOSDriver,
        "async_driver": AsyncEOSDriver,
        "auth_username": USERNAME,
        "auth_password": PASSWORD,
        "auth_secondary": PASSWORD,
        "auth_strict_key": False,
        "host": "localhost" if VROUTER_MODE else "172.18.0.14",
        "port": 24022 if VROUTER_MODE else 22,
        "comms_ansi": True,
        "base_config": f"{TEST_DATA_PATH}/base_configs/arista_eos",
    },
    "juniper_junos": {
        "driver": JunosDriver,
        "async_driver": AsyncJunosDriver,
        "auth_username": USERNAME,
        "auth_password": PASSWORD,
        "auth_secondary": PASSWORD,
        "auth_strict_key": False,
        "host": "localhost" if VROUTER_MODE else "172.18.0.15",
        "port": 25022 if VROUTER_MODE else 22,
        "base_config": f"{TEST_DATA_PATH}/base_configs/juniper_junos",
    },
    "linux": {
        "driver": Driver,
        "async_driver": AsyncDriver,
        "auth_username": "root",
        "auth_password": "docker",
        "auth_strict_key": False,
        "host": "172.18.0.20",
        "comms_ansi": True,
        "comms_prompt_pattern": r"^linux:~#\s*$",
    },
}
