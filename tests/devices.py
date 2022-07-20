import os
import sys
from pathlib import Path
from typing import Tuple

import scrapli
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

TEST_DATA_PATH = f"{Path(scrapli.__file__).parents[1]}/tests/test_data"

PRIVATE_KEY = f"{TEST_DATA_PATH}/scrapli_key"
INVALID_PRIVATE_KEY = f"{TEST_DATA_PATH}/__init__.py"


def get_env_or_default(key: str, default: str) -> str:
    return os.getenv(key, default)


def get_functional_host_ip_port_linux_or_remote(platform: str) -> Tuple[str, int]:
    plats = {
        "cisco_iosxe": ("172.20.20.11", 22),
        "cisco_iosxr": ("172.20.20.12", 22),
        "cisco_nxos": ("172.20.20.13", 22),
        "arista_eos": ("172.20.20.14", 22),
        "juniper_junos": ("172.20.20.15", 22),
    }

    return get_env_or_default(f"SCRAPLI_{platform.upper()}_HOST", plats[platform][0]), int(
        get_env_or_default(f"SCRAPLI_{platform.upper()}_PORT", plats[platform][1])
    )


def get_functional_host_ip_port(platform: str) -> Tuple[str, int]:
    if not get_env_or_default("SCRAPLI_HOST_FWD", ""):
        return get_functional_host_ip_port_linux_or_remote(platform)

    # otherwise we are running on darwin w/ local boxen w/ nat
    host = "localhost"

    if platform == "cisco_iosxe":
        return host, 21022
    if platform == "cisco_iosxr":
        return host, 22022
    if platform == "cisco_nxos":
        return host, 23022
    if platform == "arista_eos":
        return host, 24022
    if platform == "juniper_junos":
        return host, 25022


def get_functional_host_user_pass(platform: str) -> Tuple[str, str]:
    user = "admin"
    pwd = "admin"

    if platform == "cisco_iosxe":
        return user, pwd
    if platform == "cisco_iosxr":
        return "clab", "clab@123"
    if platform == "cisco_nxos":
        return user, pwd
    if platform == "arista_eos":
        return user, pwd
    if platform == "juniper_junos":
        return user, "admin@123"


DEVICES = {
    "cisco_iosxe": {
        "driver": IOSXEDriver,
        "async_driver": AsyncIOSXEDriver,
        "auth_strict_key": False,
        "base_config": f"{TEST_DATA_PATH}/base_configs/cisco_iosxe",
        "transport_options": {
            "open_cmd": [
                "-o",
                "KexAlgorithms=+diffie-hellman-group-exchange-sha1,diffie-hellman-group14-sha1",
            ]
        },
    },
    "cisco_nxos": {
        "driver": NXOSDriver,
        "async_driver": AsyncNXOSDriver,
        "auth_strict_key": False,
        "base_config": f"{TEST_DATA_PATH}/base_configs/cisco_nxos",
    },
    "cisco_iosxr": {
        "driver": IOSXRDriver,
        "async_driver": AsyncIOSXRDriver,
        "auth_strict_key": False,
        "base_config": f"{TEST_DATA_PATH}/base_configs/cisco_iosxr",
    },
    "arista_eos": {
        "driver": EOSDriver,
        "async_driver": AsyncEOSDriver,
        "auth_strict_key": False,
        "base_config": f"{TEST_DATA_PATH}/base_configs/arista_eos",
    },
    "juniper_junos": {
        "driver": JunosDriver,
        "async_driver": AsyncJunosDriver,
        "auth_strict_key": False,
        "base_config": f"{TEST_DATA_PATH}/base_configs/juniper_junos",
    },
}


def render_devices():
    for platform in ("cisco_iosxe", "cisco_iosxr", "cisco_nxos", "arista_eos", "juniper_junos"):
        host, port = get_functional_host_ip_port(platform)
        user, pwd = get_functional_host_user_pass(platform)

        DEVICES[platform]["host"] = host
        DEVICES[platform]["port"] = port
        DEVICES[platform]["auth_username"] = user
        DEVICES[platform]["auth_password"] = pwd

        # always boxen as it should only matter for iosxe and will have been set *by* boxen in
        # most cases
        DEVICES[platform]["auth_secondary"] = "b0x3N-b0x3N"


render_devices()
