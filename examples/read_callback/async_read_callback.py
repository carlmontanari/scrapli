"""examples.read_callback.async_read_callback"""
import asyncio

from scrapli.driver.core import AsyncIOSXEDriver
from scrapli.driver.generic.async_driver import AsyncGenericDriver
from scrapli.driver.generic.base_driver import ReadCallback

device = {
    "host": "c3560",
    "auth_strict_key": False,
    "ssh_config_file": True,
    "transport": "asyncssh",
}


async def callback_one(cls: AsyncGenericDriver, read_output: str):
    """Callback that enters config mode (as a silly example)"""
    _ = read_output

    # note that because cls is typed `GenericDriver` mypy/IDE will not like this, but it does work
    # because yay python :) (assuming the driver you use is a NetworkDriver of course)
    await cls.acquire_priv("configuration")
    cls.channel.send_return()


async def callback_two(cls: AsyncGenericDriver, read_output: str):
    """Callback that enters runs a silly command"""
    print(f"previous read output : {read_output}")

    r = await cls.send_command("do show run | i hostname")
    print(f"result: {r.result}")


async def main():
    """Main"""
    async with AsyncIOSXEDriver(**device) as conn:
        callbacks = [
            ReadCallback(
                contains="rtr1#",
                callback=callback_one,
                name="enter config mode callback",
                case_insensitive=False,
            ),
            ReadCallback(
                contains_re=r"^rtr1\(config\)#",
                callback=callback_two,
                complete=True,
            ),
        ]
        await conn.read_callback(callbacks=callbacks, initial_input="show run | i hostname")


if __name__ == "__main__":
    asyncio.run(main())
