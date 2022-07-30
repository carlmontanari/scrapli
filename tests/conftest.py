from pathlib import Path

import pytest
from devices import DEVICES
from helper import (
    arista_eos_clean_response,
    cisco_iosxe_clean_response,
    cisco_iosxr_clean_response,
    cisco_nxos_clean_response,
    juniper_junos_clean_response,
)
from pyfakefs.fake_filesystem_unittest import Patcher

import scrapli

TEST_DATA_PATH = f"{Path(scrapli.__file__).parents[1]}/tests/test_data"


@pytest.fixture
def fs_():
    # replaces "fs" (pyfakefs) with patched one that does *not* use cache -- this is because
    # pyats does something fucky with modules that breaks pyfakefs.
    with Patcher(use_cache=False) as patcher:
        yield patcher.fs


@pytest.fixture(scope="session")
def test_data_path():
    """Fixture to provide path to test data files"""
    return TEST_DATA_PATH


@pytest.fixture(scope="session")
def test_devices_dict():
    """Fixture to return test devices dict"""
    return DEVICES


TEST_CASES = {
    "cisco_iosxe": {
        "send_command_short": {
            "command": "show run | i hostname",
        },
        "send_command_long": {
            "command": "show run",
        },
        "send_commands_from_file": {
            "file": f"{TEST_DATA_PATH}/source/cisco_iosxe/send_commands",
        },
        "send_commands_error": {
            "commands": ["show version", "show tacocat", "show version"],
        },
        "send_interactive_normal_response": {
            "command": [("clear logg", "Clear logging buffer [confirm]"), ("", "#")],
        },
        "send_config": {
            "configs": "interface loopback123\ndescription scrapli was here",
            "teardown_configs": "no interface loopback123",
        },
        "send_configs": {
            "configs": ["interface loopback123", "description scrapli was here"],
            "teardown_configs": "no interface loopback123",
        },
        "send_configs_from_file": {
            "file": f"{TEST_DATA_PATH}/source/cisco_iosxe/send_configs",
            "teardown_configs": "no interface loopback123",
        },
        "send_configs_error": {
            "configs": ["interface loopback123", "show tacocat", "description tacocat was here"],
            "teardown_configs": "no interface loopback123",
        },
        "sanitize_response": cisco_iosxe_clean_response,
    },
    "cisco_nxos": {
        "send_command_short": {
            "command": "show run | i scp-server",
        },
        "send_command_long": {
            "command": "show run",
        },
        "send_commands_from_file": {
            "file": f"{TEST_DATA_PATH}/source/cisco_nxos/send_commands",
        },
        "send_commands_error": {
            "commands": ["show version", "show tacocat", "show version"],
        },
        "send_interactive_normal_response": {
            "command": [
                ("delete bootflash:virtual-instance.conf", "(yes/no/abort)   [y]"),
                ("n", "#"),
            ],
        },
        "send_config": {
            "configs": "interface loopback123\ndescription scrapli was here",
            "teardown_configs": "no interface loopback123",
        },
        "send_configs": {
            "configs": ["interface loopback123", "description scrapli was here"],
            "teardown_configs": "no interface loopback123",
        },
        "send_configs_from_file": {
            "file": f"{TEST_DATA_PATH}/source/cisco_nxos/send_configs",
            "teardown_configs": "no interface loopback123",
        },
        "send_configs_error": {
            "configs": ["interface loopback123", "show tacocat", "description tacocat was here"],
            "teardown_configs": "no interface loopback123",
        },
        "sanitize_response": cisco_nxos_clean_response,
    },
    "cisco_iosxr": {
        "send_command_short": {
            "command": "show run | i MgmtEth0",
        },
        "send_command_long": {
            "command": "show run",
        },
        "send_commands_from_file": {
            "file": f"{TEST_DATA_PATH}/source/cisco_iosxr/send_commands",
        },
        "send_commands_error": {
            "commands": ["show version", "show tacocat", "show version"],
        },
        "send_interactive_normal_response": None,
        "send_config": {
            "configs": "interface loopback123\ndescription scrapli was here\ncommit",
            "teardown_configs": ["no interface loopback123", "commit"],
        },
        "send_configs": {
            "configs": ["interface loopback123", "description scrapli was here", "commit"],
            "teardown_configs": ["no interface loopback123", "commit"],
        },
        "send_configs_from_file": {
            "file": f"{TEST_DATA_PATH}/source/cisco_iosxr/send_configs",
            "teardown_configs": ["no interface loopback123", "commit"],
        },
        "send_configs_error": {
            "configs": ["interface loopback123", "show tacocat", "description tacocat was here"],
            "teardown_configs": ["no interface loopback123", "commit"],
        },
        "sanitize_response": cisco_iosxr_clean_response,
    },
    "arista_eos": {
        "send_command_short": {
            "command": "show run | i ZTP",
        },
        "send_command_long": {
            "command": "show run",
        },
        "send_commands_from_file": {
            "file": f"{TEST_DATA_PATH}/source/arista_eos/send_commands",
        },
        "send_commands_error": {
            "commands": ["show version", "show tacocat", "show version"],
        },
        "send_interactive_normal_response": None,
        "send_config": {
            "configs": "interface loopback123\ndescription scrapli was here",
            "teardown_configs": "no interface loopback123",
        },
        "send_configs": {
            "configs": ["interface loopback123", "description scrapli was here"],
            "teardown_configs": "no interface loopback123",
        },
        "send_configs_from_file": {
            "file": f"{TEST_DATA_PATH}/source/arista_eos/send_configs",
            "teardown_configs": "no interface loopback123",
        },
        "send_configs_error": {
            "configs": ["interface loopback123", "show tacocat", "description tacocat was here"],
            "teardown_configs": "no interface loopback123",
        },
        "sanitize_response": arista_eos_clean_response,
    },
    "juniper_junos": {
        "send_command_short": {
            "command": "show configuration | match 10.0.0.15",
        },
        "send_command_long": {
            "command": "show configuration",
        },
        "send_commands_from_file": {
            "file": f"{TEST_DATA_PATH}/source/juniper_junos/send_commands",
        },
        "send_commands_error": {
            "commands": ["show version", "show tacocat", "show version"],
        },
        "send_interactive_normal_response": None,
        "send_config": {
            "configs": 'set interfaces fxp0 unit 0 description "scrapli was here"\ncommit',
            "teardown_configs": ["delete interfaces fxp0 unit 0 description", "commit"],
        },
        "send_configs": {
            "configs": ['set interfaces fxp0 unit 0 description "scrapli was here"', "commit"],
            "teardown_configs": ["delete interfaces fxp0 unit 0 description", "commit"],
        },
        "send_configs_from_file": {
            "file": f"{TEST_DATA_PATH}/source/juniper_junos/send_configs",
            "teardown_configs": ["delete interfaces fxp0 unit 0 description", "commit"],
        },
        "send_configs_error": {
            "configs": [
                "set interfaces fxp0 description tacocat",
                "show tacocat",
                "set interfaces fxp0 description tacocat",
            ],
            "teardown_configs": ["delete interfaces fxp0 description", "commit"],
        },
        "sanitize_response": juniper_junos_clean_response,
    },
}


@pytest.fixture(scope="session")
def test_cases():
    """Fixture to return test cases shared across functional and integration tests"""
    return TEST_CASES
