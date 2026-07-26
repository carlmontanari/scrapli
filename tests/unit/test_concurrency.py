"""scrapli concurrency tests -- mirrors scrapligo's cli TestConcurrency"""

import asyncio
import random
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

CONCURRENCY_COUNT = 100


@pytest.mark.parametrize(
    argnames=("transport",),
    argvalues=(("bin",), ("ssh2",)),
    ids=("concurrency-bin", "concurrency-ssh2"),
)
def test_concurrency(dummy_ssh_server, concurrency_cli):
    def _open_and_send_input() -> None:
        # tiny (random) sleep seems to make the test way more consistent -- at least locally on
        # darwin it seems like we can get starved for ptys and weird stuff happens w/out this
        time.sleep(random.randint(0, 100) / 1000)

        with concurrency_cli() as c:
            result = c.send_input(input_="show version")

            assert result.failed is False

    with ThreadPoolExecutor(max_workers=CONCURRENCY_COUNT) as executor:
        futures = [executor.submit(_open_and_send_input) for _ in range(CONCURRENCY_COUNT)]

        for future in futures:
            future.result()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=("transport",),
    argvalues=(("bin",), ("ssh2",)),
    ids=("concurrency-bin", "concurrency-ssh2"),
)
async def test_concurrency_async(dummy_ssh_server, concurrency_cli):
    async def _open_and_send_input() -> None:
        # as in the sync test, a tiny sleep makes things way more consistent
        await asyncio.sleep(random.randint(0, 100) / 1000)

        async with concurrency_cli() as c:
            result = await c.send_input_async(input_="show version")

            assert result.failed is False

    await asyncio.gather(*(_open_and_send_input() for _ in range(CONCURRENCY_COUNT)))
