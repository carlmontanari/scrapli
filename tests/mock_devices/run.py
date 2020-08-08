"""mock_devices.run"""
import asyncio
from typing import List, Optional

import asyncssh

from .cisco_iosxe import IOSXEServer, IOSXESSHServerSession
from .cisco_nxos import NXOSServer, NXOSSSHServerSession
from .juniper_junos import JunosServer, JunoSSHServerSession

SERVERS = {
    "cisco_iosxe": {"server_session": IOSXESSHServerSession, "server": IOSXEServer, "port": 2211},
    "cisco_nxos": {"server_session": NXOSSSHServerSession, "server": NXOSServer, "port": 2212},
    "juniper_junos": {"server_session": JunoSSHServerSession, "server": JunosServer, "port": 2215},
}


async def start_server(platform: str, server_key: str) -> None:
    """
    Coroutine to start ssh server

    Args:
        platform: name of server type to start
        server_key: string path to key to use for ssh server(s)

    Returns:
        None

    Raises:
        N/A

    """
    server = SERVERS[platform]["server"]
    server.ServerSession = SERVERS[platform]["server_session"]
    port = SERVERS[platform]["port"]
    await asyncssh.create_server(server, "localhost", port, server_host_keys=[server_key])


async def main(server_key: str, servers: List[str]) -> None:
    """
    Async main

    Args:
        server_key: string path to key to use for ssh server(s)
        servers: list of servers to start

    Returns:
        None

    Raises:
        N/A

    """
    await asyncio.gather(
        *[start_server(platform=platform, server_key=server_key) for platform in servers]
    )


def run(
    server_key: str,
    server: Optional[str] = None,
    loop: Optional[asyncio.base_events.BaseEventLoop] = None,
) -> None:
    """
    Run server(s)

    Args:
        server_key: string path to key to use for ssh server(s)
        server: name of server to run, i.e. "cisco_iosxe", if None, run all servers
        loop: event loop to use, if none provided get current loop

    Returns:
        None

    Raises:
        N/A

    """
    if loop is None:
        loop = asyncio.get_event_loop()
    if server is None:
        servers = SERVERS
    else:
        servers = [server]
    loop.run_until_complete(main(server_key=server_key, servers=servers))
    loop.run_forever()
