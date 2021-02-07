from pathlib import Path

from scrapli_replay.server.collector import ScrapliCollector

import scrapli

TEST_DATA_DIR = f"{Path(scrapli.__file__).parents[1]}/tests/test_data"


def main():
    scrapli_kwargs = {
        "host": "localhost",
        "port": 24022,
        "ssh_config_file": False,
        "auth_strict_key": False,
        "auth_username": "vrnetlab",
        "auth_password": "VR-netlab9",
        "auth_secondary": "VR-netlab9",
        "platform": "arista_eos",
    }
    collector = ScrapliCollector(
        channel_inputs=["show version", "show run"],
        interact_events=[
            [("clear logg", "Clear logging buffer [confirm]", False), ("", "switch#", False)]
        ],
        paging_indicator="--More--",
        paging_escape_string="\x1b",
        collector_session_filename=f"{TEST_DATA_DIR}/mock_server_sessions/eos.yaml",
        **scrapli_kwargs,
    )

    collector.open()
    collector.collect()
    collector.close()
    collector.dump()


if __name__ == "__main__":
    main()
