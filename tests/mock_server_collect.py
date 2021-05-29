import sys
from copy import deepcopy
from pathlib import Path

from devices import DEVICES
from scrapli_replay.server.collector import ScrapliCollector

import scrapli

TEST_DATA_DIR = f"{Path(scrapli.__file__).parents[1]}/tests/test_data"

COLLECT_COMMANDS = {
    "cisco_iosxe": ["show version", "show run"],
    "cisco_nxos": ["show version", "show run"],
    "cisco_iosxr": ["show version", "show run"],
    "arista_eos": ["show version", "show run"],
    "juniper_junos": ["show version", "show configuration"],
}
COLLECT_INTERACTIVE = {
    "cisco_iosxe": [
        [("clear logg", "Clear logging buffer [confirm]", False), ("", "csr1000v#", False)]
    ],
    "cisco_nxos": [
        [
            ("clear logg onboard", "Do you want to continue? (y/n)  [n]", False),
            ("y", "switch#", False),
        ]
    ],
    "cisco_iosxr": [
        [
            ("clear logg", "Clear logging buffer [confirm] [y/n] :", False),
            ("y", "RP/0/RP0/CPU0:ios#", False),
        ]
    ],
    "arista_eos": [
        [("clear logg", "Clear logging buffer [confirm]", False), ("", "switch#", False)]
    ],
    "juniper_junos": [],
}
PAGING_INDICATOR = {
    "cisco_iosxe": "--More--",
    "cisco_nxos": "--More--",
    "cisco_iosxr": "--More--",
    "arista_eos": "--More--",
    "juniper_junos": "---(more)---",
}
PAGING_ESCAPE = {
    "cisco_iosxe": "\x1b",
    "cisco_nxos": "q",
    "cisco_iosxr": "q",
    "arista_eos": "q",
    "juniper_junos": "q",
}


def collect(test_devices):
    for device in test_devices:
        conn_dict = {
            "host": DEVICES[device]["host"],
            "port": DEVICES[device]["port"],
            "auth_username": DEVICES[device]["auth_username"],
            "auth_password": DEVICES[device]["auth_password"],
            "auth_secondary": DEVICES[device]["auth_secondary"],
            "auth_strict_key": DEVICES[device]["auth_strict_key"],
            "platform": device,
            # nxos on macos w/out acceleration is... slooooooooooow
            "timeout_ops": 120,
            "timeout_transport": 0,
        }

        if device == "cisco_nxos":
            from scrapli.driver.core.cisco_nxos.base_driver import PRIVS

            privs = deepcopy(PRIVS)
            privs.pop("exec")
            privs["privilege_exec"].previous_priv = ""
            privs["privilege_exec"].escalate = ""
            privs["privilege_exec"].escalate_prompt = ""

            conn_dict["privilege_levels"] = privs

        conn = scrapli.Scrapli(**conn_dict)
        conn.open()

        if device == "cisco_iosxe":
            conn.send_configs(["no ip domain-lookup"])

        collector = ScrapliCollector(
            channel_inputs=COLLECT_COMMANDS[device],
            interact_events=COLLECT_INTERACTIVE[device],
            paging_indicator=PAGING_INDICATOR[device],
            paging_escape_string=PAGING_ESCAPE[device],
            collector_session_filename=f"{TEST_DATA_DIR}/mock_server_sessions/{device}.yaml",
            scrapli_connection=conn,
        )

        collector.open()
        collector.collect()
        collector.close()
        collector.dump()


def main():
    test_devices = sys.argv[1].split(",")
    collect(test_devices)


if __name__ == "__main__":
    main()
