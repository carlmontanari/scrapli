"""scrapli.helper"""

import sys
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
        fd: the fd to wait on. On Windows this is a WinSock SOCKET value
            (the read end of a loopback TCP pair); on POSIX it is the read
            end of the wakeup pipe.

    Returns:
        None

    Raises:
        N/A

    """
    if sys.platform == "win32":
        # CPython's socket(fileno=...) wrapper mis-detects raw WinSock
        # SOCKET values created inside the ffi library, so talk to
        # ws2_32 directly: select() on the wakeup socket, then recv() one
        # byte to consume the event. Mirrors the POSIX pipe flow above.
        import ctypes as _ctypes  # noqa: PLC0415

        class _fd_set(_ctypes.Structure):
            # WinSock fd_set: fd_count + fd_array[FD_SETSIZE] where each
            # element is a SOCKET (UINT_PTR = 8 bytes on x64). Using c_int
            # here misaligns the array and WSAENOTSOCKs every call.
            _fields_ = [("fd_count", _ctypes.c_uint), ("fd_array", _ctypes.c_uint64 * 64)]

        class _timeval(_ctypes.Structure):
            _fields_ = [("tv_sec", _ctypes.c_long), ("tv_usec", _ctypes.c_long)]

        ws2 = _ctypes.WinDLL("ws2_32", use_last_error=True)
        ws2.select.argtypes = [
            _ctypes.c_int,
            _ctypes.POINTER(_fd_set),
            _ctypes.c_void_p,
            _ctypes.c_void_p,
            _ctypes.POINTER(_timeval),
        ]
        ws2.select.restype = _ctypes.c_int
        ws2.recv.argtypes = [
            _ctypes.c_uint64,
            _ctypes.c_char_p,
            _ctypes.c_int,
            _ctypes.c_int,
        ]
        ws2.recv.restype = _ctypes.c_int

        read_set = _fd_set()
        read_set.fd_count = 1
        read_set.fd_array[0] = fd
        timeout = _timeval(5, 0)

        rc = ws2.select(0, _ctypes.byref(read_set), None, None, _ctypes.byref(timeout))
        err = ws2.WSAGetLastError()
        print(
            f"[helper] select(sock={fd}) rc={rc} lasterr={err}",
            file=sys.stderr,
            flush=True,
        )
        if rc > 0:
            buf = _ctypes.create_string_buffer(1)
            got = ws2.recv(fd, buf, 1, 0)
            print(
                f"[helper] consumed {got} bytes",
                file=sys.stderr,
                flush=True,
            )
        elif rc == 0:
            # timeout with no event: keep waiting rather than pretending the
            # operation finished (mirrors blocking POSIX behaviour).
            import time as _t  # noqa: PLC0415

            _t.sleep(0.05)
            return wait_for_available_operation_result(fd)
        else:
            raise OSError(err, f"winsock select failed on wake socket {fd}")
        return

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
