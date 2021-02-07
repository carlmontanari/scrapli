from pathlib import Path

from scrapli_replay.server.collector import ScrapliCollector

import scrapli

TEST_DATA_DIR = f"{Path(scrapli.__file__).parents[1]}/tests/test_data"


def main():
    scrapli_kwargs = {
        "host": "localhost",
        "port": 25022,
        "ssh_config_file": False,
        "auth_strict_key": False,
        "auth_username": "vrnetlab",
        "auth_password": "VR-netlab9",
        "auth_secondary": "VR-netlab9",
        "platform": "juniper_junos",
    }
    collector = ScrapliCollector(
        channel_inputs=["show version", "show configuration"],
        interact_events=[],
        paging_indicator="---(more)---",
        paging_escape_string="q",
        collector_session_filename=f"{TEST_DATA_DIR}/mock_server_sessions/junos.yaml",
        **scrapli_kwargs,
    )

    collector.open()
    collector.collect()
    collector.close()
    collector.dump()


if __name__ == "__main__":
    main()
