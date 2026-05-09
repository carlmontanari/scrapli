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
    LibScrapliFFIResult,
    OptionsPointer,
    USizePointer,
    ZigSlicePointer,
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
        lib.ls_shared_get_poll_fd.restype = c_int

        self._free: Callable[
            [
                DriverPointer,
            ],
            None,
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

        self._fetch_options_size: Callable[
            [
                OptionsPointer,
                USizePointer,
            ],
            int,
        ] = lib.ls_fetch_options_size
        lib.ls_fetch_options_size.argtypes = [
            OptionsPointer,
            USizePointer,
        ]
        lib.ls_fetch_options_size.restype = c_uint8

        self._fetch_options: Callable[
            [
                OptionsPointer,
                ZigSlicePointer,
            ],
            None,
        ] = lib.ls_fetch_options
        lib.ls_fetch_options.argtypes = [
            OptionsPointer,
            ZigSlicePointer,
        ]
        lib.ls_fetch_options.restype = None

    def get_poll_fd(self, ptr: DriverPointer) -> c_int:
        """
        Get the operation poll fd from the driver at ptr.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscrapli cli/netconf object.

        Returns:
            c_int: the poll fd for the driver.

        Raises:
            N/A

        """
        return self._get_poll_fd(ptr)

    def free(self, ptr: DriverPointer) -> None:
        """
        Free the driver at ptr.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscrapli cli/netconf object.

        Returns:
            N/A

        Raises:
            N/A

        """
        return self._free(ptr)

    def alloc_driver_options(self) -> OptionsPointer:
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

    def free_driver_options(self, options_ptr: OptionsPointer) -> None:
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

    def fetch_options_size(
        self,
        options_ptr: OptionsPointer,
        options_size: USizePointer,
    ) -> None:
        """
        Fetches the size of the options rendered as json.

        Should (generally) not be called directly/by users. Mostly for testing purposes.

        Args:
            options_ptr: pointer to the options to get the size of.
            options_size: pointer to write the size of the options into.

        Returns:
            N/A

        Raises:
            OptionsException: if we fail to get the size of the options from libscrapli.

        """
        LibScrapliFFIResult(
            self._fetch_options_size(
                options_ptr,
                options_size,
            )
        ).raise_if_error(
            message="failed to retrieve options size",
        )

    def fetch_options(self, options_ptr: OptionsPointer, options: ZigSlicePointer) -> None:
        """
        Fetches the options as json, written into the slice pointer.

        Should (generally) not be called directly/by users. Mostly for testing purposes.

        Args:
            options_ptr: pointer to the options to get the size of.
            options: pointer to write the options into.

        Returns:
            N/A

        Raises:
            N/A

        """
        return self._fetch_options(options_ptr, options)


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
                ZigSlicePointer,
                USizePointer,
            ],
            int,
        ] = lib.ls_session_read
        lib.ls_session_read.argtypes = [
            DriverPointer,
            ZigSlicePointer,
            USizePointer,
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

        self._write_return: Callable[
            [
                DriverPointer,
            ],
            int,
        ] = lib.ls_session_write_return
        lib.ls_session_write_return.argtypes = [
            DriverPointer,
        ]
        lib.ls_session_write_return.restype = c_uint8

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

    def read(
        self,
        ptr: DriverPointer,
        buf: ZigSlicePointer,
        read_size: USizePointer,
    ) -> None:
        """
        Read from the session of driver at ptr.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscrapli cli/netconf object.
            buf: buffer to fill during the read operation.
            read_size: c_int pointer that is filled with number of bytes written into buf.

        Returns:
            N/A

        Raises:
            OperationException: if the operation fails

        """
        LibScrapliFFIResult(
            self._read(ptr, buf, read_size),
        ).raise_if_error(
            message="executing read operation failed",
        )

    def write(
        self,
        ptr: DriverPointer,
        input_: c_char_p,
        redacted: c_bool,
    ) -> None:
        """
        Write to the session of driver at ptr.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscrapli cli/netconf object.
            input_: buffer contents to write during the write operation..
            redacted: bool indicated if the write contents should be redacted from logs.

        Returns:
            N/A

        Raises:
            OperationException: if the operation fails

        """
        LibScrapliFFIResult(
            self._write(ptr, input_, redacted),
        ).raise_if_error(
            message="executing write operation failed",
        )

    def write_and_return(
        self,
        ptr: DriverPointer,
        input_: c_char_p,
        redacted: c_bool,
    ) -> None:
        """
        Write and then send a return to the session of driver at ptr.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscrapli cli/netconf object.
            input_: buffer contents to write during the write operation..
            redacted: bool indicated if the write contents should be redacted from logs.

        Returns:
            N/A

        Raises:
            OperationException: if the operation fails

        """
        LibScrapliFFIResult(
            self._write_and_return(ptr, input_, redacted),
        ).raise_if_error(
            message="executing write and return operation failed",
        )

    def write_return(self, ptr: DriverPointer) -> None:
        """
        Write a return to the session of driver at ptr.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscrapli cli/netconf object.

        Returns:
            N/A

        Raises:
            OperationException: if the operation fails

        """
        LibScrapliFFIResult(
            self._write_return(ptr),
        ).raise_if_error(
            message="executing write return operation failed",
        )

    def set_operation_timeout_ns(
        self, ptr: DriverPointer, set_operation_timeout_ns: c_uint64
    ) -> None:
        """
        Set the session operation timeout in ns.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            set_operation_timeout_ns: operation timeout in ns

        Returns:
            N/A

        Raises:
            OptionsException: when encountering issue setting timeout

        """
        LibScrapliFFIResult(
            self._set_operation_timeout_ns(ptr, set_operation_timeout_ns),
        ).raise_if_error(
            message="failed to set session operation timeout",
        )


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
