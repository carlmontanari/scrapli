"""scrapli.helper"""

from asyncio import get_event_loop
from datetime import datetime
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


def unix_nano_timestmap_to_iso(timestamp: int) -> str:
    """
    Convert a unix ns timestamp to iso format.

    Args:
        timestamp: the timestamp to convert

    Returns:
        str: converted timestamp

    Raises:
        N/A

    """
    return datetime.fromtimestamp(timestamp / 1_000_000_000).isoformat(timespec="milliseconds")


def bulid_result_preview(result: str) -> str:
    """
    Build a preview of output for str method of result objects from the given result string.

    Skips lines that are all the same char (like a banner line "****") and only shows a single line
    plus a "... <truncated>" line indicating longer output.

    Args:
        result: the full result to build the preview for

    Returns:
        str: result preview

    Raises:
        N/A

    """
    lines = result.splitlines()

    def boring_line(line: str) -> bool:
        stripped = line.strip()

        return not stripped or len(set(stripped)) == 1

    preview_line = ""

    for line in lines[:2]:
        if not boring_line(line):
            preview_line = line[:40].rstrip()
            break

    if len(result) > len(preview_line):
        # spacing to make it look nice in result str method
        return f"{preview_line}\n\t                 : ... <truncated>"

    return preview_line
