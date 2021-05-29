"""examples.async_usage.async_iosxe_driver"""
import asyncio

from scrapli.driver.core import AsyncIOSXEDriver

MY_DEVICE = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
    "transport": "asyncssh",
}


async def main():
    """Simple example of connecting to an IOSXEDevice with the AsyncIOSXEDriver"""
    async with AsyncIOSXEDriver(**MY_DEVICE) as conn:
        # Platform drivers will auto-magically handle disabling paging for you
        result = await conn.send_command("show run")

    print(result.result)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
