"""examples.logging.specific_host_logging"""
import asyncio
import logging

from scrapli import AsyncScrapli


class HostFilter(logging.Filter):
    """We need to create a filter to filter down to just the host(s) we care about"""

    def filter(self, record):
        # in the filter method we check to see if the log record.host matches a host we care about
        # if so, we return True, otherwise we can return False obviously!
        if record.host == "172.18.0.11":
            return True
        return False


# grab the root scrapli logger and create a filehandler, attach the filter here
logger = logging.getLogger("scrapli")
fh = logging.FileHandler("scrapli.log", "w")
fh.addFilter(HostFilter())
# a pretty formatter so we can see the host:port printed out to confirm our filter is doing its job
formatter = logging.Formatter("%(asctime)s %(host)s:%(port)s : %(message)s")

# attach the formatter and set a log level, final add the file handler to the logger
fh.setFormatter(formatter)
logger.setLevel(level=logging.DEBUG)
logger.addHandler(fh)

DEVICE1 = {
    "host": "172.18.0.11",
    "auth_strict_key": False,
    "ssh_config_file": True,
    "transport": "asyncssh",
    "platform": "cisco_iosxe",
}
DEVICE2 = {
    "host": "172.18.0.12",
    "auth_strict_key": False,
    "ssh_config_file": True,
    "transport": "asyncssh",
    "platform": "cisco_nxos",
}


async def print_prompt(device):
    """Simple function to open/print prompt/close the connection"""
    conn = AsyncScrapli(**device)
    await conn.open()
    prompt = await conn.get_prompt()
    print(prompt)
    await conn.close()


async def main():
    """Main async entrypoint"""
    await asyncio.gather(*[print_prompt(host) for host in (DEVICE1, DEVICE2)])


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(main())
