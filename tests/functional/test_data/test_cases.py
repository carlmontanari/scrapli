from pathlib import Path

import scrapli

from .helper import (
    arista_eos_clean_response,
    cisco_iosxe_clean_response,
    cisco_iosxr_clean_response,
    cisco_nxos_clean_response,
    juniper_junos_clean_response,
)

TEST_DATA_PATH = f"{Path(scrapli.__file__).parents[1]}/tests/functional/test_data"


TEST_CASES = {
    "cisco_iosxe": {
        "get_prompt": {
            "exec": "csr1000v>",
            "privilege_exec": "csr1000v#",
            "configuration": "csr1000v(config)#",
        },
        "send_command_short": {
            "command": "show run | i hostname",
            "expected_no_strip": "hostname csr1000v\ncsr1000v#",
            "expected_strip": "hostname csr1000v",
        },
        "send_command_long": {
            "command": "show run",
            "expected_no_strip": open(
                f"{TEST_DATA_PATH}/expected/cisco_iosxe/send_command_long_no_strip"
            ).read(),
            "expected_strip": open(
                f"{TEST_DATA_PATH}/expected/cisco_iosxe/send_command_long_strip"
            ).read(),
        },
        "send_commands_from_file": {
            "file": f"{TEST_DATA_PATH}/source/cisco_iosxe/send_commands",
            "expected_no_strip": ["hostname csr1000v\ncsr1000v#", "hostname csr1000v\ncsr1000v#"],
            "expected_strip": ["hostname csr1000v", "hostname csr1000v"],
        },
        "send_commands_error": {
            "commands": ["show version", "show tacocat", "show version"],
        },
        "send_interactive_normal_response": {
            "command": [("clear logg", "Clear logging buffer [confirm]"), ("", "csr1000v#")],
            "expected": "clear logg\nClear logging buffer [confirm]\n\ncsr1000v#",
        },
        "send_interactive_hidden_response": None,
        "send_config": {
            "configs": "interface loopback123\ndescription scrapli was here",
            "expected_no_strip": "csr1000v(config-if)#\ncsr1000v(config-if)#",
            "expected_strip": "\n",
            "verification": "show run int loopback123",
            "verification_expected_no_strip": "Building configuration...\n\nCurrent configuration : CONFIG_BYTES"
            "\n!\ninterface Loopback123\n description scrapli was here\n no ip"
            " address\nend\n\ncsr1000v#",
            "verification_expected_strip": "Building configuration...\n\nCurrent configuration : CONFIG_BYTES"
            "\n!\ninterface Loopback123\n description scrapli was here\n no ip "
            "address\nend",
            "teardown_configs": "no interface loopback123",
        },
        "send_configs": {
            "configs": ["interface loopback123", "description scrapli was here"],
            "expected_no_strip": ["csr1000v(config-if)#", "csr1000v(config-if)#"],
            "expected_strip": ["", ""],
            "verification": "show run int loopback123",
            "verification_expected_no_strip": "Building configuration...\n\nCurrent configuration : CONFIG_BYTES"
            "\n!\ninterface Loopback123\n description scrapli was here\n no ip"
            " address\nend\n\ncsr1000v#",
            "verification_expected_strip": "Building configuration...\n\nCurrent configuration : CONFIG_BYTES"
            "\n!\ninterface Loopback123\n description scrapli was here\n no ip "
            "address\nend",
            "teardown_configs": "no interface loopback123",
        },
        "send_configs_from_file": {
            "file": f"{TEST_DATA_PATH}/source/cisco_iosxe/send_configs",
            "expected_no_strip": ["csr1000v(config-if)#", "csr1000v(config-if)#"],
            "expected_strip": ["", ""],
            "teardown_configs": "no interface loopback123",
        },
        "send_configs_error": {
            "configs": ["interface loopback123", "show tacocat", "description tacocat was here"],
            "teardown_configs": "no interface loopback123",
        },
        "sanitize_response": cisco_iosxe_clean_response,
    },
    "cisco_nxos": {
        "get_prompt": {
            "exec": None,
            "privilege_exec": "switch#",
            "configuration": "switch(config)#",
        },
        "send_command_short": {
            "command": "show run | i scp-server",
            "expected_no_strip": "feature scp-server\nswitch#",
            "expected_strip": "feature scp-server",
        },
        "send_command_long": {
            "command": "show run",
            "expected_no_strip": open(
                f"{TEST_DATA_PATH}/expected/cisco_nxos/send_command_long_no_strip"
            ).read(),
            "expected_strip": open(
                f"{TEST_DATA_PATH}/expected/cisco_nxos/send_command_long_strip"
            ).read(),
        },
        "send_commands_from_file": {
            "file": f"{TEST_DATA_PATH}/source/cisco_nxos/send_commands",
            "expected_no_strip": ["feature scp-server\nswitch#", "feature scp-server\nswitch#"],
            "expected_strip": ["feature scp-server", "feature scp-server"],
        },
        "send_commands_error": {
            "commands": ["show version", "show tacocat", "show version"],
        },
        "send_interactive_normal_response": {
            "command": [
                ("delete bootflash:virtual-instance.conf", "(yes/no/abort)   [y]"),
                ("n", "switch#"),
            ],
            "expected": 'delete bootflash:virtual-instance.conf\nDo you want to delete "/virtual-instance.conf" ? (yes/no/abort)   [y] n\nswitch#',
        },
        "send_interactive_hidden_response": None,
        "send_config": {
            "configs": "interface loopback123\ndescription scrapli was here",
            "expected_no_strip": "switch(config-if)#\nswitch(config-if)#",
            "expected_strip": "\n",
            "verification": "show run int loopback123",
            "verification_expected_no_strip": "!Command: show running-config interface loopback123\n!Running "
            "configuration last done at: TIME_STAMP_REPLACED\n!Time: "
            "TIME_STAMP_REPLACED\n\nversion 9.2(4) Bios:version\n\ninterface "
            "loopback123\n  description scrapli was here\n\nswitch#",
            "verification_expected_strip": "!Command: show running-config interface loopback123\n!Running "
            "configuration last done at: TIME_STAMP_REPLACED\n!Time: "
            "TIME_STAMP_REPLACED\n\nversion 9.2(4) Bios:version\n\ninterface "
            "loopback123\n  description scrapli was here",
            "teardown_configs": "no interface loopback123",
        },
        "send_configs": {
            "configs": ["interface loopback123", "description scrapli was here"],
            "expected_no_strip": ["switch(config-if)#", "switch(config-if)#"],
            "expected_strip": ["", ""],
            "verification": "show run int loopback123",
            "verification_expected_no_strip": "!Command: show running-config interface loopback123\n!Running "
            "configuration last done at: TIME_STAMP_REPLACED\n!Time: "
            "TIME_STAMP_REPLACED\n\nversion 9.2(4) Bios:version\n\ninterface "
            "loopback123\n  description scrapli was here\n\nswitch#",
            "verification_expected_strip": "!Command: show running-config interface loopback123\n!Running "
            "configuration last done at: TIME_STAMP_REPLACED\n!Time: "
            "TIME_STAMP_REPLACED\n\nversion 9.2(4) Bios:version\n\ninterface "
            "loopback123\n  description scrapli was here",
            "teardown_configs": "no interface loopback123",
        },
        "send_configs_from_file": {
            "file": f"{TEST_DATA_PATH}/source/cisco_nxos/send_configs",
            "expected_no_strip": ["switch(config-if)#", "switch(config-if)#"],
            "expected_strip": ["", ""],
            "teardown_configs": "no interface loopback123",
        },
        "send_configs_error": {
            "configs": ["interface loopback123", "show tacocat", "description tacocat was here"],
            "teardown_configs": "no interface loopback123",
        },
        "sanitize_response": cisco_nxos_clean_response,
    },
    "cisco_iosxr": {
        "get_prompt": {
            "exec": None,
            "privilege_exec": "RP/0/RP0/CPU0:ios#",
            "configuration": "RP/0/RP0/CPU0:ios(config)#",
        },
        "send_command_short": {
            "command": "show run | i MgmtEth0",
            "expected_no_strip": "TIME_STAMP_REPLACED\nBuilding configuration...\ninterface MgmtEth0/RP0/CPU0/0\nRP/0/RP0/CPU0:ios#",
            "expected_strip": "TIME_STAMP_REPLACED\nBuilding configuration...\ninterface MgmtEth0/RP0/CPU0/0",
        },
        "send_command_long": {
            "command": "show run",
            "expected_no_strip": open(
                f"{TEST_DATA_PATH}/expected/cisco_iosxr/send_command_long_no_strip"
            ).read(),
            "expected_strip": open(
                f"{TEST_DATA_PATH}/expected/cisco_iosxr/send_command_long_strip"
            ).read(),
        },
        "send_commands_from_file": {
            "file": f"{TEST_DATA_PATH}/source/cisco_iosxr/send_commands",
            "expected_no_strip": [
                "TIME_STAMP_REPLACED\nBuilding configuration...\ninterface MgmtEth0/RP0/CPU0/0\nRP/0/RP0/CPU0:ios#",
                "TIME_STAMP_REPLACED\nBuilding configuration...\ninterface MgmtEth0/RP0/CPU0/0\nRP/0/RP0/CPU0:ios#",
            ],
            "expected_strip": [
                "TIME_STAMP_REPLACED\nBuilding configuration...\ninterface MgmtEth0/RP0/CPU0/0",
                "TIME_STAMP_REPLACED\nBuilding configuration...\ninterface MgmtEth0/RP0/CPU0/0",
            ],
        },
        "send_commands_error": {
            "commands": ["show version", "show tacocat", "show version"],
        },
        "send_interactive_normal_response": None,
        "send_interactive_hidden_response": None,
        "send_config": {
            "configs": "interface loopback123\ndescription scrapli was here\ncommit",
            "expected_no_strip": "RP/0/RP0/CPU0:ios(config-if)#\nRP/0/RP0/CPU0:ios(config-if)#\nTIME_STAMP_REPLACED\nRP/0/RP0/CPU0:ios(config-if)#",
            "expected_strip": "\n\nTIME_STAMP_REPLACED",  # we get the timestamp of the commit in this output
            "verification": "show run int loopback123",
            "verification_expected_no_strip": "TIME_STAMP_REPLACED\ninterface Loopback123\n description scrapli was here\n!\n\nRP/0/RP0/CPU0:ios#",
            "verification_expected_strip": "TIME_STAMP_REPLACED\ninterface Loopback123\n description scrapli was here\n!",
            "teardown_configs": ["no interface loopback123", "commit"],
        },
        "send_configs": {
            "configs": ["interface loopback123", "description scrapli was here", "commit"],
            "expected_no_strip": ["RP/0/RP0/CPU0:ios(config-if)#", "RP/0/RP0/CPU0:ios(config-if)#"],
            "expected_strip": ["", ""],
            "verification": "show run int loopback123",
            "verification_expected_no_strip": "TIME_STAMP_REPLACED\ninterface Loopback123\n description scrapli was here\n!\n\nRP/0/RP0/CPU0:ios#",
            "verification_expected_strip": "TIME_STAMP_REPLACED\ninterface Loopback123\n description scrapli was here\n!",
            "teardown_configs": ["no interface loopback123", "commit"],
        },
        "send_configs_from_file": {
            "file": f"{TEST_DATA_PATH}/source/cisco_iosxr/send_configs",
            "expected_no_strip": ["RP/0/RP0/CPU0:ios(config-if)#", "RP/0/RP0/CPU0:ios(config-if)#"],
            "expected_strip": ["", ""],
            "teardown_configs": ["no interface loopback123", "commit"],
        },
        "send_configs_error": {
            "configs": ["interface loopback123", "show tacocat", "description tacocat was here"],
            "teardown_configs": ["no interface loopback123", "commit"],
        },
        "sanitize_response": cisco_iosxr_clean_response,
    },
    "arista_eos": {
        "get_prompt": {
            "exec": "localhost>",
            "privilege_exec": "localhost#",
            "configuration": "localhost(config)#",
        },
        "send_command_short": {
            "command": "show run | i ZTP",
            "expected_no_strip": "logging level ZTP informational\nlocalhost#",
            "expected_strip": "logging level ZTP informational",
        },
        "send_command_long": {
            "command": "show run",
            "expected_no_strip": open(
                f"{TEST_DATA_PATH}/expected/arista_eos/send_command_long_no_strip"
            ).read(),
            "expected_strip": open(
                f"{TEST_DATA_PATH}/expected/arista_eos/send_command_long_strip"
            ).read(),
        },
        "send_commands_from_file": {
            "file": f"{TEST_DATA_PATH}/source/arista_eos/send_commands",
            "expected_no_strip": [
                "logging level ZTP informational\nlocalhost#",
                "logging level ZTP informational\nlocalhost#",
            ],
            "expected_strip": [
                "logging level ZTP informational",
                "logging level ZTP informational",
            ],
        },
        "send_commands_error": {
            "commands": ["show version", "show tacocat", "show version"],
        },
        "send_interactive_normal_response": None,
        "send_interactive_hidden_response": None,
        "send_config": {
            "configs": "interface loopback123\ndescription scrapli was here",
            "expected_no_strip": "localhost(config-if-Lo123)#\nlocalhost(config-if-Lo123)#",
            "expected_strip": "\n",
            "verification": "show run int loopback123",
            "verification_expected_no_strip": "interface Loopback123\n   description scrapli was here\nlocalhost#",
            "verification_expected_strip": "interface Loopback123\n   description scrapli was here",
            "teardown_configs": "no interface loopback123",
        },
        "send_configs": {
            "configs": ["interface loopback123", "description scrapli was here"],
            "expected_no_strip": ["localhost(config-if-Lo123)#", "localhost(config-if-Lo123)#"],
            "expected_strip": ["", ""],
            "verification": "show run int loopback123",
            "verification_expected_no_strip": "interface Loopback123\n   description scrapli was here\nlocalhost#",
            "verification_expected_strip": "interface Loopback123\n   description scrapli was here",
            "teardown_configs": "no interface loopback123",
        },
        "send_configs_from_file": {
            "file": f"{TEST_DATA_PATH}/source/arista_eos/send_configs",
            "expected_no_strip": ["localhost(config-if-Lo123)#", "localhost(config-if-Lo123)#"],
            "expected_strip": ["", ""],
            "teardown_configs": "no interface loopback123",
        },
        "send_configs_error": {
            "configs": ["interface loopback123", "show tacocat", "description tacocat was here"],
            "teardown_configs": "no interface loopback123",
        },
        "sanitize_response": arista_eos_clean_response,
    },
    "juniper_junos": {
        "get_prompt": {
            "exec": "vrnetlab>",
            "privilege_exec": None,
            "configuration": "vrnetlab#",
        },
        "send_command_short": {
            "command": "show configuration | match 10.0.0.15",
            "expected_no_strip": "                address 10.0.0.15/24;\n\nvrnetlab>",
            "expected_strip": "                address 10.0.0.15/24;",
        },
        "send_command_long": {
            "command": "show configuration",
            "expected_no_strip": open(
                f"{TEST_DATA_PATH}/expected/juniper_junos/send_command_long_no_strip"
            ).read(),
            "expected_strip": open(
                f"{TEST_DATA_PATH}/expected/juniper_junos/send_command_long_strip"
            ).read(),
        },
        "send_commands_from_file": {
            "file": f"{TEST_DATA_PATH}/source/juniper_junos/send_commands",
            "expected_no_strip": [
                "                address 10.0.0.15/24;\n\nvrnetlab>",
                "                address 10.0.0.15/24;\n\nvrnetlab>",
            ],
            "expected_strip": [
                "                address 10.0.0.15/24;",
                "                address 10.0.0.15/24;",
            ],
        },
        "send_commands_error": {
            "commands": ["show version", "show tacocat", "show version"],
        },
        "send_interactive_normal_response": None,
        "send_interactive_hidden_response": None,
        "send_config": {
            "configs": 'set interfaces fxp0 unit 0 description "scrapli was here"\ncommit',
            "expected_no_strip": "[edit]\nvrnetlab#\ncommit complete\n\n[edit]\nvrnetlab#",
            "expected_strip": "[edit]\ncommit complete\n\n[edit]",
            "verification": "show configuration interfaces fxp0",
            "verification_expected_no_strip": 'unit 0 {\n    description "scrapli was here";\n    family inet {\n        address 10.0.0.15/24;\n    }\n}\n\nvrnetlab>',
            "verification_expected_strip": 'unit 0 {\n    description "scrapli was here";\n    family inet {\n        address 10.0.0.15/24;\n    }\n}',
            "teardown_configs": ["delete interfaces fxp0 unit 0 description", "commit"],
        },
        "send_configs": {
            "configs": ['set interfaces fxp0 unit 0 description "scrapli was here"', "commit"],
            "expected_no_strip": ["[edit]\nvrnetlab#", "commit complete\n\n[edit]\nvrnetlab#"],
            "expected_strip": ["[edit]", "commit complete\n\n[edit]"],
            "verification": "show configuration interfaces fxp0",
            "verification_expected_no_strip": 'unit 0 {\n    description "scrapli was here";\n    family inet {\n        address 10.0.0.15/24;\n    }\n}\n\nvrnetlab>',
            "verification_expected_strip": 'unit 0 {\n    description "scrapli was here";\n    family inet {\n        address 10.0.0.15/24;\n    }\n}',
            "teardown_configs": ["delete interfaces fxp0 unit 0 description", "commit"],
        },
        "send_configs_from_file": {
            "file": f"{TEST_DATA_PATH}/source/juniper_junos/send_configs",
            "expected_no_strip": ["[edit]\nvrnetlab#", "commit complete\n\n[edit]\nvrnetlab#"],
            "expected_strip": ["[edit]", "commit complete\n\n[edit]"],
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
    "linux": {
        "get_prompt": "linux:~#",
        "send_command_short": {
            "command": "cat /etc/hostname",
            "expected_no_strip": "linux\nlinux:~#",
            "expected_strip": "linux",
        },
        "send_command_long": {
            "command": "cat /etc/init.d/sshd",
            "expected_no_strip": open(
                f"{TEST_DATA_PATH}/expected/linux/send_command_long_no_strip"
            ).read(),
            "expected_strip": open(
                f"{TEST_DATA_PATH}/expected/linux/send_command_long_strip"
            ).read(),
        },
    },
}
