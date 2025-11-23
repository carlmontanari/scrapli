"""scrapli.ffi_mapping"""

from collections.abc import Callable
from ctypes import (
    CDLL,
    c_bool,
    c_char_p,
    c_int,
    c_uint8,
    c_uint64,
    c_void_p,
)

from scrapli.ffi import get_libscrapli_path
from scrapli.ffi_mapping_cli import LibScrapliCliMapping
from scrapli.ffi_mapping_netconf import LibScrapliNetconfMapping
from scrapli.ffi_types import (
    DriverPointer,
    IntPointer,
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
        self._get_poll_fd: Callable[
            [
                DriverPointer,
            ],
            c_int,
        ] = lib.ls_shared_get_poll_fd
        lib.ls_shared_get_poll_fd.argtypes = [
            DriverPointer,
        ]
        lib.ls_cli_alloc.restype = c_int

        self._free: Callable[
            [
                DriverPointer,
            ],
            int,
        ] = lib.ls_shared_free
        lib.ls_shared_free.argtypes = [
            DriverPointer,
        ]
        lib.ls_shared_free.restype = None

        self._alloc_driver_options: Callable[
            [],
            c_void_p,
        ] = lib.ls_alloc_driver_options
        lib.ls_alloc_driver_options.argtypes = []
        lib.ls_alloc_driver_options.restype = c_void_p

        self._free_driver_options: Callable[
            [
                c_void_p,
            ],
            None,
        ] = lib.ls_free_driver_options
        lib.ls_free_driver_options.argtypes = [c_void_p]
        lib.ls_free_driver_options.restype = None

    def get_poll_fd(self, ptr: DriverPointer) -> c_int:
        """
        Get the operation poll fd from the driver at ptr.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscrapli cli/netconf object.

        Returns:
            c_uint32: the poll fd for the driver.

        Raises:
            N/A

        """
        return self._get_poll_fd(ptr)

    def free(self, ptr: DriverPointer) -> int:
        """
        Free the driver at ptr.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscrapli cli/netconf object.

        Returns:
            c_uint8: return code, non-zero value indicates an error.

        Raises:
            N/A

        """
        return self._free(ptr)

    def alloc_driver_options(self) -> c_void_p:
        """
        Allocates a cli/netconf driver options struct in the zig ffi bits.

        Should (generally) not be called directly/by users.

        Args:
            N/A

        Returns:
            c_void_p: pointer to the allocated options struct.

        Raises:
            N/A

        """
        return self._alloc_driver_options()

    def free_driver_options(self, options_ptr: c_void_p) -> None:
        """
        Frees a cli/netconf driver options struct in the zig ffi bits.

        Should (generally) not be called directly/by users.

        Args:
            options_ptr: pointer to the struct to free.

        Returns:
            None

        Raises:
            N/A

        """
        return self._free_driver_options(options_ptr)


class LibScrapliSessionMapping:
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
        self._read: Callable[
            [
                DriverPointer,
                StringPointer,
                IntPointer,
            ],
            int,
        ] = lib.ls_session_read
        lib.ls_session_read.argtypes = [
            DriverPointer,
            StringPointer,
            IntPointer,
        ]
        lib.ls_session_read.restype = c_int

        self._write: Callable[
            [
                DriverPointer,
                c_char_p,
                c_bool,
            ],
            int,
        ] = lib.ls_session_write
        lib.ls_session_write.argtypes = [
            DriverPointer,
            c_char_p,
            c_bool,
        ]
        lib.ls_session_write.restype = c_uint8

        self._write_and_return: Callable[
            [
                DriverPointer,
                c_char_p,
                c_bool,
            ],
            int,
        ] = lib.ls_session_write_and_return
        lib.ls_session_write_and_return.argtypes = [
            DriverPointer,
            c_char_p,
            c_bool,
        ]
        lib.ls_session_write_and_return.restype = c_uint8

        self._set_operation_timeout_ns: Callable[
            [
                DriverPointer,
                c_uint64,
            ],
            int,
        ] = lib.ls_session_operation_timeout_ns
        lib.ls_session_operation_timeout_ns.argtypes = [
            DriverPointer,
            c_uint64,
        ]
        lib.ls_session_operation_timeout_ns.restype = c_uint8

    def read(self, ptr: DriverPointer, buf: StringPointer, read_size: IntPointer) -> int:
        """
        Read from the session of driver at ptr.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscrapli cli/netconf object.
            buf: buffer to fill during the read operation.
            read_size: c_int pointer that is filled with number of bytes written into buf.

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._read(ptr, buf, read_size)

    def write(self, ptr: DriverPointer, input_: c_char_p, redacted: c_bool) -> int:
        """
        Write to the session of driver at ptr.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscrapli cli/netconf object.
            input_: buffer contents to write during the write operation..
            redacted: bool indicated if the write contents should be redacted from logs.

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._write(ptr, input_, redacted)

    def write_and_return(self, ptr: DriverPointer, input_: c_char_p, redacted: c_bool) -> int:
        """
        Write and then send a return to the session of driver at ptr.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscrapli cli/netconf object.
            input_: buffer contents to write during the write operation..
            redacted: bool indicated if the write contents should be redacted from logs.

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._write_and_return(ptr, input_, redacted)

    def set_operation_timeout_ns(
        self, ptr: DriverPointer, set_operation_timeout_ns: c_uint64
    ) -> int:
        """
        Set the session operation timeout in ns.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            set_operation_timeout_ns: operation timeout in ns

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_operation_timeout_ns(ptr, set_operation_timeout_ns)


class LibScrapliMapping:
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
        """Returns the singleton instance of the ffi mapping"""
        if not cls._instance:
            cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self) -> None:
        self.lib = CDLL(get_libscrapli_path())

        self._assert_no_leaks: Callable[
            [],
            bool,
        ] = self.lib.ls_assert_no_leaks
        self.lib.ls_assert_no_leaks.argtypes = []
        self.lib.ls_assert_no_leaks.restype = c_bool

        self.shared_mapping = LibScrapliSharedMapping(self.lib)
        self.session_mapping = LibScrapliSessionMapping(self.lib)
        self.cli_mapping = LibScrapliCliMapping(self.lib)
        self.netconf_mapping = LibScrapliNetconfMapping(self.lib)

    def assert_no_leaks(self) -> bool:
        """
        Assert no memory leaks -- only works with debug libscrapli build.

        Should (generally) not be called directly/by users.

        Args:
            N/A

        Returns:
            bool: True if leaks, otherwise False

        Raises:
            N/A

        """
        return bool(self._assert_no_leaks())
