"""scrapli.ffi_mapping"""  # pylint: disable=too-many-lines,too-many-arguments,too-many-instance-attributes

from ctypes import (
    CDLL,
    c_bool,
    c_char_p,
    c_int,
    c_uint8,
)
from typing import Callable

from scrapli.ffi import get_libscrapli_path
from scrapli.ffi_mapping_cli import LibScrapliCliMapping
from scrapli.ffi_mapping_netconf import LibScrapliNetconfMapping
from scrapli.ffi_mapping_options import LibScrapliOptionsMapping
from scrapli.ffi_types import (
    CancelPointer,
    DriverPointer,
    IntPointer,
    OperationIdPointer,
    StringPointer,
)


class LibScrapliSharedMapping:
    """
    Mapping to libscrapli shared (between cli/netconf) object functions mapping.

    Should not be used/called directly.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(self, lib: CDLL) -> None:
        self._free: Callable[
            [
                DriverPointer,
            ],
            int,
        ] = lib.ls_free
        lib.ls_free.argtypes = [
            DriverPointer,
        ]
        lib.ls_free.restype = None

        self._open: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
            ],
            int,
        ] = lib.ls_open
        lib.ls_open.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
        ]
        lib.ls_open.restype = c_uint8

        self._close: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
            ],
            int,
        ] = lib.ls_close
        lib.ls_close.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
        ]
        lib.ls_close.restype = c_uint8

        self._read: Callable[
            [
                DriverPointer,
                StringPointer,
                IntPointer,
            ],
            int,
        ] = lib.ls_read_session
        lib.ls_read_session.argtypes = [
            DriverPointer,
            StringPointer,
            IntPointer,
        ]
        lib.ls_read_session.restype = c_int

        self._write: Callable[
            [
                DriverPointer,
                c_char_p,
                c_bool,
            ],
            int,
        ] = lib.ls_write_session
        lib.ls_write_session.argtypes = [
            DriverPointer,
            c_char_p,
            c_bool,
        ]
        lib.ls_write_session.restype = c_uint8

    def free(self, ptr: DriverPointer) -> int:
        """
        Free the driver at ptr.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscraplicli/netconf object.

        Returns:
            c_uint8: return code, non-zero value indicates an error.

        Raises:
            N/A

        """
        return self._free(ptr)

    def open(
        self, ptr: DriverPointer, operation_id: OperationIdPointer, cancel: CancelPointer
    ) -> int:
        """
        Open the driver at ptr.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscraplicli/netconf object.
            operation_id: c_int pointer that is filled with the operation id to poll for completion.
            cancel: bool pointer that can be set to true to cancel the operation.

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._open(ptr, operation_id, cancel)

    def close(
        self, ptr: DriverPointer, operation_id: OperationIdPointer, cancel: CancelPointer
    ) -> int:
        """
        Close the driver at ptr.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscraplicli/netconf object.
            operation_id: c_int pointer that is filled with the operation id to poll for completion.
            cancel: bool pointer that can be set to true to cancel the operation.

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._close(ptr, operation_id, cancel)

    def read(self, ptr: DriverPointer, buf: StringPointer, read_size: IntPointer) -> int:
        """
        Read from the session of driver at ptr.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscraplicli/netconf object.
            buf: buffer to fill during the read operation.
            read_size: c_int pointer that is filled with number of bytes written into buf.

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._read(ptr, buf, read_size)

    def write(self, ptr: DriverPointer, buf: c_char_p, redacted: c_bool) -> int:
        """
        Write to the session of driver at ptr.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscraplicli/netconf object.
            buf: buffer contents to write during the write operation..
            redacted: bool indicated if the write contents should be redacted from logs.

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._write(ptr, buf, redacted)


class LibScrapliMapping:  # pylint: disable=too-few-public-methods
    """
    Single mapping to libscrapli shared library exported functions.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    _instance = None

    def __new__(cls) -> "LibScrapliMapping":
        if not cls._instance:
            cls._instance = super(LibScrapliMapping, cls).__new__(cls)

        return cls._instance

    def __init__(self) -> None:
        self.lib = CDLL(get_libscrapli_path())
        self.shared_mapping = LibScrapliSharedMapping(self.lib)
        self.cli_mapping = LibScrapliCliMapping(self.lib)
        self.netconf_mapping = LibScrapliNetconfMapping(self.lib)
        self.options_mapping = LibScrapliOptionsMapping(self.lib)
