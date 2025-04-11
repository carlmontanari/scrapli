"""scrapli.ffi_mapping"""  # pylint: disable=too-many-lines,too-many-arguments,too-many-instance-attributes

from ctypes import (
    CDLL,
    c_bool,
    c_char_p,
    c_int,
    c_uint8,
)
from typing import Callable

from _ctypes import POINTER

from scrapli.ffi import get_libscrapli_path
from scrapli.ffi_types import (
    BoolPointer,
    CancelPointer,
    DriverPointer,
    IntPointer,
    LogFuncCallback,
    OperationId,
    OperationIdPointer,
    StringPointer,
    ZigSlice,
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


class LibScrapliCliMapping:
    """
    Mapping to libscrapli cli object functions mapping.

    Should not be used/called directly.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(self, lib: CDLL) -> None:
        self._alloc: Callable[
            [
                c_char_p,
                LogFuncCallback,
                c_char_p,
                c_int,
                c_char_p,
            ],
            DriverPointer,
        ] = lib.ls_alloc_cli
        lib.ls_alloc_cli.argtypes = [
            c_char_p,
            LogFuncCallback,
            c_char_p,
            c_int,
            c_char_p,
        ]
        lib.ls_alloc_cli.restype = DriverPointer

        self._poll: Callable[
            [
                DriverPointer,
                OperationId,
                BoolPointer,
                IntPointer,
                IntPointer,
                IntPointer,
                IntPointer,
                IntPointer,
            ],
            int,
        ] = lib.ls_cli_poll_operation
        lib.ls_cli_poll_operation.argtypes = [
            DriverPointer,
            OperationId,
            BoolPointer,
            IntPointer,
            IntPointer,
            IntPointer,
            IntPointer,
            IntPointer,
        ]
        lib.ls_cli_poll_operation.restype = c_uint8

        self._fetch: Callable[
            [
                DriverPointer,
                OperationId,
                IntPointer,
                IntPointer,
                ZigSlicePointer,
                ZigSlicePointer,
                ZigSlicePointer,
                ZigSlicePointer,
                ZigSlicePointer,
            ],
            int,
        ] = lib.ls_cli_fetch_operation
        lib.ls_cli_fetch_operation.argtypes = [
            DriverPointer,
            OperationId,
            IntPointer,
            IntPointer,
            POINTER(ZigSlice),
            POINTER(ZigSlice),
            POINTER(ZigSlice),
            POINTER(ZigSlice),
            POINTER(ZigSlice),
        ]
        lib.ls_cli_fetch_operation.restype = c_uint8

        self._enter_mode: Callable[
            [DriverPointer, OperationIdPointer, CancelPointer, c_char_p], int
        ] = lib.ls_cli_enter_mode
        lib.ls_cli_enter_mode.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
            c_char_p,
        ]
        lib.ls_cli_enter_mode.restype = c_uint8

        self._get_prompt: Callable[[DriverPointer, OperationIdPointer, CancelPointer], int] = (
            lib.ls_cli_get_prompt
        )
        lib.ls_cli_get_prompt.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
        ]
        lib.ls_cli_get_prompt.restype = c_uint8

        self._send_input: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
                c_char_p,
                c_char_p,
                c_char_p,
                c_bool,
                c_bool,
            ],
            int,
        ] = lib.ls_cli_send_input
        lib.ls_cli_send_input.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
            c_char_p,
            c_char_p,
            c_char_p,
            c_bool,
            c_bool,
        ]
        lib.ls_cli_send_input.restype = c_uint8

        self._send_prompted_input: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
                c_char_p,
                c_char_p,
                c_char_p,
                c_char_p,
                c_bool,
                c_char_p,
                c_char_p,
                c_bool,
            ],
            int,
        ] = lib.ls_cli_send_prompted_input
        lib.ls_cli_send_prompted_input.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
            c_char_p,
            c_char_p,
            c_char_p,
            c_char_p,
            c_bool,
            c_char_p,
            c_char_p,
            c_bool,
        ]
        lib.ls_cli_send_prompted_input.restype = c_uint8

    def alloc(
        self,
        *,
        definition_string: c_char_p,
        logger_callback: LogFuncCallback,
        host: c_char_p,
        port: c_int,
        transport_kind: c_char_p,
    ) -> DriverPointer:
        """
        Allocate a cli object.

        Should (generally) not be called directly/by users.

        Args:
            definition_string: yaml definition string
            logger_callback: pointer to logger callback function
            host: host to connect to
            port: port at which to connect
            transport_kind: transport kind to use

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._alloc(definition_string, logger_callback, host, port, transport_kind)

    def poll(
        self,
        *,
        ptr: DriverPointer,
        operation_id: OperationId,
        done: BoolPointer,
        input_size: IntPointer,
        result_raw_size: IntPointer,
        result_size: IntPointer,
        failed_indicator_size: IntPointer,
        err_size: IntPointer,
    ) -> int:
        """
        Poll for the result of a cli operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            operation_id: operation id of which to poll
            done: bool pointer that is set to true if the operation has completed
            input_size: int pointer to fill with the operation's input size
            result_raw_size: int pointer to fill with the operation's result raw size
            result_size:  int pointer to fill with the operation's result size
            failed_indicator_size: int pointer to fill with the operation's failed indicator size
            err_size: int pointer to fill with the operation's error size

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._poll(
            ptr,
            operation_id,
            done,
            input_size,
            result_raw_size,
            result_size,
            failed_indicator_size,
            err_size,
        )

    def fetch(
        self,
        *,
        ptr: DriverPointer,
        operation_id: OperationId,
        start_time: IntPointer,
        end_time: IntPointer,
        input_slice: ZigSlicePointer,
        result_raw_slice: ZigSlicePointer,
        result_slice: ZigSlicePointer,
        result_failed_indicator_slice: ZigSlicePointer,
        err_slice: ZigSlicePointer,
    ) -> int:
        """
        Fetch the result of a cli operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            operation_id: operation id of which to poll
            start_time: int pointer to fill with the operation's start time
            end_time: int pointer to fill with the operation's end time
            input_slice: pre allocated slice to fill with the operations input
            result_raw_slice: pre allocated slice to fill with the operations result raw
            result_slice: pre allocated slice to fill with the operations result
            result_failed_indicator_slice: pre allocated slice to fill with the operations failed
                indicator
            err_slice: pre allocated slice to fill with the operations error

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._fetch(
            ptr,
            operation_id,
            start_time,
            end_time,
            input_slice,
            result_raw_slice,
            result_slice,
            result_failed_indicator_slice,
            err_slice,
        )

    def enter_mode(
        self,
        *,
        ptr: DriverPointer,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
        requested_mode: c_char_p,
    ) -> int:
        """
        Enter the given mode for the cli object.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            operation_id: int pointer to fill with the id of the submitted operation
            cancel: bool pointer that can be set to true to cancel the operation
            requested_mode: string name of the mode to enter

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._enter_mode(ptr, operation_id, cancel, requested_mode)

    def get_prompt(
        self, *, ptr: DriverPointer, operation_id: OperationIdPointer, cancel: CancelPointer
    ) -> int:
        """
        Get the current prompt for the cli object.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            operation_id: int pointer to fill with the id of the submitted operation
            cancel: bool pointer that can be set to true to cancel the operation

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._get_prompt(ptr, operation_id, cancel)

    def send_input(
        self,
        *,
        ptr: DriverPointer,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
        input_: c_char_p,
        requested_mode: c_char_p,
        input_handling: c_char_p,
        retain_input: c_bool,
        retain_trailing_prompt: c_bool,
    ) -> int:
        """
        Send some input to the cli object.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            operation_id: int pointer to fill with the id of the submitted operation
            cancel: bool pointer that can be set to true to cancel the operation
            input: the input to send
            requested_mode: string name of the mode to send the input in
            input_handling: string mapping to input handling enum that governs how the input is
                handled
            retain_input: boolean indicating whether to retain the input after entering
            retain_trailing_prompt: boolean indicating whether to retain the trailing

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._send_input(
            ptr,
            operation_id,
            cancel,
            input_,
            requested_mode,
            input_handling,
            retain_input,
            retain_trailing_prompt,
        )

    def send_prompted_input(
        self,
        *,
        ptr: DriverPointer,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
        input_: c_char_p,
        prompt: c_char_p,
        prompt_pattern: c_char_p,
        response: c_char_p,
        hidden_response: c_bool,
        requested_mode: c_char_p,
        input_handling: c_char_p,
        retain_trailing_prompt: c_bool,
    ) -> int:
        """
        Send some prompted input to the cli object.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            operation_id: int pointer to fill with the id of the submitted operation
            cancel: bool pointer that can be set to true to cancel the operation
            input_: the input to send
            prompt: the prompt to expect
            prompt_pattern: the prompt pattern to expect
            response: the response to write when the prompt has been seen
            hidden_response: bool indicated if the response we write will be "hidden" on the device
            requested_mode: string name of the mode to send the input in
            input_handling: string mapping to input handling enum that governs how the input is
                handled
            retain_trailing_prompt: boolean indicating whether to retain the trailing

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._send_prompted_input(
            ptr,
            operation_id,
            cancel,
            input_,
            prompt,
            prompt_pattern,
            response,
            hidden_response,
            requested_mode,
            input_handling,
            retain_trailing_prompt,
        )


class LibScrapliNetconfMapping:
    """
    Mapping to libscrapli netconf object functions mapping.

    Should not be used/called directly.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(self, lib: CDLL) -> None:
        _ = lib


class LibScrapliSessionOptionsMapping:
    """
    Mapping to libscrapli session option setter exported functions.

    Should not be used/called directly.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(self, lib: CDLL) -> None:
        self._set_read_size: Callable[[DriverPointer, c_int], int] = lib.ls_option_session_read_size
        lib.ls_option_session_read_size.argtypes = [
            DriverPointer,
            c_int,
        ]
        lib.ls_option_session_read_size.restype = c_uint8

        self._set_read_delay_min_ns: Callable[[DriverPointer, c_int], int] = (
            lib.ls_option_session_read_delay_min_ns
        )
        lib.ls_option_session_read_delay_min_ns.argtypes = [
            DriverPointer,
            c_int,
        ]
        lib.ls_option_session_read_delay_min_ns.restype = c_uint8

        self._set_read_delay_max_ns: Callable[[DriverPointer, c_int], int] = (
            lib.ls_option_session_read_delay_max_ns
        )
        lib.ls_option_session_read_delay_max_ns.argtypes = [
            DriverPointer,
            c_int,
        ]
        lib.ls_option_session_read_delay_max_ns.restype = c_uint8

        self._set_read_delay_backoff_factor: Callable[[DriverPointer, c_int], int] = (
            lib.ls_option_session_read_delay_backoff_factor
        )
        lib.ls_option_session_read_delay_backoff_factor.argtypes = [
            DriverPointer,
            c_int,
        ]
        lib.ls_option_session_read_delay_backoff_factor.restype = c_uint8

        self._set_return_char: Callable[[DriverPointer, c_char_p], int] = (
            lib.ls_option_session_return_char
        )
        lib.ls_option_session_return_char.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_session_return_char.restype = c_uint8

        self._set_operation_timeout_ns: Callable[[DriverPointer, c_int], int] = (
            lib.ls_option_session_operation_timeout_ns
        )
        lib.ls_option_session_operation_timeout_ns.argtypes = [
            DriverPointer,
            c_int,
        ]
        lib.ls_option_session_operation_timeout_ns.restype = c_uint8

        self._set_operation_max_search_depth: Callable[[DriverPointer, c_int], int] = (
            lib.ls_option_session_operation_max_search_depth
        )
        lib.ls_option_session_operation_max_search_depth.argtypes = [
            DriverPointer,
            c_int,
        ]
        lib.ls_option_session_operation_max_search_depth.restype = c_uint8

        self._set_recorder_path: Callable[[DriverPointer, c_char_p], int] = (
            lib.ls_option_session_record_destination
        )
        lib.ls_option_session_record_destination.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_session_record_destination.restype = c_uint8

    def set_read_size(self, ptr: DriverPointer, read_size: c_int) -> int:
        """
        Set the session read size.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            read_size: read size

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_read_size(ptr, read_size)

    def set_read_delay_min_ns(self, ptr: DriverPointer, read_delay_min_ns: c_int) -> int:
        """
        Set the session minimum read delay in ns.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            read_delay_min_ns: minimum read delay in ns

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_read_delay_min_ns(ptr, read_delay_min_ns)

    def set_read_delay_max_ns(self, ptr: DriverPointer, read_delay_max_ns: c_int) -> int:
        """
        Set the session maximum read delay in ns.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            read_delay_max_ns: maximum read delay in ns

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_read_delay_max_ns(ptr, read_delay_max_ns)

    def set_read_delay_backoff_factor(
        self, ptr: DriverPointer, read_delay_backoff_factor: c_int
    ) -> int:
        """
        Set the session read delay backoff factor.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            read_delay_backoff_factor: read delay backoff factor

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_read_delay_backoff_factor(ptr, read_delay_backoff_factor)

    def set_return_char(self, ptr: DriverPointer, return_char: c_char_p) -> int:
        """
        Set the session return char

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            return_char: return char to use in the session (usually \n, could be \r\n)

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_return_char(ptr, return_char)

    def set_operation_timeout_ns(self, ptr: DriverPointer, set_operation_timeout_ns: c_int) -> int:
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

    def set_operation_max_search_depth(
        self, ptr: DriverPointer, set_operation_max_search_depth: c_int
    ) -> int:
        """
        Set the session maximum prompt search depth

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            set_operation_max_search_depth: maximum prompt search depth (in count of chars)

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_operation_max_search_depth(ptr, set_operation_max_search_depth)

    def set_recorder_path(self, ptr: DriverPointer, set_recorder_path: c_char_p) -> int:
        """
        Set the session recorder output path

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            set_recorder_path: file path to write session recorder output to

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_recorder_path(ptr, set_recorder_path)


class LibScrapliAuthOptionsMapping:
    """
    Mapping to libscrapli auth option setter exported functions.

    Should not be used/called directly.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(self, lib: CDLL) -> None:
        self._set_username: Callable[[DriverPointer, c_char_p], int] = lib.ls_option_auth_username
        lib.ls_option_auth_username.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_auth_username.restype = c_uint8

        self._set_password: Callable[[DriverPointer, c_char_p], int] = lib.ls_option_auth_password
        lib.ls_option_auth_password.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_auth_password.restype = c_uint8

        self._set_private_key_path: Callable[[DriverPointer, c_char_p], int] = (
            lib.ls_option_auth_private_key_path
        )
        lib.ls_option_auth_private_key_path.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_auth_private_key_path.restype = c_uint8

        self._set_private_key_passphrase: Callable[[DriverPointer, c_char_p], int] = (
            lib.ls_option_auth_private_key_passphrase
        )
        lib.ls_option_auth_private_key_passphrase.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_auth_private_key_passphrase.restype = c_uint8

        self._set_lookup_key_value: Callable[[DriverPointer, c_char_p, c_char_p], int] = (
            lib.ls_option_auth_set_lookup_key_value
        )
        lib.ls_option_auth_set_lookup_key_value.argtypes = [
            DriverPointer,
            c_char_p,
            c_char_p,
        ]
        lib.ls_option_auth_set_lookup_key_value.restype = c_uint8

        self._set_in_session_auth_bypass: Callable[[DriverPointer], int] = (
            lib.ls_option_auth_in_session_auth_bypass
        )
        lib.ls_option_auth_in_session_auth_bypass.argtypes = [
            DriverPointer,
        ]
        lib.ls_option_auth_in_session_auth_bypass.restype = c_uint8

        self._set_username_pattern: Callable[[DriverPointer, c_char_p], int] = (
            lib.ls_option_auth_username_pattern
        )
        lib.ls_option_auth_username_pattern.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_auth_username_pattern.restype = c_uint8

        self._set_password_pattern: Callable[[DriverPointer, c_char_p], int] = (
            lib.ls_option_auth_password_pattern
        )
        lib.ls_option_auth_password_pattern.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_auth_password_pattern.restype = c_uint8

        self._set_private_key_passphrase_pattern: Callable[[DriverPointer, c_char_p], int] = (
            lib.ls_option_auth_private_key_passphrase_pattern
        )
        lib.ls_option_auth_private_key_passphrase_pattern.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_auth_private_key_passphrase_pattern.restype = c_uint8

    def set_username(self, ptr: DriverPointer, username: c_char_p) -> int:
        """
        Set the username.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            username: username string

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_username(ptr, username)

    def set_password(self, ptr: DriverPointer, password: c_char_p) -> int:
        """
        Set the password.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            password: password string

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_password(ptr, password)

    def set_private_key_path(self, ptr: DriverPointer, private_key_path: c_char_p) -> int:
        """
        Set the private key path.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            private_key_path: private key path string

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_private_key_path(ptr, private_key_path)

    def set_private_key_passphrase(
        self, ptr: DriverPointer, private_key_passphrase: c_char_p
    ) -> int:
        """
        Set the private key passphrase.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            private_key_passphrase: private key passphrase string

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_private_key_passphrase(ptr, private_key_passphrase)

    def set_lookup_key_value(
        self,
        ptr: DriverPointer,
        key: c_char_p,
        value: c_char_p,
    ) -> int:
        """
        Set a lookup key/value pair.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            key: the name of the key
            value: the value of the key

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_lookup_key_value(ptr, key, value)

    def set_in_session_auth_bypass(
        self,
        ptr: DriverPointer,
    ) -> int:
        """
        Enable the in session auth bypass.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_in_session_auth_bypass(
            ptr,
        )

    def set_username_pattern(self, ptr: DriverPointer, pattern: c_char_p) -> int:
        """
        Set the username pattern.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            pattern: username pattern string

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_username_pattern(ptr, pattern)

    def set_password_pattern(self, ptr: DriverPointer, pattern: c_char_p) -> int:
        """
        Set the password pattern.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            pattern: password pattern string

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_password_pattern(ptr, pattern)

    def set_private_key_passphrase_pattern(self, ptr: DriverPointer, pattern: c_char_p) -> int:
        """
        Set the private key passphrase pattern.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            pattern: private key passphrase pattern string

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_private_key_passphrase_pattern(ptr, pattern)


class LibScrapliTransportBinOptionsMapping:
    """
    Mapping to libscrapli bin (default) transport option setter exported functions.

    Should not be used/called directly.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(self, lib: CDLL) -> None:
        self._set_bin: Callable[[DriverPointer, c_char_p], int] = lib.ls_option_transport_bin_bin
        lib.ls_option_transport_bin_bin.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_transport_bin_bin.restype = c_uint8

        self._set_extra_open_args: Callable[[DriverPointer, c_char_p], int] = (
            lib.ls_option_transport_bin_extra_open_args
        )
        lib.ls_option_transport_bin_extra_open_args.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_transport_bin_extra_open_args.restype = c_uint8

        self._set_override_open_args: Callable[[DriverPointer, c_char_p], int] = (
            lib.ls_option_transport_bin_override_open_args
        )
        lib.ls_option_transport_bin_override_open_args.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_transport_bin_override_open_args.restype = c_uint8

        self._set_ssh_config_path: Callable[[DriverPointer, c_char_p], int] = (
            lib.ls_option_transport_bin_ssh_config_path
        )
        lib.ls_option_transport_bin_ssh_config_path.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_transport_bin_ssh_config_path.restype = c_uint8

        self._set_known_hosts_path: Callable[[DriverPointer, c_char_p], int] = (
            lib.ls_option_transport_bin_known_hosts_path
        )
        lib.ls_option_transport_bin_known_hosts_path.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_transport_bin_known_hosts_path.restype = c_uint8

        self._set_enable_strict_key: Callable[[DriverPointer], int] = (
            lib.ls_option_transport_bin_enable_strict_key
        )
        lib.ls_option_transport_bin_enable_strict_key.argtypes = [
            DriverPointer,
        ]
        lib.ls_option_transport_bin_enable_strict_key.restype = c_uint8

        self._set_term_height: Callable[[DriverPointer, c_int], int] = (
            lib.ls_option_transport_bin_term_height
        )
        lib.ls_option_transport_bin_term_height.argtypes = [
            DriverPointer,
            c_int,
        ]
        lib.ls_option_transport_bin_term_height.restype = c_uint8

        self._set_term_width: Callable[[DriverPointer, c_int], int] = (
            lib.ls_option_transport_bin_term_width
        )
        lib.ls_option_transport_bin_term_width.argtypes = [
            DriverPointer,
            c_int,
        ]
        lib.ls_option_transport_bin_term_width.restype = c_uint8

    def set_bin(self, ptr: DriverPointer, bin_: c_char_p) -> int:
        """
        Set bin transport binary file to exec.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            bin_: path to the bin to use

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_bin(ptr, bin_)

    def set_extra_open_args(
        self,
        ptr: DriverPointer,
        extra_open_args: c_char_p,
    ) -> int:
        """
        Set bin transport extra open args.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            extra_open_args: extra open args

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_extra_open_args(
            ptr,
            extra_open_args,
        )

    def set_override_open_args(
        self,
        ptr: DriverPointer,
        override_open_args: c_char_p,
    ) -> int:
        """
        Set bin transport extra open args.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            override_open_args: override open args

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_override_open_args(
            ptr,
            override_open_args,
        )

    def set_ssh_config_path(self, ptr: DriverPointer, path: c_char_p) -> int:
        """
        Set bin transport ssh config file path.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            path: the path to the ssh config file

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_ssh_config_path(ptr, path)

    def set_known_hosts_path(self, ptr: DriverPointer, path: c_char_p) -> int:
        """
        Set bin transport known hosts file path.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            path: the path to the known hosts file

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_known_hosts_path(ptr, path)

    def set_enable_strict_key(
        self,
        ptr: DriverPointer,
    ) -> int:
        """
        Set bin transport strict key checking

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_enable_strict_key(
            ptr,
        )

    def set_term_height(self, ptr: DriverPointer, height: c_int) -> int:
        """
        Set bin transport terminal height

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            height: size of terminal height

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_term_height(ptr, height)

    def set_term_width(self, ptr: DriverPointer, width: c_int) -> int:
        """
        Set bin transport terminal width

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            width: size of terminal width

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_term_width(ptr, width)


class LibScrapliTransportSsh2OptionsMapping:
    """
    Mapping to libscrapli ssh2 transport option setter exported functions.

    Should not be used/called directly.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(self, lib: CDLL) -> None:
        self._set_libssh2_trace: Callable[[DriverPointer], int] = (
            lib.ls_option_transport_ssh2_libssh2trace
        )
        lib.ls_option_transport_ssh2_libssh2trace.argtypes = [
            DriverPointer,
        ]
        lib.ls_option_transport_ssh2_libssh2trace.restype = c_uint8

    def set_libssh2_trace(self, ptr: DriverPointer) -> int:
        """
        Set ssh2 transport libssh2 trace

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_libssh2_trace(ptr)


class LibScrapliTransportTelnetOptionsMapping:
    """
    Mapping to libscrapli telnet transport option setter exported functions.

    Should not be used/called directly.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(self, lib: CDLL) -> None:
        _ = lib


class LibScrapliTransportTestOptionsMapping:
    """
    Mapping to libscrapli test transport option setter exported functions.

    Should not be used/called directly.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(self, lib: CDLL) -> None:
        self._set_f: Callable[[DriverPointer, c_char_p], int] = lib.ls_option_transport_test_f
        lib.ls_option_transport_test_f.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_transport_test_f.restype = c_int

    def set_f(self, ptr: DriverPointer, f: c_char_p) -> int:
        """
        Set test transport f

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            f: file to read/load

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_f(ptr, f)


class LibScrapliOptionsMapping:
    """
    Mapping to libscrapli option setter exported functions.

    Should not be used/called directly.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(self, lib: CDLL) -> None:
        self.session = LibScrapliSessionOptionsMapping(lib)
        self.auth = LibScrapliAuthOptionsMapping(lib)
        self.transport_bin = LibScrapliTransportBinOptionsMapping(lib)
        self.transport_ssh2 = LibScrapliTransportSsh2OptionsMapping(lib)
        self.transport_telnet = LibScrapliTransportTelnetOptionsMapping(lib)
        self.transport_test = LibScrapliTransportTestOptionsMapping(lib)


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
        if not cls._instance:
            cls._instance = super(LibScrapliMapping, cls).__new__(cls)

        return cls._instance

    def __init__(self) -> None:
        self.lib = CDLL(get_libscrapli_path())
        self.shared_mapping = LibScrapliSharedMapping(self.lib)
        self.cli_mapping = LibScrapliCliMapping(self.lib)
        self.netconf_mapping = LibScrapliNetconfMapping(self.lib)
        self.options_mapping = LibScrapliOptionsMapping(self.lib)
