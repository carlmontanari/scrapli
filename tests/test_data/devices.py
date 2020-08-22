from pathlib import Path

import scrapli

TEST_DATA_PATH = f"{Path(scrapli.__file__).parents[1]}/tests/test_data"

FUNCTIONAL_USERNAME = "vrnetlab"
FUNCTIONAL_PASSWORD = "VR-netlab9"
FUNCTIONAL_PASSPHRASE = "scrapli"
PRIVATE_KEY = f"{TEST_DATA_PATH}/files/vrnetlab_key"
ENCRYPTED_PRIVATE_KEY = f"{TEST_DATA_PATH}/files/vrnetlab_key_encrypted"
INVALID_PRIVATE_KEY = f"{TEST_DATA_PATH}/files/invalid_key"
MOCK_USERNAME = "scrapli"
MOCK_PASSWORD = "scrapli"
MOCK_PASSPHRASE = FUNCTIONAL_PASSPHRASE

DEVICES = {
    "cisco_iosxe": {
        "auth_username": FUNCTIONAL_USERNAME,
        "auth_password": FUNCTIONAL_PASSWORD,
        "auth_secondary": FUNCTIONAL_PASSWORD,
        "auth_private_key_passphrase": FUNCTIONAL_PASSPHRASE,
        "auth_strict_key": False,
        "host": "172.18.0.11",
        "base_config": f"{TEST_DATA_PATH}/base_configs/cisco_iosxe",
    },
    "mock_cisco_iosxe": {
        "auth_username": MOCK_USERNAME,
        "auth_password": MOCK_PASSWORD,
        "auth_secondary": MOCK_PASSWORD,
        "auth_private_key_passphrase": MOCK_PASSPHRASE,
        "auth_strict_key": False,
        "host": "localhost",
        "port": 2211,
    },
    "cisco_nxos": {
        "auth_username": FUNCTIONAL_USERNAME,
        "auth_password": FUNCTIONAL_PASSWORD,
        "auth_secondary": FUNCTIONAL_PASSWORD,
        "auth_strict_key": False,
        "host": "172.18.0.12",
        "base_config": f"{TEST_DATA_PATH}/base_configs/cisco_nxos",
    },
    "mock_cisco_nxos": {
        "auth_username": MOCK_USERNAME,
        "auth_password": MOCK_PASSWORD,
        "auth_secondary": MOCK_PASSWORD,
        "auth_private_key_passphrase": MOCK_PASSPHRASE,
        "auth_strict_key": False,
        "host": "localhost",
        "port": 2212,
    },
    "cisco_iosxr": {
        "auth_username": FUNCTIONAL_USERNAME,
        "auth_password": FUNCTIONAL_PASSWORD,
        "auth_secondary": FUNCTIONAL_PASSWORD,
        "auth_strict_key": False,
        "host": "172.18.0.13",
        "base_config": f"{TEST_DATA_PATH}/base_configs/cisco_iosxr",
    },
    "arista_eos": {
        "auth_username": FUNCTIONAL_USERNAME,
        "auth_password": FUNCTIONAL_PASSWORD,
        "auth_secondary": FUNCTIONAL_PASSWORD,
        "auth_strict_key": False,
        "host": "172.18.0.14",
        "comms_ansi": True,
        "base_config": f"{TEST_DATA_PATH}/base_configs/arista_eos",
    },
    "juniper_junos": {
        "auth_username": FUNCTIONAL_USERNAME,
        "auth_password": FUNCTIONAL_PASSWORD,
        "auth_secondary": FUNCTIONAL_PASSWORD,
        "auth_strict_key": False,
        "host": "172.18.0.15",
        "base_config": f"{TEST_DATA_PATH}/base_configs/juniper_junos",
    },
    "mock_juniper_junos": {
        "auth_username": MOCK_USERNAME,
        "auth_password": MOCK_PASSWORD,
        "auth_secondary": MOCK_PASSWORD,
        "auth_private_key_passphrase": MOCK_PASSPHRASE,
        "auth_strict_key": False,
        "host": "localhost",
        "port": 2215,
    },
    "linux": {
        "auth_username": "root",
        "auth_password": "docker",
        "auth_strict_key": False,
        "host": "172.18.0.20",
        "comms_ansi": True,
        "comms_prompt_pattern": r"^linux:~#\s*$",
    },
}
