from copy import deepcopy
from pathlib import Path

from scrapli_replay.server.collector import ScrapliCollector

import scrapli
from scrapli.driver.core.cisco_nxos.base_driver import PRIVS

TEST_DATA_DIR = f"{Path(scrapli.__file__).parents[1]}/tests/test_data"


def main():
    privs = deepcopy(PRIVS)
    privs.pop("exec")
    privs["privilege_exec"].previous_priv = ""
    privs["privilege_exec"].escalate = ""
    privs["privilege_exec"].escalate_prompt = ""

    scrapli_kwargs = {
        "host": "localhost",
        "port": 22022,
        "ssh_config_file": False,
        "auth_strict_key": False,
        "auth_username": "vrnetlab",
        "auth_password": "VR-netlab9",
        "auth_secondary": "VR-netlab9",
        "platform": "cisco_nxos",
        "privilege_levels": privs,
        "timeout_ops": 120.0,
        "timeout_socket": 120.0,
        "timeout_transport": 120.0,
        "comms_ansi": True,
    }

    collector = ScrapliCollector(
        channel_inputs=["show version", "show run"],
        interact_events=[
            [
                ("clear logg onboard", "Do you want to continue? (y/n)  [n]", False),
                ("y", "switch#", False),
            ]
        ],
        paging_indicator="--More--",
        paging_escape_string="q",
        collector_session_filename=f"{TEST_DATA_DIR}/mock_server_sessions/nxos.yaml",
        **scrapli_kwargs,
    )

    collector.open()
    collector.collect()
    collector.close()
    collector.dump()


if __name__ == "__main__":
    main()
