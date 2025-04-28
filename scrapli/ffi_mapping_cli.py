"""scrapli.ffi_mapping_cli"""  # pylint: disable=too-many-lines,too-many-arguments,too-many-instance-attributes

from ctypes import (
    CDLL,
    c_bool,
    c_char_p,
    c_int,
    c_uint8,
)
from typing import Callable

from _ctypes import POINTER

from scrapli.ffi_types import (
    BoolPointer,
    CancelPointer,
    DriverPointer,
    IntPointer,
    LogFuncCallback,
    OperationId,
    OperationIdPointer,
    UnixTimestampPointer,
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
        ] = lib.ls_alloc_cli
        lib.ls_alloc_cli.argtypes = [
            c_char_p,
            LogFuncCallback,
            c_char_p,
            c_int,
            c_char_p,
        ]
        lib.ls_alloc_cli.restype = DriverPointer

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

        self._wait: Callable[
            [
                DriverPointer,
                OperationId,
                BoolPointer,
                IntPointer,
                IntPointer,
                IntPointer,
                IntPointer,
                IntPointer,
                IntPointer,
            ],
            int,
        ] = lib.ls_cli_wait_operation
        lib.ls_cli_wait_operation.argtypes = [
            DriverPointer,
            OperationId,
            BoolPointer,
            IntPointer,
            IntPointer,
            IntPointer,
            IntPointer,
            IntPointer,
        ]
        lib.ls_cli_wait_operation.restype = c_uint8

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
            UnixTimestampPointer,
            POINTER(ZigU64Slice),
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

    def poll(
        self,
        *,
        ptr: DriverPointer,
        operation_id: OperationId,
        done: BoolPointer,
        operation_count: IntPointer,
        inputs_size: IntPointer,
        results_raw_size: IntPointer,
        results_size: IntPointer,
        results_failed_indicator_size: IntPointer,
        err_size: IntPointer,
    ) -> int:
        """
        Poll for the result of a cli operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            operation_id: operation id of which to poll
            done: bool pointer that is set to true if the operation has completed
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
        return self._poll(
            ptr,
            operation_id,
            done,
            operation_count,
            inputs_size,
            results_raw_size,
            results_size,
            results_failed_indicator_size,
            err_size,
        )

    def wait(
        self,
        *,
        ptr: DriverPointer,
        operation_id: OperationId,
        done: BoolPointer,
        operation_count: IntPointer,
        inputs_size: IntPointer,
        results_raw_size: IntPointer,
        results_size: IntPointer,
        results_failed_indicator_size: IntPointer,
        err_size: IntPointer,
    ) -> int:
        """
        Wait for the result of a cli operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            operation_id: operation id of which to poll
            done: bool pointer that is set to true if the operation has completed
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
        return self._wait(
            ptr,
            operation_id,
            done,
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
        start_time: UnixTimestampPointer,
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
            cancel: bool pointer that can be set to true to cancel the operation
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
            cancel,
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
