"""scrapli.transport"""

ASYNCIO_TRANSPORTS = (
    "asynctelnet",
    "asyncssh",
)
CORE_TRANSPORTS = ("telnet", "system", "ssh2", "paramiko", "asynctelnet", "asyncssh")

__all__ = (
    "ASYNCIO_TRANSPORTS",
    "CORE_TRANSPORTS",
)
