"""scrapli.helper"""

from asyncio import get_event_loop
from os import read
from pathlib import Path
from select import select

from scrapli.exceptions import OperationException


def resolve_file(file: str) -> str:
    """
    Resolve file from provided string

    Args:
        file: string path to file

    Returns:
        str: resolved/expanded (if applicable) string path to file

    Raises:
        OperationException: if file cannot be resolved

    """
    if Path(file).is_file():
        return str(Path(file))
    if Path(file).expanduser().is_file():
        return str(Path(file).expanduser())

    raise OperationException(f"path `{file}` could not be resolved")


def wait_for_available_operation_result(fd: int) -> None:
    """
    Wait for the next operation to be complete.

    Args:
        fd: the fd to wait on

    Returns:
        None

    Raises:
        N/A

    """
    _, _, _ = select([fd], [], [])
    read(fd, 1)


async def _wait_for_fd_readable(fd: int) -> None:
    """
    Wait for fd to be readable.

    Args:
        fd: the fd to wait on

    Returns:
        None

    Raises:
        N/A

    """
    loop = get_event_loop()

    fut = loop.create_future()

    def on_ready() -> None:
        loop.remove_reader(fd)

        fut.set_result(None)

    loop.add_reader(fd, on_ready)

    await fut


async def wait_for_available_operation_result_async(fd: int) -> None:
    """
    Wait for the next operation to be complete.

    Args:
        fd: the fd to wait on

    Returns:
        None

    Raises:
        N/A

    """
    await _wait_for_fd_readable(fd)

    read(fd, 1)
