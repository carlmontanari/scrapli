"""scrapli.ffi_mapping_cli"""

from collections.abc import Callable
from ctypes import (
    CDLL,
    c_bool,
    c_char_p,
    c_uint8,
    c_uint32,
    c_void_p,
)

from scrapli.ffi_types import (
    CANCEL,
    BoolPointer,
    CancelPointer,
    DriverPointer,
    LibScrapliFFIResult,
    OperationId,
    OperationIdPointer,
    U8Pointer,
    U32Pointer,
    U64Pointer,
    USizePointer,
    ZigSlicePointer,
    ZigU64SlicePointer,
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
                c_void_p,
            ],
            DriverPointer,
        ] = lib.ls_cli_alloc
        lib.ls_cli_alloc.argtypes = [
            c_char_p,
            c_void_p,
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
            ZigSlicePointer,
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
            ZigSlicePointer,
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
                U32Pointer,
                USizePointer,
                USizePointer,
                USizePointer,
                USizePointer,
                USizePointer,
                USizePointer,
            ],
            int,
        ] = lib.ls_cli_fetch_operation_sizes
        lib.ls_cli_fetch_operation_sizes.argtypes = [
            DriverPointer,
            OperationId,
            U32Pointer,
            USizePointer,
            USizePointer,
            USizePointer,
            USizePointer,
            USizePointer,
            USizePointer,
        ]
        lib.ls_cli_fetch_operation_sizes.restype = c_uint8

        self._fetch: Callable[
            [
                DriverPointer,
                OperationId,
                U64Pointer,
                ZigU64SlicePointer,
                ZigSlicePointer,
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
            ZigU64SlicePointer,
            ZigSlicePointer,
            ZigSlicePointer,
            ZigSlicePointer,
            ZigSlicePointer,
            ZigSlicePointer,
            ZigSlicePointer,
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
                U8Pointer,
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
            U8Pointer,
            c_bool,
            c_bool,
        ]
        lib.ls_cli_send_input.restype = c_uint8

        self._send_inputs: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
                c_char_p,
                c_char_p,
                U8Pointer,
                c_bool,
                c_bool,
                c_bool,
            ],
            int,
        ] = lib.ls_cli_send_inputs
        lib.ls_cli_send_inputs.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
            c_char_p,
            c_char_p,
            U8Pointer,
            c_bool,
            c_bool,
            c_bool,
        ]
        lib.ls_cli_send_inputs.restype = c_uint8

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
                U8Pointer,
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
            U8Pointer,
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
            BoolPointer,
        ]
        lib.ls_cli_read_callback_should_execute.restype = c_uint8

        self._replace_definition: Callable[
            [
                DriverPointer,
                c_char_p,
            ],
            int,
        ] = lib.ls_cli_replace_definition
        lib.ls_cli_replace_definition.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_cli_replace_definition.restype = c_uint8

    def alloc(
        self,
        *,
        host: c_char_p,
        options_ptr: c_void_p,
    ) -> DriverPointer:
        """
        Allocate a cli object.

        Should (generally) not be called directly/by users.

        Args:
            host: host to connect to
            options_ptr: the pointer to the options struct

        Returns:
            DriverPointer: the pointer to the allocated cli object.

        Raises:
            N/A

        """
        return self._alloc(
            host,
            options_ptr,
        )

    def get_ntc_templates_platform(
        self,
        *,
        ptr: DriverPointer,
        ntc_templates_platform: ZigSlicePointer,
    ) -> None:
        """
        Writes the ntc templates platform into the given slice pointer.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            ntc_templates_platform: slice to write the ntc templates platform into

        Returns:
            N/A

        Raises:
            FFIException: if the platform cant be retreived

        """
        LibScrapliFFIResult(
            self._get_ntc_templates_platform(
                ptr,
                ntc_templates_platform,
            )
        ).raise_if_error(
            message="failed to retrieve ntc templates platform",
        )

    def get_genie_platform(
        self,
        *,
        ptr: DriverPointer,
        genie_platform: ZigSlicePointer,
    ) -> None:
        """
        Writes the (cisco/pyats) genie platform into the given slice pointer.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            genie_platform: slice to write the ntc templates platform into

        Returns:
            N/A

        Raises:
            FFIException: if the platform cant be retreived

        """
        LibScrapliFFIResult(
            self._get_genie_platform(
                ptr,
                genie_platform,
            )
        ).raise_if_error(
            message="failed to retrieve genie platform",
        )

    def open(
        self,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
    ) -> None:
        """
        Open the driver at ptr.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscrapli cli object.
            operation_id_ptr: c_int pointer that is filled with the operation id to poll for
                completion.

        Returns:
            N/A

        Raises:
            FFIException: if the open operation isnt successfully submitted

        """
        LibScrapliFFIResult(
            self._open(
                ptr,
                operation_id_ptr,
                CANCEL,
            )
        ).raise_if_error(
            message="failed submitting open operation",
        )

    def close(
        self,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
    ) -> None:
        """
        Close the driver at ptr.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscrapli cli object.
            operation_id_ptr: c_int pointer that is filled with the operation id to poll for
                completion.

        Returns:
            N/A

        Raises:
            FFIException: if the close operation isnt successfully submitted

        """
        LibScrapliFFIResult(
            self._close(
                ptr,
                operation_id_ptr,
                CANCEL,
            )
        ).raise_if_error(
            message="failed submitting close operation",
        )

    def fetch_sizes(
        self,
        *,
        ptr: DriverPointer,
        operation_id_value: OperationId,
        operation_count: U32Pointer,
        inputs_size: USizePointer,
        results_raw_size: USizePointer,
        results_size: USizePointer,
        results_failed_indicator_size: USizePointer,
        err_size: USizePointer,
        last_err_str_size: USizePointer,
    ) -> None:
        """
        Fetch the sizes of a cli operation's results.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            operation_id_value: operation id of which to fetch
            operation_count: int pointer to fill with the count of operations
            inputs_size: int pointer to fill with the operation's input size
            results_raw_size: int pointer to fill with the operation's result raw size
            results_size:  int pointer to fill with the operation's result size
            results_failed_indicator_size: int pointer to fill with the operation's failed indicator
                size
            err_size: int pointer to fill with the operation's error size
            last_err_str_size: int pointer to fill with the operation's last error string size

        Returns:
            N/A

        Raises:
            FFIException: if the operation sizes cant be fetched

        """
        LibScrapliFFIResult(
            self._fetch_sizes(
                ptr,
                operation_id_value,
                operation_count,
                inputs_size,
                results_raw_size,
                results_size,
                results_failed_indicator_size,
                err_size,
                last_err_str_size,
            )
        ).raise_if_error(
            message="fetching operation sizes failed",
        )

    def fetch(
        self,
        *,
        ptr: DriverPointer,
        operation_id_value: c_uint32,
        start_time: U64Pointer,
        splits: ZigU64SlicePointer,
        inputs_slice: ZigSlicePointer,
        results_raw_slice: ZigSlicePointer,
        results_slice: ZigSlicePointer,
        results_failed_indicator_slice: ZigSlicePointer,
        err_slice: ZigSlicePointer,
        last_err_string: ZigSlicePointer,
    ) -> None:
        """
        Fetch the result of a cli operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            operation_id_value: operation id of which to fetch
            start_time: int pointer to fill with the operation's start time
            splits: slice of u64 timestamps -- the end time (in unix ns) for each operation
            inputs_slice: pre allocated slice to fill with the operations input
            results_raw_slice: pre allocated slice to fill with the operations result raw
            results_slice: pre allocated slice to fill with the operations result
            results_failed_indicator_slice: pre allocated slice to fill with the operations failed
                indicator
            err_slice: pre allocated slice to fill with the operations error
            last_err_string: pre allocated slice to fill with the operations last error string

        Returns:
            N/A

        Raises:
            FFIException: if the operation results cant be fetched

        """
        LibScrapliFFIResult(
            self._fetch(
                ptr,
                operation_id_value,
                start_time,
                splits,
                inputs_slice,
                results_raw_slice,
                results_slice,
                results_failed_indicator_slice,
                err_slice,
                last_err_string,
            )
        ).raise_if_error(
            message="fetching operation content failed",
        )

    def enter_mode(
        self,
        *,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
        requested_mode: c_char_p,
    ) -> None:
        """
        Enter the given mode for the cli object.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            operation_id_ptr: int pointer to fill with the id of the submitted operation
            requested_mode: string name of the mode to enter

        Returns:
            N/A

        Raises:
            FFIException: if submitting the enter mode operation failed

        """
        LibScrapliFFIResult(
            self._enter_mode(
                ptr,
                operation_id_ptr,
                CANCEL,
                requested_mode,
            )
        ).raise_if_error(
            message="submitting enter mode operation failed",
        )

    def get_prompt(
        self,
        *,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
    ) -> None:
        """
        Get the current prompt for the cli object.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            operation_id_ptr: int pointer to fill with the id of the submitted operation

        Returns:
            N/A

        Raises:
            FFIException: if submitting the get prompt operation failed

        """
        LibScrapliFFIResult(
            self._get_prompt(
                ptr,
                operation_id_ptr,
                CANCEL,
            )
        ).raise_if_error(
            message="submitting get prompt operation failed",
        )

    def send_input(
        self,
        *,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
        input_: c_char_p,
        requested_mode: c_char_p,
        input_handling: U8Pointer,
        retain_input: c_bool,
        retain_trailing_prompt: c_bool,
    ) -> None:
        """
        Send some input to the cli object.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            operation_id_ptr: int pointer to fill with the id of the submitted operation
            input_: the input to send
            requested_mode: string name of the mode to send the input in
            input_handling: u8 mapping to input handling enum that governs how the input is
                handled
            retain_input: boolean indicating whether to retain the input after entering
            retain_trailing_prompt: boolean indicating whether to retain the trailing

        Returns:
            N/A

        Raises:
            FFIException: if submitting the send input operation failed

        """
        LibScrapliFFIResult(
            self._send_input(
                ptr,
                operation_id_ptr,
                CANCEL,
                input_,
                requested_mode,
                input_handling,
                retain_input,
                retain_trailing_prompt,
            )
        ).raise_if_error(
            message="submitting send input operation failed",
        )

    def send_inputs(
        self,
        *,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
        inputs: c_char_p,
        requested_mode: c_char_p,
        input_handling: U8Pointer,
        retain_input: c_bool,
        retain_trailing_prompt: c_bool,
        stop_on_indicated_failure: c_bool,
    ) -> None:
        """
        Send some input to the cli object.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            operation_id_ptr: int pointer to fill with the id of the submitted operation
            inputs: the inputs to send, joined on the libscrapli delimiter
            requested_mode: string name of the mode to send the input in
            input_handling: u8 mapping to input handling enum that governs how the input is
                handled
            retain_input: boolean indicating whether to retain the input after entering
            retain_trailing_prompt: boolean indicating whether to retain the trailing
            stop_on_indicated_failure: indiciates if we should stop at first sign of a failure as
                indicated by the "failed when" values (of the platform).

        Returns:
            N/A

        Raises:
            FFIException: if submitting the send inputs operation failed

        """
        LibScrapliFFIResult(
            self._send_inputs(
                ptr,
                operation_id_ptr,
                CANCEL,
                inputs,
                requested_mode,
                input_handling,
                retain_input,
                retain_trailing_prompt,
                stop_on_indicated_failure,
            )
        ).raise_if_error(
            message="submitting send inputs operation failed",
        )

    def send_prompted_input(
        self,
        *,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
        input_: c_char_p,
        prompt: c_char_p,
        prompt_pattern: c_char_p,
        response: c_char_p,
        abort_input: c_char_p,
        requested_mode: c_char_p,
        input_handling: U8Pointer,
        hidden_response: c_bool,
        retain_trailing_prompt: c_bool,
    ) -> None:
        """
        Send some prompted input to the cli object.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the cli object
            operation_id_ptr: int pointer to fill with the id of the submitted operation
            input_: the input to send
            prompt: the prompt to expect
            prompt_pattern: the prompt pattern to expect
            response: the response to write when the prompt has been seen
            abort_input: the input to send to abort the "prompted input" operation if an error
                is encountered
            requested_mode: string name of the mode to send the input in
            input_handling: u8 mapping to input handling enum that governs how the input is
                handled
            hidden_response: bool indicated if the response we write will be "hidden" on the device
            retain_trailing_prompt: boolean indicating whether to retain the trailing

        Returns:
            N/A

        Raises:
            FFIException: if submitting the send prompted input operation failed

        """
        LibScrapliFFIResult(
            self._send_prompted_input(
                ptr,
                operation_id_ptr,
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
        ).raise_if_error(
            message="submitting send prompted input operation failed",
        )

    def read_any(
        self,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
    ) -> None:
        """
        Read any available data from the session, up to the normal timeout behavior.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscrapli cli/netconf object.
            operation_id_ptr: pointer to fill with the id of the submitted operation

        Returns:
            N/A

        Raises:
            FFIException: if submitting the read any operation failed

        """
        LibScrapliFFIResult(
            self._read_any(
                ptr,
                operation_id_ptr,
                CANCEL,
            )
        ).raise_if_error(
            message="submitting read any operation failed",
        )

    def read_callback_should_execute(
        self,
        buf: c_char_p,
        name: c_char_p,
        contains: c_char_p,
        contains_pattern: c_char_p,
        not_contains: c_char_p,
        execute: BoolPointer,
    ) -> None:
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
            N/A

        Raises:
            FFIException: if submitting the read any operation failed

        """
        LibScrapliFFIResult(
            self._read_callback_should_execute(
                buf,
                name,
                contains,
                contains_pattern,
                not_contains,
                execute,
            )
        ).raise_if_error(
            message="failed checking if callback should execute",
        )

    def replace_definition(
        self,
        ptr: DriverPointer,
        definition_string: c_char_p,
    ) -> None:
        """
        Replace the "definition" of the driver at driver ptr.

        Most importantly changes/updates the prompt pattern, but also updates the modes etc.
        available in the driver.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscrapli cli/netconf object.
            definition_string: string content of the definition to pass to zig.

        Returns:
            N/A

        Raises:
            FFIException: if replacing the definition failed

        """
        LibScrapliFFIResult(
            self._replace_definition(
                ptr,
                definition_string,
            )
        ).raise_if_error(
            message="failed replacing cli definition",
        )
