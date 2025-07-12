"""scrapli.cli"""

import importlib.resources
from collections.abc import Awaitable, Callable
from ctypes import (
    c_bool,
    c_char_p,
    c_int,
    c_uint,
    c_uint64,
    pointer,
)
from dataclasses import dataclass
from enum import Enum
from logging import getLogger
from os import environ
from pathlib import Path
from time import time_ns
from types import TracebackType
from typing import Any

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
    DriverPointer,
    IntPointer,
    OperationIdPointer,
    U64Pointer,
    ZigSlice,
    ZigU64Slice,
    ffi_logger_wrapper,
    to_c_string,
)
from scrapli.helper import (
    resolve_file,
    wait_for_available_operation_result,
    wait_for_available_operation_result_async,
)
from scrapli.session import Options as SessionOptions
from scrapli.transport import BinOptions as TransportBinOptions
from scrapli.transport import Options as TransportOptions

CLI_DEFINITIONS_PATH_OVERRIDE_ENV = "SCRAPLI_DEFINITIONS_PATH"
CLI_DEFINITIONS_PATH_OVERRIDE = environ.get(CLI_DEFINITIONS_PATH_OVERRIDE_ENV)


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


@dataclass
class ReadCallback:
    """
    ReadCallback represents a callback and how it should be executed in a read_with_callbacks op.

    Args:
        name: friendly name for the callback
        contains: string that when contained in the buf being processed indicates this callback
            should be executed
        contains_pattern: string representing a pcre2 pattern that, if found in the buf being
            processed indicates this callback should be executed -- note: ignored if contains is set
        not_contains: a string that if found in the buf being processed nullifies the containment
            check
        once: bool indicating if this is an "only once" callback or if it can be executed multiple
            times
        completes: bool indicated if, after execution, this callback should "complete" (end) the
            read_with_callbacks operation
        callback: the callback func to execute

    Returns:
        None

    Raises:
        N/A

    """

    name: str
    contains: str = ""
    contains_pattern: str = ""
    not_contains: str = ""
    once: bool = False
    completes: bool = False
    callback: Callable[["Cli"], None] | None = None
    callback_async: Callable[["Cli"], Awaitable[None]] | None = None

    def __post_init__(self) -> None:
        if not self.contains and not self.contains_pattern:
            raise OperationException("one of 'contains' or 'contains_pattern' must be set")

        if self.callback is None and self.callback_async is None:
            raise OperationException("one of 'callback' or 'callback_async' must be set")


class Cli:
    """
    Cli represents a cli connection object.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(  # noqa: PLR0913
        self,
        definition_file_or_name: str,
        host: str,
        *,
        port: int = 22,
        auth_options: AuthOptions | None = None,
        session_options: SessionOptions | None = None,
        transport_options: TransportOptions | None = None,
        logging_uid: str | None = None,
    ) -> None:
        logger_name = f"{__name__}.{host}:{port}"
        if logging_uid is not None:
            logger_name += f":{logging_uid}"

        self.logger = getLogger(logger_name)
        self.logger_callback = ffi_logger_wrapper(logger=self.logger)
        self._logging_uid = logging_uid

        self.ffi_mapping = LibScrapliMapping()

        self.definition_file_or_name = definition_file_or_name
        self._load_definition(definition_file_or_name=definition_file_or_name)

        # note: many places have encodings done prior to function calls such that the encoded
        # result is not gc'd prior to being used in zig-land, so it looks a bit weird, but thats
        # why. in this case we also just store the host since thats cheap and we need it as a string
        # in places too
        self.host = host
        self._host = to_c_string(s=host)

        self.port = port

        self.auth_options = auth_options or AuthOptions()
        self.session_options = session_options or SessionOptions()
        self.transport_options = transport_options or TransportBinOptions()

        self.ptr: DriverPointer | None = None
        self.poll_fd: int = 0

        self._ntc_templates_platform: str | None = None
        self._genie_platform: str | None = None

    def __enter__(self: "Cli") -> "Cli":
        """
        Enter method for context manager.

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
        exception_type: BaseException | None,
        exception_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """
        Exit method to cleanup for context manager.

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
        Enter method for context manager.

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
        exception_type: BaseException | None,
        exception_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """
        Exit method to cleanup for context manager.

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
        Magic str method for Cli object.

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
        Magic repr method for Cli object.

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

    def __copy__(self, memodict: dict[Any, Any] = {}) -> "Cli":
        # reasonably safely copy of the object... *reasonably*... basically assumes that options
        # will never be mutated during an objects lifetime, which *should* be the case. probably.
        return Cli(
            host=self.host,
            definition_file_or_name=self.definition_file_or_name,
            port=self.port,
            auth_options=self.auth_options,
            session_options=self.session_options,
            transport_options=self.transport_options,
            logging_uid=self._logging_uid,
        )

    def _load_definition(self, definition_file_or_name: str) -> None:
        if CLI_DEFINITIONS_PATH_OVERRIDE is not None:
            definition_path = f"{CLI_DEFINITIONS_PATH_OVERRIDE}/{definition_file_or_name}.yaml"
        else:
            definitions_path = importlib.resources.files("scrapli.definitions")
            definition_path = f"{definitions_path}/{definition_file_or_name}.yaml"

        if Path(definition_path).exists():
            with open(definition_path, "rb") as f:
                self.definition_string = f.read()

            return

        if Path(definition_file_or_name).exists():
            with open(definition_file_or_name, "rb") as f:
                self.definition_string = f.read()

            return

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
            transport_kind=c_char_p(self.transport_options.transport_kind.encode(encoding="utf-8")),
        )
        if ptr == 0:  # type: ignore[comparison-overlap]
            raise AllocationException("failed to allocate cli")

        self.ptr = ptr

        poll_fd = int(
            self.ffi_mapping.shared_mapping.get_poll_fd(
                ptr=self._ptr_or_exception(),
            )
        )
        if poll_fd <= 0:
            raise AllocationException("failed to allocate cli")

        self.poll_fd = poll_fd

    def _free(
        self,
    ) -> None:
        self.ffi_mapping.shared_mapping.free(ptr=self._ptr_or_exception())

    @property
    def ntc_templates_platform(self) -> str:
        """
        Returns the ntc templates platform for the cli object.

        Args:
            N/A

        Returns:
            str: the ntc templates platform name

        Raises:
            N/A

        """
        if self._ntc_templates_platform is not None:
            return self._ntc_templates_platform

        ntc_templates_platform = ZigSlice(size=c_int(256))

        status = self.ffi_mapping.cli_mapping.get_ntc_templates_platform(
            ptr=self._ptr_or_exception(),
            ntc_templates_platform=ntc_templates_platform,
        )
        if status != 0:
            raise GetResultException("failed to retrieve ntc templates platform")

        self._ntc_templates_platform = ntc_templates_platform.get_decoded_contents().strip("\x00")

        return self._ntc_templates_platform

    @property
    def genie_platform(self) -> str:
        """
        Returns the genie platform for the cli object.

        Args:
            N/A

        Returns:
            str: the genie platform name

        Raises:
            N/A

        """
        if self._genie_platform is not None:
            return self._genie_platform

        genie_platform = ZigSlice(size=c_int(256))

        status = self.ffi_mapping.cli_mapping.get_ntc_templates_platform(
            ptr=self._ptr_or_exception(),
            ntc_templates_platform=genie_platform,
        )
        if status != 0:
            raise GetResultException("failed to retrieve genie templates platform")

        self._genie_platform = genie_platform.get_decoded_contents().strip("\x00")

        return self._genie_platform

    def _open(
        self,
        *,
        operation_id: OperationIdPointer,
    ) -> None:
        self._alloc()

        self.auth_options.apply(self.ffi_mapping, self._ptr_or_exception())
        self.session_options.apply(self.ffi_mapping, self._ptr_or_exception())
        self.transport_options.apply(self.ffi_mapping, self._ptr_or_exception())

        status = self.ffi_mapping.cli_mapping.open(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
        )
        if status != 0:
            self._free()

            raise OpenException("failed to submit open operation")

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
        operation_id = OperationIdPointer(c_uint(0))

        self._open(operation_id=operation_id)

        return self._get_result(operation_id=operation_id.contents.value)

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
        operation_id = OperationIdPointer(c_uint(0))

        self._open(operation_id=operation_id)

        return await self._get_result_async(operation_id=operation_id.contents.value)

    def _close(
        self,
        *,
        operation_id: OperationIdPointer,
    ) -> None:
        status = self.ffi_mapping.cli_mapping.close(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
        )
        if status != 0:
            raise CloseException("submitting close operation")

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
        operation_id = OperationIdPointer(c_uint(0))

        self._close(operation_id=operation_id)

        result = self._get_result(operation_id=operation_id.contents.value)

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
        operation_id = OperationIdPointer(c_uint(0))

        self._close(operation_id=operation_id)

        result = await self._get_result_async(operation_id=operation_id.contents.value)

        self._free()

        return result

    def write(self, input_: str) -> None:
        """
        Write the given input.

        Args:
            input_: the input to write

        Returns:
            Result: a Result object representing the operation

        Raises:
            NotOpenedException: if the ptr to the cli object is None (via _ptr_or_exception)
            SubmitOperationException: if the operation fails

        """
        _input = to_c_string(s=input_)

        status = self.ffi_mapping.session_mapping.write(
            ptr=self._ptr_or_exception(),
            input_=_input,
            redacted=c_bool(False),
        )
        if status != 0:
            raise SubmitOperationException("executing write and return operation failed")

        _ = _input

    def write_and_return(self, input_: str) -> None:
        """
        Write the given input then send a return character.

        Args:
            input_: the input to write

        Returns:
            Result: a Result object representing the operation

        Raises:
            NotOpenedException: if the ptr to the cli object is None (via _ptr_or_exception)
            SubmitOperationException: if the operation fails

        """
        _input = to_c_string(s=input_)

        status = self.ffi_mapping.session_mapping.write_and_return(
            ptr=self._ptr_or_exception(),
            input_=_input,
            redacted=c_bool(False),
        )
        if status != 0:
            raise SubmitOperationException("executing write and return operation failed")

        _ = _input

    def _get_result(
        self,
        operation_id: c_uint,
    ) -> Result:
        wait_for_available_operation_result(self.poll_fd)

        operation_count = IntPointer(c_int())
        inputs_size = IntPointer(c_int())
        results_raw_size = IntPointer(c_int())
        results_size = IntPointer(c_int())
        results_failed_indicator_size = IntPointer(c_int())
        err_size = IntPointer(c_int())

        status = self.ffi_mapping.cli_mapping.fetch_sizes(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            operation_count=operation_count,
            inputs_size=inputs_size,
            results_raw_size=results_raw_size,
            results_size=results_size,
            results_failed_indicator_size=results_failed_indicator_size,
            err_size=err_size,
        )
        if status != 0:
            raise GetResultException("wait operation failed")

        start_time = U64Pointer(c_uint64())
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
            textfsm_platform=self.ntc_templates_platform,
            genie_platform=self.genie_platform,
        )

    async def _get_result_async(
        self,
        operation_id: c_uint,
    ) -> Result:
        await wait_for_available_operation_result_async(fd=self.poll_fd)

        operation_count = IntPointer(c_int())
        inputs_size = IntPointer(c_int())
        results_raw_size = IntPointer(c_int())
        results_size = IntPointer(c_int())
        results_failed_indicator_size = IntPointer(c_int())
        err_size = IntPointer(c_int())

        status = self.ffi_mapping.cli_mapping.fetch_sizes(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            operation_count=operation_count,
            inputs_size=inputs_size,
            results_raw_size=results_raw_size,
            results_size=results_size,
            results_failed_indicator_size=results_failed_indicator_size,
            err_size=err_size,
        )
        if status != 0:
            raise GetResultException("fetch operation sizes failed")

        start_time = U64Pointer(c_uint64())
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
            textfsm_platform=self.ntc_templates_platform,
            genie_platform=self.genie_platform,
        )

    def _enter_mode(
        self,
        *,
        operation_id: OperationIdPointer,
        requested_mode: c_char_p,
    ) -> c_uint:
        status = self.ffi_mapping.cli_mapping.enter_mode(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
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
        operation_timeout_ns: int | None = None,
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

        _requested_mode = to_c_string(requested_mode)

        operation_id = self._enter_mode(
            operation_id=operation_id,
            requested_mode=_requested_mode,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def enter_mode_async(
        self,
        requested_mode: str,
        *,
        operation_timeout_ns: int | None = None,
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

        _requested_mode = to_c_string(requested_mode)

        operation_id = self._enter_mode(
            operation_id=operation_id,
            requested_mode=_requested_mode,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _get_prompt(
        self,
        *,
        operation_id: OperationIdPointer,
    ) -> c_uint:
        status = self.ffi_mapping.cli_mapping.get_prompt(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
        )
        if status != 0:
            raise SubmitOperationException("submitting get prompt operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def get_prompt(
        self,
        *,
        operation_timeout_ns: int | None = None,
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

        operation_id = self._get_prompt(operation_id=operation_id)

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def get_prompt_async(
        self,
        *,
        operation_timeout_ns: int | None = None,
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

        operation_id = self._get_prompt(operation_id=operation_id)

        return await self._get_result_async(operation_id=operation_id)

    def _send_input(  # noqa: PLR0913
        self,
        *,
        operation_id: OperationIdPointer,
        input_: c_char_p,
        requested_mode: c_char_p,
        input_handling: c_char_p,
        retain_input: c_bool,
        retain_trailing_prompt: c_bool,
    ) -> c_uint:
        status = self.ffi_mapping.cli_mapping.send_input(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
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
    def send_input(  # noqa: PLR0913
        self,
        input_: str,
        *,
        requested_mode: str = "",
        input_handling: InputHandling = InputHandling.FUZZY,
        retain_input: bool = False,
        retain_trailing_prompt: bool = False,
        operation_timeout_ns: int | None = None,
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

        _input = to_c_string(input_)
        _requested_mode = to_c_string(requested_mode)
        _input_handling = to_c_string(input_handling)

        operation_id = self._send_input(
            operation_id=operation_id,
            input_=_input,
            requested_mode=_requested_mode,
            input_handling=_input_handling,
            retain_input=c_bool(retain_input),
            retain_trailing_prompt=c_bool(retain_trailing_prompt),
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def send_input_async(  # noqa: PLR0913
        self,
        input_: str,
        *,
        requested_mode: str = "",
        input_handling: InputHandling = InputHandling.FUZZY,
        retain_input: bool = False,
        retain_trailing_prompt: bool = False,
        operation_timeout_ns: int | None = None,
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

        _input = to_c_string(input_)
        _requested_mode = to_c_string(requested_mode)
        _input_handling = to_c_string(input_handling)

        operation_id = self._send_input(
            operation_id=operation_id,
            input_=_input,
            requested_mode=_requested_mode,
            input_handling=_input_handling,
            retain_input=c_bool(retain_input),
            retain_trailing_prompt=c_bool(retain_trailing_prompt),
        )

        return await self._get_result_async(operation_id=operation_id)

    @handle_operation_timeout
    def send_inputs(  # noqa: PLR0913
        self,
        inputs: list[str],
        *,
        requested_mode: str = "",
        input_handling: InputHandling = InputHandling.FUZZY,
        retain_input: bool = False,
        retain_trailing_prompt: bool = False,
        stop_on_indicated_failure: bool = True,
        operation_timeout_ns: int | None = None,
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

        result: Result | None = None

        for input_ in inputs:
            operation_id = OperationIdPointer(c_uint(0))

            _input = to_c_string(input_)
            _requested_mode = to_c_string(requested_mode)
            _input_handling = to_c_string(input_handling)

            operation_id = self._send_input(
                operation_id=operation_id,
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
    async def send_inputs_async(  # noqa: PLR0913
        self,
        inputs: list[str],
        *,
        requested_mode: str = "",
        input_handling: InputHandling = InputHandling.FUZZY,
        retain_input: bool = False,
        retain_trailing_prompt: bool = False,
        stop_on_indicated_failure: bool = True,
        operation_timeout_ns: int | None = None,
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

        result: Result | None = None

        for input_ in inputs:
            operation_id = OperationIdPointer(c_uint(0))

            _input = to_c_string(input_)
            _requested_mode = to_c_string(requested_mode)
            _input_handling = to_c_string(input_handling)

            operation_id = self._send_input(
                operation_id=operation_id,
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

    def send_inputs_from_file(  # noqa: PLR0913
        self,
        f: str,
        *,
        requested_mode: str = "",
        input_handling: InputHandling = InputHandling.FUZZY,
        retain_input: bool = False,
        retain_trailing_prompt: bool = False,
        stop_on_indicated_failure: bool = True,
        operation_timeout_ns: int | None = None,
    ) -> Result:
        """
        Send inputs (plural! from a file, line-by-line) on the cli connection.

        Args:
            f: the file to load -- each line will be sent, tralining newlines ignored
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
        with open(resolve_file(f), encoding="utf-8", mode="r") as _f:
            inputs = _f.read().splitlines()

        return self.send_inputs(
            inputs=inputs,
            requested_mode=requested_mode,
            input_handling=input_handling,
            retain_input=retain_input,
            retain_trailing_prompt=retain_trailing_prompt,
            stop_on_indicated_failure=stop_on_indicated_failure,
            operation_timeout_ns=operation_timeout_ns,
        )

    async def send_inputs_from_file_async(  # noqa: PLR0913
        self,
        f: str,
        *,
        requested_mode: str = "",
        input_handling: InputHandling = InputHandling.FUZZY,
        retain_input: bool = False,
        retain_trailing_prompt: bool = False,
        stop_on_indicated_failure: bool = True,
        operation_timeout_ns: int | None = None,
    ) -> Result:
        """
        Send inputs (plural! from a file, line-by-line) on the cli connection.

        Args:
            f: the file to load -- each line will be sent, tralining newlines ignored
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
        with open(resolve_file(f), encoding="utf-8", mode="r") as _f:
            inputs = _f.read().splitlines()

        return await self.send_inputs_async(
            inputs=inputs,
            requested_mode=requested_mode,
            input_handling=input_handling,
            retain_input=retain_input,
            retain_trailing_prompt=retain_trailing_prompt,
            stop_on_indicated_failure=stop_on_indicated_failure,
            operation_timeout_ns=operation_timeout_ns,
        )

    def _send_prompted_input(  # noqa: PLR0913
        self,
        *,
        operation_id: OperationIdPointer,
        input_: c_char_p,
        prompt: c_char_p,
        prompt_pattern: c_char_p,
        response: c_char_p,
        hidden_response: c_bool,
        abort_input: c_char_p,
        requested_mode: c_char_p,
        input_handling: c_char_p,
        retain_trailing_prompt: c_bool,
    ) -> c_uint:
        status = self.ffi_mapping.cli_mapping.send_prompted_input(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            input_=input_,
            prompt=prompt,
            prompt_pattern=prompt_pattern,
            response=response,
            hidden_response=hidden_response,
            abort_input=abort_input,
            requested_mode=requested_mode,
            input_handling=input_handling,
            retain_trailing_prompt=retain_trailing_prompt,
        )
        if status != 0:
            raise SubmitOperationException("submitting send prompted input operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def send_prompted_input(  # noqa: PLR0913
        self,
        input_: str,
        prompt: str,
        prompt_pattern: str,
        response: str,
        *,
        requested_mode: str = "",
        abort_input: str = "",
        input_handling: InputHandling = InputHandling.FUZZY,
        hidden_response: bool = False,
        retain_trailing_prompt: bool = False,
        operation_timeout_ns: int | None = None,
    ) -> Result:
        """
        Send a prompted input on the cli connection.

        Args:
            input_: the input to send
            prompt: the prompt to respond to (must set this or prompt_pattern)
            prompt_pattern: the prompt pattern to respond to (must set this or prompt)
            response: the response to send to the prompt
            abort_input: the input to send to abort the "prompted input" operation if an error
                is encountered
            requested_mode: name of the mode to send the input at
            input_handling: how to handle the input
            hidden_response: if the response input will be hidden (like for a password prompt)
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

        _input = to_c_string(input_)
        _prompt = to_c_string(prompt)
        _prompt_pattern = to_c_string(prompt_pattern)
        _response = to_c_string(response)
        _abort_input = to_c_string(abort_input)
        _requested_mode = to_c_string(requested_mode)
        _input_handling = to_c_string(input_handling)

        operation_id = self._send_prompted_input(
            operation_id=operation_id,
            input_=_input,
            prompt=_prompt,
            prompt_pattern=_prompt_pattern,
            response=_response,
            abort_input=_abort_input,
            requested_mode=_requested_mode,
            input_handling=_input_handling,
            hidden_response=c_bool(hidden_response),
            retain_trailing_prompt=c_bool(retain_trailing_prompt),
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def send_prompted_input_async(  # noqa: PLR0913
        self,
        input_: str,
        prompt: str,
        prompt_pattern: str,
        response: str,
        *,
        abort_input: str = "",
        requested_mode: str = "",
        input_handling: InputHandling = InputHandling.FUZZY,
        hidden_response: bool = False,
        retain_trailing_prompt: bool = False,
        operation_timeout_ns: int | None = None,
    ) -> Result:
        """
        Send a prompted input on the cli connection.

        Args:
            input_: the input to send
            prompt: the prompt to respond to (must set this or prompt_pattern)
            prompt_pattern: the prompt pattern to respond to (must set this or prompt)
            response: the response to send to the prompt
            abort_input: the input to send to abort the "prompted input" operation if an error
                is encountered
            requested_mode: name of the mode to send the input at
            input_handling: how to handle the input
            hidden_response: if the response input will be hidden (like for a password prompt)
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

        _input = to_c_string(input_)
        _prompt = to_c_string(prompt)
        _prompt_pattern = to_c_string(prompt_pattern)
        _response = to_c_string(response)
        _abort_input = to_c_string(abort_input)
        _requested_mode = to_c_string(requested_mode)
        _input_handling = to_c_string(input_handling)

        operation_id = self._send_prompted_input(
            operation_id=operation_id,
            input_=_input,
            prompt=_prompt,
            prompt_pattern=_prompt_pattern,
            response=_response,
            abort_input=_abort_input,
            requested_mode=_requested_mode,
            input_handling=_input_handling,
            hidden_response=c_bool(hidden_response),
            retain_trailing_prompt=c_bool(retain_trailing_prompt),
        )

        return await self._get_result_async(operation_id=operation_id)

    @handle_operation_timeout
    def read_with_callbacks(
        self,
        callbacks: list[ReadCallback],
        *,
        initial_input: str = "",
        operation_timeout_ns: int | None = None,
    ) -> Result:
        """
        Read from the device and react to the output with some callback.

        Args:
            callbacks: a list of callbacks to process when reading from the session
            initial_input: an initial input to send
            operation_timeout_ns: operation timeout in ns for this operation

        Returns:
            Result: a Result object representing the operation

        Raises:
            NotOpenedException: if the ptr to the cli object is None (via _ptr_or_exception)
            SubmitOperationException: if the operation fails

        """
        # only used in the decorator
        _ = operation_timeout_ns

        start_time = time_ns()

        if initial_input:
            self.write_and_return(input_=initial_input)

        pos = 0

        result = ""
        result_raw = b""

        executed_callbacks = set()

        while True:
            operation_id = OperationIdPointer(c_uint(0))

            status = self.ffi_mapping.cli_mapping.read_any(
                ptr=self._ptr_or_exception(),
                operation_id=operation_id,
            )
            if status != 0:
                raise SubmitOperationException("submitting read any operation failed")

            intermediate_result = self._get_result(operation_id=operation_id.contents.value)

            result += intermediate_result.result
            result_raw += intermediate_result.result_raw

            for callback in callbacks:
                if callback.name in executed_callbacks and callback.once:
                    continue

                execute = pointer(c_bool(False))

                status = self.ffi_mapping.cli_mapping.read_callback_should_execute(
                    buf=to_c_string(result[pos:]),
                    name=to_c_string(callback.name),
                    contains=to_c_string(callback.contains),
                    contains_pattern=to_c_string(callback.contains_pattern),
                    not_contains=to_c_string(callback.not_contains),
                    execute=execute,
                )
                if status != 0:
                    raise OperationException("failed checking if callback should execute")

                if execute.contents.value is False:
                    continue

                executed_callbacks.add(callback.name)

                pos = len(result)

                if callback.callback is None:
                    raise OperationException("callback is None, cannot proceed")
                else:
                    callback.callback(self)

                if callback.completes is True:
                    return Result(
                        inputs=initial_input,
                        host=self.host,
                        port=self.port,
                        start_time=start_time,
                        splits=[time_ns()],
                        results_raw=result_raw,
                        results=result,
                        results_failed_indicator="",
                        textfsm_platform=self.ntc_templates_platform,
                        genie_platform=self.genie_platform,
                    )

    @handle_operation_timeout_async
    async def read_with_callbacks_async(
        self,
        callbacks: list[ReadCallback],
        *,
        initial_input: str = "",
        operation_timeout_ns: int | None = None,
    ) -> Result:
        """
        Read from the device and react to the output with some callback.

        Args:
            callbacks: a list of callbacks to process when reading from the session
            initial_input: an initial input to send
            operation_timeout_ns: operation timeout in ns for this operation

        Returns:
            Result: a Result object representing the operation

        Raises:
            NotOpenedException: if the ptr to the cli object is None (via _ptr_or_exception)
            SubmitOperationException: if the operation fails

        """
        # only used in the decorator
        _ = operation_timeout_ns

        start_time = time_ns()

        if initial_input:
            self.write_and_return(input_=initial_input)

        pos = 0

        result = ""
        result_raw = b""

        executed_callbacks = set()

        while True:
            operation_id = OperationIdPointer(c_uint(0))

            status = self.ffi_mapping.cli_mapping.read_any(
                ptr=self._ptr_or_exception(),
                operation_id=operation_id,
            )
            if status != 0:
                raise SubmitOperationException("submitting read any operation failed")

            intermediate_result = await self._get_result_async(
                operation_id=operation_id.contents.value
            )

            result += intermediate_result.result
            result_raw += intermediate_result.result_raw

            for callback in callbacks:
                if callback.name in executed_callbacks and callback.once:
                    continue

                execute = pointer(c_bool(False))

                status = self.ffi_mapping.cli_mapping.read_callback_should_execute(
                    buf=to_c_string(result[pos:]),
                    name=to_c_string(callback.name),
                    contains=to_c_string(callback.contains),
                    contains_pattern=to_c_string(callback.contains_pattern),
                    not_contains=to_c_string(callback.not_contains),
                    execute=execute,
                )
                if status != 0:
                    raise OperationException("failed checking if callback should execute")

                if execute.contents.value is False:
                    continue

                executed_callbacks.add(callback.name)

                pos = len(result)

                if callback.callback is None:
                    raise OperationException("callback is None, cannot proceed")
                else:
                    callback.callback(self)

                if callback.completes is True:
                    return Result(
                        inputs=initial_input,
                        host=self.host,
                        port=self.port,
                        start_time=start_time,
                        splits=[time_ns()],
                        results_raw=result_raw,
                        results=result,
                        results_failed_indicator="",
                        textfsm_platform=self.ntc_templates_platform,
                        genie_platform=self.genie_platform,
                    )

    @staticmethod
    def ___getwide___() -> None:  # pragma: no cover
        """
        Dumb inside joke easter egg :)

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        wide = r"""
KKKXXXXXXXXXXNNNNNNNNNNNNNNNWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW
000000000000KKKKKKKKKKXXXXXXXXXXXXXXXXXNNXXK0Okxdoolllloodxk0KXNNWWNWWWWWWWWWWWWWWWWWWWWWWWWWWWWNNNN
kkkkkkkOOOOOOOOOOO00000000000000000000kdl:,...              ..';coxOKKKKKKKKKKKKXKKXXKKKXXXXXKKKK000
kkkkkkkOOOOOOOOOOOO000000000000000Od:,.                            .,cdOKKKKKKKKKKKK0000OOOOOOOOOOOO
kkkkkkkkOOOOOOOOOOO0000000000000kc'                                    .:d0KKKKKKKKK0KKOkOOOOOOOOOO0
kkkkkkkkOOOOOOOOOOOO00000000000o'                                         ,o0KKKKKKKKKKOkOOOOOOOOO00
kkkkkkkkOOOOOOOOOOOOO000000000o.                                            ;kKKKKKKKKKOkOOOOOOOOO00
OOOOOOOOOO0000000000000000K0Kk'                                              'xKKKKKKKKOkOOOOOOOOO00
KKKKKKKKKXXXXXXXXXXXXXXNNNNNNd.                                               cXNNNNNNNK0000O00O0000
KKKKKKKKKXXXXXXXXXXXXNNNNNNNXl        ...............                         :XWWWWWWWX000000000000
KKKKKKKKKXXXXXXXXXXXXXXNNNNNXc     ...''',,,,,,;;,,,,,,'''......             .xWWWWWWWWX000000000000
KKKKKKKKKKKXXXXXXXXXXXXXNNNNK;    ...',,,,;;;;;;;:::::::;;;;;;,,'.          .oNWWWWWWWNK000000OOOO00
KKKKKKKKKKKKXXXXXXXXXXXXXXXN0,  ...'',,,;;;;;;:::::::::::::::;;;;,'.       .dNWWWWWWWWNK0000OOOOOOOO
0000KKKKKKKKKKKKKXXXXXXXXXXN0, ..'',,,,;;;;;;:::::::::::::::::;;;;,,..    ;ONNNNNWWWWWNK00OOOOOOOOOO
kkkkkkOOOOOOOOOOOOOOOOOOO000k; ..,,,,,,'',,;;::::::::::::::::;;;;;;,'.  .lOKKKKXXKXXKK0OOOOOOOOOOOOO
xxxkkkkkkkkkkkkkkkkkkOOOOkdll;..',,,,,,,''...';::ccccc:::::::::;;;;;,...o0000000000000OkkOOOkkOOOOOO
xxxxxxkkkkkkkkkkkkkkkkkkOd:;;,..,;;;;;;;;;;,'',,;:ccccccccc:::;;;;;;,..cO0000000000000Oxkkkkkkkkkkkk
xxxxxxxxkkkkkkkkkkkkkkkkkl:;;,'';;;;;,'''''',,,,,;::ccc::;,,'.'''',;,,lO00000000000000kxkkkkkkkkkkkk
xxxxxxxxkkkkkkkkkkkkkkkkko::;'';;;;;;,''....,'',,,,;:c:;,,'''',,;;;;,:x00000000000000Okxkkkkkkkkkkkk
xxxxxxxxxxkkkkkkkkkkkkkkkxl;,,;;;;:::;;;,,,,,,,,,,,,:c:;,'....''',;;,;cxO000000000000Okxkkkkkkkkkkkk
kkkkOOOOOOOOOOOOOO00000000x:;;;;;:::c::::::;;;;;;;;;:c:;,,,,'',,',;:::lOKKKKKKXXXXXXKKOkkkkkkkkkkkkk
000000000000000KKKKKKKKKKK0dc;,;;:::ccccccc::::;;;;;:cc:;;;;:::::::::lOXXXXXNNNNNNNNXX0Okkkkkkkkkkkk
OO00000000000000000KKKKKKKK0d::;;;::ccccccccc:;;;;;;;:c:;::ccccccc::cOXXXXXXXXXNNNNNXX0kkkkkkkkkkkkk
OOO00000000000000000000KKKKKOxxc;;;::ccccccc:;;;;;;;:ccc:::cccllcc;:kKXXXXXXXXXXXXXXXKOkkkkkkkkkkkkk
OOOOO00000000000000000000KKK0kdl;;;;;:ccccc::;,,,,;;:clc:::cclllcc:oKXXXXXXXXXXXXXXXXKOkkkkkkkkkkkkk
OOOOOOO0000000000000000Okxdlc;,,;;::;;::cc::;;,,,,,;:::;;:cccccc::clxkO00KKKKKKKKKXKK0kkkkkkkkkkkxkk
kkkkkkkkkkkkkkkkkkkxdoc:,''.....,;:::;;;::;;;;;;;;;;;;;;;:ccc:::;,',;;:clodxkOOOOOOOOkxxxxxxxxxxxxxx
ddddddddddddddoolc;,'''..........,;;:;;;::;,,,,,;;;;;::::::c:::;'.',,;;;;;::clodxkkkkxdxxxxxxxxxxxxx
dddddddoolc::;,'''.......      ..',;;;;;;;;,'........',;::::::;;,,;;;;;;;;:::::ccloddddxxxxxxxxxxxxx
dollc:;,,''.........         ..'''',,,,;;;;;,'''.....'',::::;,,;;;::::;;,,;;;;;;;;;::cldxxxxxxdxxdxx
l;'''.''......             ..'',,''',,,,;;;::;;,,,,,,;;::;;'.....',;;,,''',,,,,,'',,,',:odxddddddddd
.............             .'',,,,,''',,,;;;;::::;::::::;;;........'''''''..'.....,,'...';cdddddddddd
. .......                .',,,,,;,,'',,,,;;;::::::::::;;cc. .....''...'''.......','......':odxdddddd
   ...                  .',,;;;;;;,'',;;,,,;;;::::::::;cxo....................''''.......'';lddddddd
    ..                  .,;,;;;;;;,,,',;;;,,,,;;;;;;;;:dKO:..................''''.. .......',cdddddd
                         ,:;;;;;,,,,;,,;::;,,,,,;::::::dK0c..................'''..  ........',codddd
                         .;:;;;;;,,;;;,,;:;;:;,,;:::::clc,...   ...........'''.... ....  .....':oddd
                          .',;;;;;;;;;,,;:;;;;,;::::::;'......       ......'.........   .....'',cood
                            ..,;;;;;;;;;;;:;;;;:::::;'.    .         ..............       ...''',:od
                              ..',;;;;:;;;:::::::,,'.              ...............        ....''.':o
                                 ...',,;;,,;,,'..                 ...............        ..  .....'c
               __              _     __....                      ................     ....   ......'
   ____ ____  / /_   _      __(_)___/ /__                    ..............   ..    ...     .......
  / __ `/ _ \/ __/  | | /| / / / __  / _ \                 ................    .             ......
 / /_/ /  __/ /_    | |/ |/ / / /_/ /  __/                .................                  ......
 \__, /\___/\__/    |__/|__/_/\__,_/\___/                  ...............                   ......
/____/                                                     ...............  ..             ........
"""
        print(wide)
