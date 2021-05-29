"""examples.async_usage.async_multiple_connections"""
import asyncio

from scrapli.driver.core import AsyncIOSXEDriver, AsyncNXOSDriver

IOSXE_DEVICE = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
    "transport": "asyncssh",
    "driver": AsyncIOSXEDriver,
}

NXOS_DEVICE = {
    "host": "172.18.0.12",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
    "transport": "asyncssh",
    "driver": AsyncNXOSDriver,
}

DEVICES = [IOSXE_DEVICE, NXOS_DEVICE]


async def gather_version(device):
    """Simple function to open a connection and get some data"""
    driver = device.pop("driver")
    conn = driver(**device)
    await conn.open()
    prompt_result = await conn.get_prompt()
    version_result = await conn.send_command("show version")
    await conn.close()
    return prompt_result, version_result


async def main():
    """Function to gather coroutines, await them and print results"""
    coroutines = [gather_version(device) for device in DEVICES]
    results = await asyncio.gather(*coroutines)
    for result in results:
        print(f"device prompt: {result[0]}")
        print(f"device show version: {result[1].result}")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
