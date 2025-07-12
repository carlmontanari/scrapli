"""examples.cli.async_usage.main"""

import asyncio
import os
import sys
from random import random

from scrapli import AuthOptions, Cli

IS_DARWIN = sys.platform == "darwin"
PLATFORM = os.getenv("SCRAPLI_PLATFORM", "nokia_srlinux")
HOST = os.getenv("SCRAPLI_HOST", "localhost" if IS_DARWIN else "172.20.20.16")
PORT = int(os.getenv("SCRAPLI_PORT") or 21022 if IS_DARWIN else 22)
USERNAME = os.getenv("SCRAPLI_USERNAME", "admin")
PASSWORD = os.getenv("SCRAPLI_USERNAME", "NokiaSrl1!")


async def background(i: int) -> None:
    """Do dumb background work"""
    while True:
        print(f"background task {i} doign work...")
        await asyncio.sleep(random())


async def run(i: int, cli: Cli) -> tuple[int, str]:
    """Run some stuff asynchronously for the connection"""
    print(f"cli connection {i} opening...")

    async with cli as c:
        # addign some randomness to make output more interesting
        await asyncio.sleep(random())

        # when doing async stuff, just do the same as you'd do with sync, but add _async to the
        # method name (and obv await it/schedule it), thats the only difference
        r = await c.send_input_async(input_="show version")

    print(f"cli connection {i} closed, returning...")

    return i, r.result


async def main() -> None:
    """A simple program showing async usage."""
    clis = [
        # creation is exactly the same as sync -- in "new" scrapli ("scrapli2", the stuff using
        # the zig backend) any transport can be used asynchronously and there is no differnet
        # class to use to create the Cli connection object.
        Cli(
            definition_file_or_name=PLATFORM,
            host=HOST,
            port=PORT,
            auth_options=AuthOptions(
                username=USERNAME,
                password=PASSWORD,
            ),
        )
        for _ in range(0, 5)
    ]

    for i in range(0, 25):
        # run some background junk to simulate a realish event loop
        asyncio.create_task(background(i))  # noqa:RUF006

    # run some stuff for each of our cli objects
    coros = [run(i, c) for i, c in enumerate(clis)]

    for coro in asyncio.as_completed(coros):
        # as they finish we'll print some stuff
        i, r = await coro

        print(f"cli connection {i} complete, result:\n{r}")


if __name__ == "__main__":
    asyncio.run(main())
