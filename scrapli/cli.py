"""scrapli.cli"""  # pylint: disable=too-many-lines

import importlib.resources
from asyncio import sleep as async_sleep
from ctypes import (
    c_bool,
    c_char_p,
    c_int,
    c_uint,
    c_uint64,
)
from enum import Enum
from logging import getLogger
from pathlib import Path
from random import randint
from types import TracebackType
from typing import Callable, Optional, Type

from scrapli.auth import Options as AuthOptions
from scrapli.cli_decorators import handle_operation_timeout, handle_operation_timeout_async
from scrapli.cli_result import Result
from scrapli.exceptions import (
    AllocationException,
    CloseException,
    GetResultException,
    NotOpenedException,
    OpenException,
    OperationException,
    OptionsException,
    SubmitOperationException,
)
from scrapli.ffi_mapping import LibScrapliMapping
from scrapli.ffi_types import (
    BoolPointer,
    CancelPointer,
    DriverPointer,
    IntPointer,
    LogFuncCallback,
    OperationIdPointer,
    UnixTimestampPointer,
    ZigSlice,
    ZigU64Slice,
    to_c_string,
)
from scrapli.session import (
    DEFAULT_READ_DELAY_BACKOFF_FACTOR,
    DEFAULT_READ_DELAY_MAX_NS,
    DEFAULT_READ_DELAY_MIN_NS,
    READ_DELAY_MULTIPLIER,
)
from scrapli.session import Options as SessionOptions
from scrapli.transport import Options as TransportOptions


class InputHandling(str, Enum):
    """
    Enum representing the input handling flavor.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    EXACT = "exact"
    FUZZY = "fuzzy"
    IGNORE = "ignore"


class Cli:  # pylint: disable=too-many-instance-attributes
    """
    Cli represents a cli connection object.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        definition_file_or_name: str,
        host: str,
        *,
        logger_callback: Optional[Callable[[int, str], None]] = None,
        port: int = 22,
        auth_options: Optional[AuthOptions] = None,
        session_options: Optional[SessionOptions] = None,
        transport_options: Optional[TransportOptions] = None,
        logging_uid: Optional[str] = None,
    ) -> None:
        logger_name = f"{__name__}.{host}:{port}"
        if logging_uid is not None:
            logger_name += f":{logging_uid}"

        self.logger = getLogger(logger_name)

        self.ffi_mapping = LibScrapliMapping()

        self.definition_file_or_name = definition_file_or_name
        self._load_definition(definition_file_or_name=definition_file_or_name)

        # note: many places have encodings done prior to function calls such that the encoded
        # result is not gc'd prior to being used in zig-land, so it looks a bit weird, but thats
        # why. in this case we also just store the host since thats cheap and we need it as a string
        # in places too
        self.host = host
        self._host = to_c_string(host)

        self.logger_callback = (
            LogFuncCallback(logger_callback) if logger_callback else LogFuncCallback(0)
        )

        self.port = port

        self.auth_options = auth_options or AuthOptions()
        self.session_options = session_options or SessionOptions()
        self.transport_options = transport_options or TransportOptions()

        self.ptr: Optional[DriverPointer] = None

    def __enter__(self: "Cli") -> "Cli":
        """
        Enter method for context manager

        Args:
            N/A

        Returns:
            Cli: a concrete implementation of the opened Cli object

        Raises:
            N/A

        """
        self.open()

        return self

    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """
        Exit method to cleanup for context manager

        Args:
            exception_type: exception type being raised
            exception_value: message from exception being raised
            traceback: traceback from exception being raised

        Returns:
            None

        Raises:
            N/A

        """
        self.close()

    async def __aenter__(self: "Cli") -> "Cli":
        """
        Enter method for context manager

        Args:
            N/A

        Returns:
            Cli: a concrete implementation of the opened Cli object

        Raises:
            N/A

        """
        await self.open_async()

        return self

    async def __aexit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """
        Exit method to cleanup for context manager

        Args:
            exception_type: exception type being raised
            exception_value: message from exception being raised
            traceback: traceback from exception being raised

        Returns:
            None

        Raises:
            N/A

        """
        await self.close_async()

    def __str__(self) -> str:
        """
        Magic str method for Cli object

        Args:
            N/A

        Returns:
            str: str representation of Cli

        Raises:
            N/A

        """
        return f"scrapli.Cli {self.host}:{self.port}"

    def __repr__(self) -> str:
        """
        Magic repr method for Cli object

        Args:
            N/A

        Returns:
            str: repr for Cli object

        Raises:
            N/A

        """
        return (
            f"{self.__class__.__name__}("
            f"definition_file_or_name={self.definition_file_or_name!r}, "
            f"host={self.host!r}, "
            f"port={self.port!r}, "
            f"auth_options={self.auth_options!r} "
            f"session_options={self.auth_options!r} "
            f"transport_options={self.transport_options!r}) "
        )

    def _load_definition(self, definition_file_or_name: str) -> None:
        with importlib.resources.path(
            "scrapli.definitions", f"{definition_file_or_name}.yaml"
        ) as source_lib_definition:
            if Path(source_lib_definition).exists():
                with open(source_lib_definition, "rb") as f:
                    self.definition_string = f.read()

                return

        if Path(definition_file_or_name).exists():
            with open(definition_file_or_name, "rb") as f:
                self.definition_string = f.read()

        raise OptionsException(
            f"definition platform name or filename '{definition_file_or_name}' not found"
        )

    def _ptr_or_exception(self) -> DriverPointer:
        if self.ptr is None:
            raise NotOpenedException

        return self.ptr

    def _alloc(
        self,
    ) -> None:
        ptr = self.ffi_mapping.cli_mapping.alloc(
            definition_string=c_char_p(self.definition_string),
            logger_callback=self.logger_callback,
            host=self._host,
            port=c_int(self.port),
            transport_kind=c_char_p(self.transport_options.get_transport_kind()),
        )
        if ptr == 0:  # type: ignore[comparison-overlap]
            raise AllocationException("failed to allocate cli")

        self.ptr = ptr

    def _free(
        self,
    ) -> None:
        self.ffi_mapping.shared_mapping.free(ptr=self._ptr_or_exception())

    def _open(self) -> c_uint:
        self._alloc()

        self.auth_options.apply(self.ffi_mapping, self._ptr_or_exception())
        self.session_options.apply(self.ffi_mapping, self._ptr_or_exception())
        self.transport_options.apply(self.ffi_mapping, self._ptr_or_exception())

        operation_id = OperationIdPointer(c_uint(0))
        cancel = CancelPointer(c_bool(False))

        status = self.ffi_mapping.shared_mapping.open(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
        )
        if status != 0:
            self._free()

            raise OpenException("failed to submit open operation")

        # cast it again, for mypy reasons
        return c_uint(operation_id.contents.value)

    def open(
        self,
    ) -> Result:
        """
        Open the cli connection.

        Args:
            N/A

        Returns:
            None

        Raises:
            OpenException: if the operation fails

        """
        operation_id = self._open()

        return self._get_result(operation_id=operation_id)

    async def open_async(self) -> Result:
        """
        Open the cli connection.

        Args:
            N/A

        Returns:
            None

        Raises:
            OpenException: if the operation fails

        """
        operation_id = self._open()

        return await self._get_result_async(operation_id=operation_id)

    def _close(self) -> c_uint:
        operation_id = OperationIdPointer(c_uint(0))
        cancel = CancelPointer(c_bool(False))

        status = self.ffi_mapping.shared_mapping.close(
            ptr=self._ptr_or_exception(), operation_id=operation_id, cancel=cancel
        )
        if status != 0:
            raise CloseException("submitting close operation")

        return c_uint(operation_id.contents.value)

    def close(
        self,
    ) -> Result:
        """
        Close the cli connection.

        Args:
            N/A

        Returns:
            None

        Raises:
            NotOpenedException: if the ptr to the cli object is None (via _ptr_or_exception)
            CloseException: if the operation fails

        """
        operation_id = self._close()

        result = self._get_result(operation_id=operation_id)

        self._free()

        return result

    async def close_async(
        self,
    ) -> Result:
        """
        Close the cli connection.

        Args:
            N/A

        Returns:
            None

        Raises:
            NotOpenedException: if the ptr to the cli object is None (via _ptr_or_exception)
            CloseException: if the operation fails

        """
        operation_id = self._close()

        result = await self._get_result_async(operation_id=operation_id)

        self._free()

        return result

    @staticmethod
    def _get_poll_delay(
        current_delay: int, min_delay: int, max_delay: int, backoff_factor: int
    ) -> int:
        new_delay = current_delay
        new_delay *= backoff_factor

        if new_delay > max_delay:
            return max_delay * READ_DELAY_MULTIPLIER

        return new_delay + randint(0, min_delay) * READ_DELAY_MULTIPLIER

    def _get_result(  # pylint: disable=too-many-locals
        self,
        operation_id: c_uint,
    ) -> Result:
        done = BoolPointer(c_bool(False))
        operation_count = IntPointer(c_int())
        inputs_size = IntPointer(c_int())
        results_raw_size = IntPointer(c_int())
        results_size = IntPointer(c_int())
        results_failed_indicator_size = IntPointer(c_int())
        err_size = IntPointer(c_int())

        # in sync flavor we call the blocking wait to limit the number of calls to the c abi
        status = self.ffi_mapping.cli_mapping.wait(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            done=done,
            operation_count=operation_count,
            inputs_size=inputs_size,
            results_raw_size=results_raw_size,
            results_size=results_size,
            results_failed_indicator_size=results_failed_indicator_size,
            err_size=err_size,
        )
        if status != 0:
            raise GetResultException("wait operation failed")

        start_time = UnixTimestampPointer(c_uint64())
        splits = ZigU64Slice(size=operation_count.contents)

        inputs_slice = ZigSlice(size=inputs_size.contents)
        results_raw_slice = ZigSlice(size=results_raw_size.contents)
        results_slice = ZigSlice(size=results_size.contents)

        results_failed_indicator_slice = ZigSlice(size=results_failed_indicator_size.contents)
        err_slice = ZigSlice(size=err_size.contents)

        status = self.ffi_mapping.cli_mapping.fetch(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            start_time=start_time,
            splits=splits,
            inputs_slice=inputs_slice,
            results_raw_slice=results_raw_slice,
            results_slice=results_slice,
            results_failed_indicator_slice=results_failed_indicator_slice,
            err_slice=err_slice,
        )
        if status != 0:
            raise GetResultException("fetch operation failed")

        err_contents = err_slice.get_decoded_contents()
        if err_contents:
            raise OperationException(err_contents)

        return Result(
            inputs=inputs_slice.get_decoded_contents(),
            host=self.host,
            port=self.port,
            start_time=start_time.contents.value,
            splits=splits.get_contents(),
            results_raw=results_raw_slice.get_contents(),
            results=results_slice.get_decoded_contents(),
            results_failed_indicator=results_failed_indicator_slice.get_decoded_contents(),
        )

    async def _get_result_async(  # pylint: disable=too-many-locals
        self,
        operation_id: c_uint,
    ) -> Result:
        min_delay = self.session_options.read_delay_min_ns or DEFAULT_READ_DELAY_MIN_NS
        max_delay = self.session_options.read_delay_max_ns or DEFAULT_READ_DELAY_MAX_NS
        backoff_factor = (
            self.session_options.read_delay_backoff_factor or DEFAULT_READ_DELAY_BACKOFF_FACTOR
        )
        current_delay = min_delay

        done = BoolPointer(c_bool(False))
        operation_count = IntPointer(c_int())
        inputs_size = IntPointer(c_int())
        results_raw_size = IntPointer(c_int())
        results_size = IntPointer(c_int())
        results_failed_indicator_size = IntPointer(c_int())
        err_size = IntPointer(c_int())

        while True:
            status = self.ffi_mapping.cli_mapping.poll(
                ptr=self._ptr_or_exception(),
                operation_id=operation_id,
                done=done,
                operation_count=operation_count,
                inputs_size=inputs_size,
                results_raw_size=results_raw_size,
                results_size=results_size,
                results_failed_indicator_size=results_failed_indicator_size,
                err_size=err_size,
            )
            if status != 0:
                raise GetResultException("poll operation failed")

            if done.contents.value is True:
                break

            # ns to seconds
            await async_sleep(current_delay / 1_000_000_000)

            current_delay = self._get_poll_delay(
                current_delay=current_delay,
                min_delay=min_delay,
                max_delay=max_delay,
                backoff_factor=backoff_factor,
            )

        start_time = UnixTimestampPointer(c_uint64())
        splits = ZigU64Slice(size=operation_count.contents)

        inputs_slice = ZigSlice(size=inputs_size.contents)
        results_raw_slice = ZigSlice(size=results_raw_size.contents)
        results_slice = ZigSlice(size=results_size.contents)

        results_failed_indicator_slice = ZigSlice(size=results_failed_indicator_size.contents)
        err_slice = ZigSlice(size=err_size.contents)

        status = self.ffi_mapping.cli_mapping.fetch(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            start_time=start_time,
            splits=splits,
            inputs_slice=inputs_slice,
            results_raw_slice=results_raw_slice,
            results_slice=results_slice,
            results_failed_indicator_slice=results_failed_indicator_slice,
            err_slice=err_slice,
        )
        if status != 0:
            raise GetResultException("fetch operation failed")

        err_contents = err_slice.get_decoded_contents()
        if err_contents:
            raise OperationException(err_contents)

        return Result(
            inputs=inputs_slice.get_decoded_contents(),
            host=self.host,
            port=self.port,
            start_time=start_time.contents.value,
            splits=splits.get_contents(),
            results_raw=results_raw_slice.get_contents(),
            results=results_slice.get_decoded_contents(),
            results_failed_indicator=results_failed_indicator_slice.get_decoded_contents(),
        )

    def _enter_mode(
        self,
        *,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
        requested_mode: c_char_p,
    ) -> c_uint:
        status = self.ffi_mapping.cli_mapping.enter_mode(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
            requested_mode=requested_mode,
        )
        if status != 0:
            raise SubmitOperationException("submitting get prompt operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def enter_mode(
        self,
        requested_mode: str,
        *,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Enter the given mode on the cli connection.

        Args:
            requested_mode: name of the mode to enter
            operation_timeout_ns: operation timeout in ns for this operation

        Returns:
            Result: a Result object representing the operation

        Raises:
            NotOpenedException: if the ptr to the cli object is None (via _ptr_or_exception)
            SubmitOperationException: if the operation fails

        """
        # only used in the decorator
        _ = operation_timeout_ns

        operation_id = OperationIdPointer(c_uint(0))
        cancel = CancelPointer(c_bool(False))

        _requested_mode = to_c_string(requested_mode)

        operation_id = self._enter_mode(
            operation_id=operation_id, cancel=cancel, requested_mode=_requested_mode
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def enter_mode_async(
        self,
        requested_mode: str,
        *,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Enter the given mode on the cli connection.

        Args:
            requested_mode: name of the mode to enter
            operation_timeout_ns: operation timeout in ns for this operation

        Returns:
            Result: a Result object representing the operation

        Raises:
            NotOpenedException: if the ptr to the cli object is None (via _ptr_or_exception)
            SubmitOperationException: if the operation fails

        """
        # only used in the decorator
        _ = operation_timeout_ns

        operation_id = OperationIdPointer(c_uint(0))
        cancel = CancelPointer(c_bool(False))

        _requested_mode = to_c_string(requested_mode)

        operation_id = self._enter_mode(
            operation_id=operation_id, cancel=cancel, requested_mode=_requested_mode
        )

        return await self._get_result_async(operation_id=operation_id)

    def _get_prompt(
        self,
        *,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
    ) -> c_uint:
        status = self.ffi_mapping.cli_mapping.get_prompt(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
        )
        if status != 0:
            raise SubmitOperationException("submitting get prompt operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def get_prompt(
        self,
        *,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Get the current prompt of the cli connection.

        Args:
            operation_timeout_ns: operation timeout in ns for this operation

        Returns:
            Result: a Result object representing the operation

        Raises:
            NotOpenedException: if the ptr to the cli object is None (via _ptr_or_exception)
            SubmitOperationException: if the operation fails

        """
        # only used in the decorator
        _ = operation_timeout_ns

        operation_id = OperationIdPointer(c_uint(0))
        cancel = CancelPointer(c_bool(False))

        operation_id = self._get_prompt(operation_id=operation_id, cancel=cancel)

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def get_prompt_async(
        self,
        *,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Get the current prompt of the cli connection.

        Args:
            operation_timeout_ns: operation timeout in ns for this operation

        Returns:
            Result: a Result object representing the operation

        Raises:
            NotOpenedException: if the ptr to the cli object is None (via _ptr_or_exception)
            SubmitOperationException: if the operation fails

        """
        # only used in the decorator
        _ = operation_timeout_ns

        operation_id = OperationIdPointer(c_uint(0))
        cancel = CancelPointer(c_bool(False))

        operation_id = self._get_prompt(operation_id=operation_id, cancel=cancel)

        return await self._get_result_async(operation_id=operation_id)

    def _send_input(  # pylint: disable=too-many-arguments
        self,
        *,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
        input_: c_char_p,
        requested_mode: c_char_p,
        input_handling: c_char_p,
        retain_input: c_bool,
        retain_trailing_prompt: c_bool,
    ) -> c_uint:
        status = self.ffi_mapping.cli_mapping.send_input(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
            input_=input_,
            requested_mode=requested_mode,
            input_handling=input_handling,
            retain_input=retain_input,
            retain_trailing_prompt=retain_trailing_prompt,
        )
        if status != 0:
            raise SubmitOperationException("submitting send input operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def send_input(  # pylint: disable=too-many-arguments
        self,
        input_: str,
        *,
        requested_mode: str = "",
        input_handling: InputHandling = InputHandling.FUZZY,
        retain_input: bool = False,
        retain_trailing_prompt: bool = False,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Send an input on the cli connection.

        Args:
            input_: the input to send
            requested_mode: name of the mode to send the input at
            input_handling: how to handle the input
            retain_input: retain the input in the final "result"
            retain_trailing_prompt: retain the trailing prompt in the final "result"
            operation_timeout_ns: operation timeout in ns for this operation

        Returns:
            Result: a Result object representing the operation

        Raises:
            NotOpenedException: if the ptr to the cli object is None (via _ptr_or_exception)
            SubmitOperationException: if the operation fails

        """
        # only used in the decorator
        _ = operation_timeout_ns

        operation_id = OperationIdPointer(c_uint(0))
        cancel = CancelPointer(c_bool(False))

        _input = to_c_string(input_)
        _requested_mode = to_c_string(requested_mode)
        _input_handling = to_c_string(input_handling)

        operation_id = self._send_input(
            operation_id=operation_id,
            cancel=cancel,
            input_=_input,
            requested_mode=_requested_mode,
            input_handling=_input_handling,
            retain_input=c_bool(retain_input),
            retain_trailing_prompt=c_bool(retain_trailing_prompt),
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def send_input_async(  # pylint: disable=too-many-arguments
        self,
        input_: str,
        *,
        requested_mode: str = "",
        input_handling: InputHandling = InputHandling.FUZZY,
        retain_input: bool = False,
        retain_trailing_prompt: bool = False,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Send an input on the cli connection.

        Args:
            input_: the input to send
            requested_mode: name of the mode to send the input at
            input_handling: how to handle the input
            retain_input: retain the input in the final "result"
            retain_trailing_prompt: retain the trailing prompt in the final "result"
            operation_timeout_ns: operation timeout in ns for this operation

        Returns:
            Result: a Result object representing the operation

        Raises:
            NotOpenedException: if the ptr to the cli object is None (via _ptr_or_exception)
            SubmitOperationException: if the operation fails

        """
        # only used in the decorator
        _ = operation_timeout_ns

        operation_id = OperationIdPointer(c_uint(0))
        cancel = CancelPointer(c_bool(False))

        _input = to_c_string(input_)
        _requested_mode = to_c_string(requested_mode)
        _input_handling = to_c_string(input_handling)

        operation_id = self._send_input(
            operation_id=operation_id,
            cancel=cancel,
            input_=_input,
            requested_mode=_requested_mode,
            input_handling=_input_handling,
            retain_input=c_bool(retain_input),
            retain_trailing_prompt=c_bool(retain_trailing_prompt),
        )

        return await self._get_result_async(operation_id=operation_id)

    @handle_operation_timeout
    def send_inputs(  # pylint: disable=too-many-arguments, too-many-locals
        self,
        inputs: list[str],
        *,
        requested_mode: str = "",
        input_handling: InputHandling = InputHandling.FUZZY,
        retain_input: bool = False,
        retain_trailing_prompt: bool = False,
        stop_on_indicated_failure: bool = True,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Send inputs (plural!) on the cli connection.

        Args:
            inputs: the inputs to send
            requested_mode: name of the mode to send the input at`
            input_handling: how to handle the input
            retain_input: retain the input in the final "result"
            retain_trailing_prompt: retain the trailing prompt in the final "result"
            stop_on_indicated_failure: stops sending inputs at first indicated failure
            operation_timeout_ns: operation timeout in ns for this operation

        Returns:
            Result: a Result object representing the operation

        Raises:
            NotOpenedException: if the ptr to the cli object is None (via _ptr_or_exception)
            SubmitOperationException: if the operation fails

        """
        # only used in the decorator; note that the timeout here is for the whole operation,
        # meaning all the "inputs" combined, not individually
        _ = operation_timeout_ns

        operation_id = OperationIdPointer(c_uint(0))
        cancel = CancelPointer(c_bool(False))

        result: Optional[Result] = None

        for input_ in inputs:
            _input = to_c_string(input_)
            _requested_mode = to_c_string(requested_mode)
            _input_handling = to_c_string(input_handling)

            operation_id = self._send_input(
                operation_id=operation_id,
                cancel=cancel,
                input_=_input,
                requested_mode=_requested_mode,
                input_handling=_input_handling,
                retain_input=c_bool(retain_input),
                retain_trailing_prompt=c_bool(retain_trailing_prompt),
            )

            _result = self._get_result(operation_id=operation_id)

            if result is None:
                result = _result
            else:
                result.extend(result=_result)

            if result.failed and stop_on_indicated_failure:
                return result

        return result  # type: ignore[return-value]

    @handle_operation_timeout_async
    async def send_inputs_async(  # pylint: disable=too-many-arguments, too-many-locals
        self,
        inputs: list[str],
        *,
        requested_mode: str = "",
        input_handling: InputHandling = InputHandling.FUZZY,
        retain_input: bool = False,
        retain_trailing_prompt: bool = False,
        stop_on_indicated_failure: bool = True,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Send inputs (plural!) on the cli connection.

        Args:
            inputs: the inputs to send
            requested_mode: name of the mode to send the input at`
            input_handling: how to handle the input
            retain_input: retain the input in the final "result"
            retain_trailing_prompt: retain the trailing prompt in the final "result"
            stop_on_indicated_failure: stops sending inputs at first indicated failure
            operation_timeout_ns: operation timeout in ns for this operation

        Returns:
            MultiResult: a MultiResult object representing the operations

        Raises:
            NotOpenedException: if the ptr to the cli object is None (via _ptr_or_exception)
            SubmitOperationException: if the operation fails

        """
        # only used in the decorator; note that the timeout here is for the whole operation,
        # meaning all the "inputs" combined, not individually
        _ = operation_timeout_ns

        operation_id = OperationIdPointer(c_uint(0))
        cancel = CancelPointer(c_bool(False))

        result: Optional[Result] = None

        for input_ in inputs:
            _input = to_c_string(input_)
            _requested_mode = to_c_string(requested_mode)
            _input_handling = to_c_string(input_handling)

            operation_id = self._send_input(
                operation_id=operation_id,
                cancel=cancel,
                input_=_input,
                requested_mode=_requested_mode,
                input_handling=_input_handling,
                retain_input=c_bool(retain_input),
                retain_trailing_prompt=c_bool(retain_trailing_prompt),
            )

            _result = await self._get_result_async(operation_id=operation_id)
            if result is None:
                result = _result
            else:
                result.extend(result=_result)

            if result.failed and stop_on_indicated_failure:
                return result

        return result  # type: ignore[return-value]

    def _send_prompted_input(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        *,
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
    ) -> c_uint:
        status = self.ffi_mapping.cli_mapping.send_prompted_input(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
            input_=input_,
            prompt=prompt,
            prompt_pattern=prompt_pattern,
            response=response,
            hidden_response=hidden_response,
            requested_mode=requested_mode,
            input_handling=input_handling,
            retain_trailing_prompt=retain_trailing_prompt,
        )
        if status != 0:
            raise SubmitOperationException("submitting send prompted input operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def send_prompted_input(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        input_: str,
        prompt: str,
        prompt_pattern: str,
        response: str,
        *,
        hidden_response: bool = False,
        requested_mode: str = "",
        input_handling: InputHandling = InputHandling.FUZZY,
        retain_trailing_prompt: bool = False,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Send a prompted input on the cli connection.

        Args:
            input_: the input to send
            prompt: the prompt to respond to (must set this or prompt_pattern)
            prompt_pattern: the prompt pattern to respond to (must set this or prompt)
            response: the response to send to the prompt
            hidden_response: if the response input will be hidden (like for a password prompt)
            requested_mode: name of the mode to send the input at
            input_handling: how to handle the input
            retain_trailing_prompt: retain the trailing prompt in the final "result"
            operation_timeout_ns: operation timeout in ns for this operation

        Returns:
            Result: a Result object representing the operation

        Raises:
            NotOpenedException: if the ptr to the cli object is None (via _ptr_or_exception)
            SubmitOperationException: if the operation fails

        """
        # only used in the decorator
        _ = operation_timeout_ns

        operation_id = OperationIdPointer(c_uint(0))
        cancel = CancelPointer(c_bool(False))

        _input = to_c_string(input_)
        _prompt = to_c_string(prompt)
        _prompt_pattern = to_c_string(prompt_pattern)
        _response = to_c_string(response)
        _requested_mode = to_c_string(requested_mode)
        _input_handling = to_c_string(input_handling)

        operation_id = self._send_prompted_input(
            operation_id=operation_id,
            cancel=cancel,
            input_=_input,
            prompt=_prompt,
            prompt_pattern=_prompt_pattern,
            response=_response,
            hidden_response=c_bool(hidden_response),
            requested_mode=_requested_mode,
            input_handling=_input_handling,
            retain_trailing_prompt=c_bool(retain_trailing_prompt),
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def send_prompted_input_async(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        input_: str,
        prompt: str,
        prompt_pattern: str,
        response: str,
        *,
        hidden_response: bool = False,
        requested_mode: str = "",
        input_handling: InputHandling = InputHandling.FUZZY,
        retain_trailing_prompt: bool = False,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Send a prompted input on the cli connection.

        Args:
            input_: the input to send
            prompt: the prompt to respond to (must set this or prompt_pattern)
            prompt_pattern: the prompt pattern to respond to (must set this or prompt)
            response: the response to send to the prompt
            hidden_response: if the response input will be hidden (like for a password prompt)
            requested_mode: name of the mode to send the input at
            input_handling: how to handle the input
            retain_trailing_prompt: retain the trailing prompt in the final "result"
            operation_timeout_ns: operation timeout in ns for this operation

        Returns:
            Result: a Result object representing the operation

        Raises:
            NotOpenedException: if the ptr to the cli object is None (via _ptr_or_exception)
            SubmitOperationException: if the operation fails

        """
        # only used in the decorator
        _ = operation_timeout_ns

        operation_id = OperationIdPointer(c_uint(0))
        cancel = CancelPointer(c_bool(False))

        _input = to_c_string(input_)
        _prompt = to_c_string(prompt)
        _prompt_pattern = to_c_string(prompt_pattern)
        _response = to_c_string(response)
        _requested_mode = to_c_string(requested_mode)
        _input_handling = to_c_string(input_handling)

        operation_id = self._send_prompted_input(
            operation_id=operation_id,
            cancel=cancel,
            input_=_input,
            prompt=_prompt,
            prompt_pattern=_prompt_pattern,
            response=_response,
            hidden_response=c_bool(hidden_response),
            requested_mode=_requested_mode,
            input_handling=_input_handling,
            retain_trailing_prompt=c_bool(retain_trailing_prompt),
        )

        return await self._get_result_async(operation_id=operation_id)
