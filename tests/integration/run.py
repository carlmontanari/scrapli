import asyncio
from pathlib import Path
from typing import Optional

from scrapli_replay.server.server import start

import scrapli

TEST_DATA_DIR = f"{Path(scrapli.__file__).parents[1]}/tests/test_data"

SERVERS = [("iosxe", 2221), ("nxos", 2222), ("iosxr", 2223), ("eos", 2224), ("junos", 2225)]


async def run_servers() -> None:
    await asyncio.gather(
        *[
            start(
                port=server[1],
                collect_data=f"{TEST_DATA_DIR}/mock_server_sessions/{server[0]}.yaml",
            )
            for server in SERVERS
        ]
    )


def sync_run_servers(loop: Optional[asyncio.base_events.BaseEventLoop] = None) -> None:
    if loop is None:
        loop = asyncio.get_event_loop()

    loop.run_until_complete(run_servers())
    loop.run_forever()


if __name__ == "__main__":
    sync_run_servers()
