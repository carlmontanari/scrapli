"""scrapli.ffi_mapping_cli"""

from collections.abc import Callable
from ctypes import (
    CDLL,
    c_bool,
    c_char_p,
    c_int,
    c_uint8,
)

from _ctypes import POINTER

from scrapli.ffi_types import (
    CANCEL,
    BoolPointer,
    CancelPointer,
    DriverPointer,
    IntPointer,
    LogFuncCallback,
    OperationId,
    OperationIdPointer,
    U64Pointer,
    ZigSlice,
    ZigSlicePointer,
    ZigU64Slice,
)


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
        ] = lib.ls_cli_alloc
        lib.ls_cli_alloc.argtypes = [
            c_char_p,
            LogFuncCallback,
            c_char_p,
            c_int,
            c_char_p,
        ]
        lib.ls_cli_alloc.restype = DriverPointer

        self._get_ntc_templates_platform: Callable[
            [
                DriverPointer,
                ZigSlicePointer,
            ],
            int,
        ] = lib.ls_cli_get_ntc_templates_platform
        lib.ls_cli_get_ntc_templates_platform.argtypes = [
            DriverPointer,
            POINTER(ZigSlice),
        ]
        lib.ls_cli_get_ntc_templates_platform.restype = c_uint8

        self._get_genie_platform: Callable[
            [
                DriverPointer,
                ZigSlicePointer,
            ],
            int,
        ] = lib.ls_cli_get_genie_platform
        lib.ls_cli_get_genie_platform.argtypes = [
            DriverPointer,
            POINTER(ZigSlice),
        ]
        lib.ls_cli_get_genie_platform.restype = c_uint8

        self._open: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
            ],
            int,
        ] = lib.ls_cli_open
        lib.ls_cli_open.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
        ]
        lib.ls_cli_open.restype = c_uint8

        self._close: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
            ],
            int,
        ] = lib.ls_cli_close
        lib.ls_cli_close.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
        ]
        lib.ls_cli_close.restype = c_uint8

        self._fetch_sizes: Callable[
            [
                DriverPointer,
                OperationId,
                IntPointer,
                IntPointer,
                IntPointer,
                IntPointer,
                IntPointer,
                IntPointer,
            ],
            int,
        ] = lib.ls_cli_fetch_operation_sizes
        lib.ls_cli_fetch_operation_sizes.argtypes = [
            DriverPointer,
            OperationId,
            IntPointer,
            IntPointer,
            IntPointer,
            IntPointer,
            IntPointer,
            IntPointer,
        ]
        lib.ls_cli_fetch_operation_sizes.restype = c_uint8

        self._fetch: Callable[
            [
                DriverPointer,
                OperationId,
                IntPointer,
                ZigU64Slice,
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
            U64Pointer,
            POINTER(ZigU64Slice),
            POINTER(ZigSlice),
            POINTER(ZigSlice),
            POINTER(ZigSlice),
            POINTER(ZigSlice),
            POINTER(ZigSlice),
        ]
        lib.ls_cli_fetch_operation.restype = c_uint8

        self._enter_mode: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
                c_char_p,
            ],
            int,
        ] = lib.ls_cli_enter_mode
        lib.ls_cli_enter_mode.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
            c_char_p,
        ]
        lib.ls_cli_enter_mode.restype = c_uint8

        self._get_prompt: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
            ],
            int,
        ] = lib.ls_cli_get_prompt
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
                c_char_p,
                c_char_p,
                c_char_p,
                c_bool,
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
            c_char_p,
            c_char_p,
            c_char_p,
            c_bool,
            c_bool,
        ]
        lib.ls_cli_send_prompted_input.restype = c_uint8

        self._read_any: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
            ],
            int,
        ] = lib.ls_cli_read_any
        lib.ls_cli_read_any.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
        ]
        lib.ls_cli_read_any.restype = c_uint8

        self._read_callback_should_execute: Callable[
            [
                c_char_p,
                c_char_p,
                c_char_p,
                c_char_p,
                c_char_p,
                BoolPointer,
            ],
            int,
        ] = lib.ls_cli_read_callback_should_execute
        lib.ls_cli_read_callback_should_execute.argtypes = [
            c_char_p,
            c_char_p,
            c_char_p,
            c_char_p,
            c_char_p,
            POINTER(c_bool),
        ]
        lib.ls_cli_read_callback_should_execute.restype = c_uint8

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

    def get_ntc_templates_platform(
        self,
        *,
        ptr: DriverPointer,
        ntc_templates_platform: ZigSlicePointer,
    ) -> int:
        """
        Writes the ntc templates platform into the given slice pointer.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            ntc_templates_platform: slice to write the ntc templates platform into

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._get_ntc_templates_platform(
            ptr,
            ntc_templates_platform,
        )

    def get_genie_platform(
        self,
        *,
        ptr: DriverPointer,
        genie_platform: ZigSlicePointer,
    ) -> int:
        """
        Writes the (cisco/pyats) genie platform into the given slice pointer.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            genie_platform: slice to write the ntc templates platform into

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._get_genie_platform(
            ptr,
            genie_platform,
        )

    def open(
        self,
        ptr: DriverPointer,
        operation_id: OperationIdPointer,
    ) -> int:
        """
        Open the driver at ptr.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscrapli cli object.
            operation_id: c_int pointer that is filled with the operation id to poll for completion.

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._open(
            ptr,
            operation_id,
            CANCEL,
        )

    def close(
        self,
        ptr: DriverPointer,
        operation_id: OperationIdPointer,
    ) -> int:
        """
        Close the driver at ptr.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscrapli cli object.
            operation_id: c_int pointer that is filled with the operation id to poll for completion.

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._close(
            ptr,
            operation_id,
            CANCEL,
        )

    def fetch_sizes(
        self,
        *,
        ptr: DriverPointer,
        operation_id: OperationId,
        operation_count: IntPointer,
        inputs_size: IntPointer,
        results_raw_size: IntPointer,
        results_size: IntPointer,
        results_failed_indicator_size: IntPointer,
        err_size: IntPointer,
    ) -> int:
        """
        Fetch the sizes of a cli operation's results.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            operation_id: operation id of which to poll
            operation_count: int pointer to fill with the count of operations
            inputs_size: int pointer to fill with the operation's input size
            results_raw_size: int pointer to fill with the operation's result raw size
            results_size:  int pointer to fill with the operation's result size
            results_failed_indicator_size: int pointer to fill with the operation's failed indicator
                size
            err_size: int pointer to fill with the operation's error size

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._fetch_sizes(
            ptr,
            operation_id,
            operation_count,
            inputs_size,
            results_raw_size,
            results_size,
            results_failed_indicator_size,
            err_size,
        )

    def fetch(
        self,
        *,
        ptr: DriverPointer,
        operation_id: OperationId,
        start_time: U64Pointer,
        splits: ZigU64Slice,
        inputs_slice: ZigSlicePointer,
        results_raw_slice: ZigSlicePointer,
        results_slice: ZigSlicePointer,
        results_failed_indicator_slice: ZigSlicePointer,
        err_slice: ZigSlicePointer,
    ) -> int:
        """
        Fetch the result of a cli operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            operation_id: operation id of which to poll
            start_time: int pointer to fill with the operation's start time
            splits: slice of u64 timestamps -- the end time (in unix ns) for each operation
            inputs_slice: pre allocated slice to fill with the operations input
            results_raw_slice: pre allocated slice to fill with the operations result raw
            results_slice: pre allocated slice to fill with the operations result
            results_failed_indicator_slice: pre allocated slice to fill with the operations failed
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
            splits,
            inputs_slice,
            results_raw_slice,
            results_slice,
            results_failed_indicator_slice,
            err_slice,
        )

    def enter_mode(
        self,
        *,
        ptr: DriverPointer,
        operation_id: OperationIdPointer,
        requested_mode: c_char_p,
    ) -> int:
        """
        Enter the given mode for the cli object.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            operation_id: int pointer to fill with the id of the submitted operation
            requested_mode: string name of the mode to enter

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._enter_mode(
            ptr,
            operation_id,
            CANCEL,
            requested_mode,
        )

    def get_prompt(
        self,
        *,
        ptr: DriverPointer,
        operation_id: OperationIdPointer,
    ) -> int:
        """
        Get the current prompt for the cli object.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            operation_id: int pointer to fill with the id of the submitted operation

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._get_prompt(
            ptr,
            operation_id,
            CANCEL,
        )

    def send_input(
        self,
        *,
        ptr: DriverPointer,
        operation_id: OperationIdPointer,
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
            input_: the input to send
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
            CANCEL,
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
        input_: c_char_p,
        prompt: c_char_p,
        prompt_pattern: c_char_p,
        response: c_char_p,
        abort_input: c_char_p,
        requested_mode: c_char_p,
        input_handling: c_char_p,
        hidden_response: c_bool,
        retain_trailing_prompt: c_bool,
    ) -> int:
        """
        Send some prompted input to the cli object.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            operation_id: int pointer to fill with the id of the submitted operation
            input_: the input to send
            prompt: the prompt to expect
            prompt_pattern: the prompt pattern to expect
            response: the response to write when the prompt has been seen
            abort_input: the input to send to abort the "prompted input" operation if an error
                is encountered
            requested_mode: string name of the mode to send the input in
            input_handling: string mapping to input handling enum that governs how the input is
                handled
            hidden_response: bool indicated if the response we write will be "hidden" on the device
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
            CANCEL,
            input_,
            prompt,
            prompt_pattern,
            response,
            abort_input,
            requested_mode,
            input_handling,
            hidden_response,
            retain_trailing_prompt,
        )

    def read_any(self, ptr: DriverPointer, operation_id: OperationIdPointer) -> int:
        """
        Read any available data from the session, up to the normal timeout behavior.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscrapli cli/netconf object.
            operation_id: int pointer to fill with the id of the submitted operation

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._read_any(
            ptr,
            operation_id,
            CANCEL,
        )

    def read_callback_should_execute(
        self,
        buf: c_char_p,
        name: c_char_p,
        contains: c_char_p,
        contains_pattern: c_char_p,
        not_contains: c_char_p,
        execute: BoolPointer,
    ) -> int:
        """
        Decide if a callback should execute for read_with_callbacks operations.

        Should (generally) not be called directly/by users.

        Done in zig due to regex checks and wanting to ensure we always use pcre2 (vs go re, py re).

        Args:
            buf: the buf to use to check if the callback should execute
            name: the name of the callback
            contains: the contains string to check for in the buf -- if found, the callback should
                execute
            contains_pattern: a string pattern that, if found, indicates the callback should execute
            not_contains: string that contains data that should not be in the buf for hte callback
                to execute
            execute: bool pointer to update w/ execution state

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._read_callback_should_execute(
            buf,
            name,
            contains,
            contains_pattern,
            not_contains,
            execute,
        )
