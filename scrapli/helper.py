"""scrapli.helper"""

from asyncio import CancelledError
from asyncio import TimeoutError as AsyncioTimeoutError
from asyncio import get_event_loop, wait_for
from datetime import datetime
from os import read
from pathlib import Path
from select import select

from scrapli.exceptions import CancelledException, OperationException
from scrapli.ffi_types import Cancel, OperationIdPointer

WAKEUP_FD_SIGNAL_SIZE = 4
WAKEUP_FD_POLL_INTERVAL_S = 0.1


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


def _read_wakeup_signal_operation_id(fd: int) -> int:
    """
    Read a wakeup signal (an operation id) off of the wakeup fd.

    Args:
        fd: the fd to read from

    Returns:
        int: the operation id the wakeup signal was for

    Raises:
        OperationException: if the fd was closed or we read an invalid signal size

    """
    b = read(fd, WAKEUP_FD_SIGNAL_SIZE)

    if len(b) == 0:
        raise OperationException("wakeup signal fd closed")

    if len(b) != WAKEUP_FD_SIGNAL_SIZE:
        raise OperationException("wakeup signal read invalid read size")

    return int.from_bytes(b, byteorder="little")


def wait_for_available_operation_result(
    fd: int,
    cancel: Cancel,
    operation_id_ptr: OperationIdPointer,
) -> None:
    """
    Wait for the next operation to be complete.

    Args:
        fd: the fd to wait on
        cancel: the cancellation object for the op
        operation_id_ptr: the pointer to the operation id we are polling for

    Returns:
        None

    Raises:
        CancelledException: if cancellation ocurred while waiting.
        OperationException: if a wakeup signal is received for an operation id greater than the
            requested id -- this should never happen

    """
    while True:
        if cancel.cancelled:
            raise CancelledException

        readable, _, _ = select([fd], [], [], WAKEUP_FD_POLL_INTERVAL_S)

        if not readable:
            continue

        wait_wakeup_operation_id = _read_wakeup_signal_operation_id(fd)

        if wait_wakeup_operation_id == operation_id_ptr.contents.value:
            return

        if wait_wakeup_operation_id > operation_id_ptr.contents.value:
            raise OperationException(
                "signal received for operation id greater than requested, this should not happen"
            )


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
        if not fut.done():
            fut.set_result(None)

    loop.add_reader(fd, on_ready)

    try:
        await fut
    finally:
        loop.remove_reader(fd)


async def wait_for_available_operation_result_async(
    fd: int,
    cancel: Cancel,
    operation_id_ptr: OperationIdPointer,
) -> None:
    """
    Wait for the next operation to be complete.

    Args:
        fd: the fd to wait on
        cancel: the cancellation object for the op
        operation_id_ptr: the pointer to the operation id we are polling for

    Returns:
        None

    Raises:
        CancelledException: if cancellation ocurred while waiting.
        OperationException: if a wakeup signal is received for an operation id greater than the
            requested id -- this should never happen

    """
    while True:
        if cancel.cancelled:
            raise CancelledException

        try:
            await wait_for(_wait_for_fd_readable(fd), timeout=WAKEUP_FD_POLL_INTERVAL_S)
        except AsyncioTimeoutError:
            continue
        except CancelledError:
            # the enclosing task was cancelled -- propagate that into the operation's cancel so
            # libscrapli stops the work (and drops the result), then re-raise
            cancel.cancel()

            raise

        wait_wakeup_operation_id = _read_wakeup_signal_operation_id(fd)

        if wait_wakeup_operation_id == operation_id_ptr.contents.value:
            return

        if wait_wakeup_operation_id > operation_id_ptr.contents.value:
            raise OperationException(
                "signal received for operation id greater than requested, this should not happen"
            )


def second_to_nano(d: int | float) -> int:
    """
    Convert a duration in seconds to nanoseconds

    Args:
        d: the duration in seconds to convert

    Returns:
        int: converted duration in nanoseconds

    Raises:
        N/A

    """
    return int(d / 1e-9)


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
