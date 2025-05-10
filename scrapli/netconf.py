"""scrapli.netconf"""

from asyncio import sleep as async_sleep
from ctypes import c_bool, c_char_p, c_int, c_uint, c_uint64
from dataclasses import dataclass, field
from enum import Enum
from logging import getLogger
from random import randint
from types import TracebackType
from typing import Callable, Optional

from scrapli.auth import Options as AuthOptions
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
    to_c_string,
)
from scrapli.netconf_decorators import handle_operation_timeout, handle_operation_timeout_async
from scrapli.netconf_result import Result
from scrapli.session import (
    DEFAULT_READ_DELAY_BACKOFF_FACTOR,
    DEFAULT_READ_DELAY_MAX_NS,
    DEFAULT_READ_DELAY_MIN_NS,
    READ_DELAY_MULTIPLIER,
)
from scrapli.session import Options as SessionOptions
from scrapli.transport import Options as TransportOptions


class Version(str, Enum):
    """
    Enum representing a netconf version

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    VERSION_1_0 = "1.0"
    VERSION_1_1 = "1.1"


class DatastoreType(str, Enum):
    """
    Enum representing the datastore types

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    CONVENTIONAL = "conventional"
    RUNNING = "running"
    CANDIDATE = "candidate"
    STARTUP = "startup"
    INTENDED = "intended"
    DYNAMIC = "dynamic"
    OPERATIONAL = "operational"


class FilterType(str, Enum):
    """
    Enum representing a filter type value

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    SUBTREE = "subtree"
    XPATH = "xpath"


class DefaultsType(str, Enum):
    """
    Enum representing a defaults type value

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    UNSET = "unset"
    REPORT_ALL = "report-all"
    REPORT_ALL_TAGGED = "report-all-tagged"
    TRIM = "trim"
    EXPLICIT = "explicit"


class SchemaFormat(str, Enum):
    """
    Enum representing valid schema formats

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    XSD = "xsd"
    YANG = "yang"
    YIN = "yin"
    RNG = "rng"
    RNC = "rnc"


class ConfigFilter(str, Enum):
    """
    Enum representing valid config filter values

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    UNSET = "unset"
    TRUE = "true"
    FALSE = "false"


@dataclass
class Options:
    """
    Options holds netconf related options to pass to the ffi layer.

    Args:
        error_tag: the error tag substring that identifies errors in an rpc reply
        preferred_version: preferred netconf version to use
        message_poll_interval_ns: interval in ns for message polling
        force_close: exists to enable sending "force" on close when using the context manager, this
            option causes the connection to not wait for the result of the close-session rpc. this
            can be useful if the device immediately closes the connection, not sending the "ok"
            reply.

    Returns:
        None

    Raises:
        N/A

    """

    error_tag: Optional[str] = None
    preferred_version: Optional[Version] = None
    message_poll_interval_ns: Optional[int] = None
    close_expect_no_reply: bool = False
    close_force: bool = False

    _error_tag: Optional[c_char_p] = field(init=False, default=None, repr=False)
    _preferred_version: Optional[c_char_p] = field(init=False, default=None, repr=False)

    def apply(self, ffi_mapping: LibScrapliMapping, ptr: DriverPointer) -> None:
        """
        Applies the options to the given driver pointer.

        Should not be called directly/by users.

        Args:
            ffi_mapping: the handle to the ffi mapping singleton
            ptr: the pointer to the underlying cli or netconf object

        Returns:
            None

        Raises:
            OptionsException: if any option apply returns a non-zero return code.

        """
        if self.error_tag is not None:
            self._error_tag = to_c_string(self.error_tag)

            status = ffi_mapping.options_mapping.netconf.set_error_tag(ptr, self._error_tag)
            if status != 0:
                raise OptionsException("failed to set netconf error tag")

        if self.preferred_version is not None:
            self._preferred_version = to_c_string(self.preferred_version)

            status = ffi_mapping.options_mapping.netconf.set_preferred_version(
                ptr, self._preferred_version
            )
            if status != 0:
                raise OptionsException("failed to set netconf preferred version")

        if self.message_poll_interval_ns is not None:
            status = ffi_mapping.options_mapping.netconf.set_message_poll_interva_ns(
                ptr, c_int(self.message_poll_interval_ns)
            )
            if status != 0:
                raise OptionsException("failed to set netconf message poll interval")

    def __repr__(self) -> str:
        """
        Magic repr method for Options object

        Args:
            N/A

        Returns:
            str: repr for Options object

        Raises:
            N/A

        """
        return (
            # it will probably be "canonical" to import Options as NetconfOptions, so we'll make
            # the repr do that too
            f"Netconf{self.__class__.__name__}("
            f"error_tag={self.error_tag!r}, "
            f"preferred_version={self.preferred_version!r} "
            f"message_poll_interval_ns={self.message_poll_interval_ns!r})"
        )


class Netconf:
    """
    Netconf represents a netconf connection object.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(  # noqa: PLR0913
        self,
        host: str,
        *,
        logger_callback: Optional[Callable[[int, str], None]] = None,
        port: int = 830,
        options: Optional[Options] = None,
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

        self.host = host
        self._host = to_c_string(host)

        self.logger_callback = (
            LogFuncCallback(logger_callback) if logger_callback else LogFuncCallback(0)
        )

        self.port = port

        self.options = options or Options()
        self.auth_options = auth_options or AuthOptions()
        self.session_options = session_options or SessionOptions()
        self.transport_options = transport_options or TransportOptions()

        self.ptr: Optional[DriverPointer] = None
        self._session_id: Optional[int] = None

    def __enter__(self: "Netconf") -> "Netconf":
        """
        Enter method for context manager

        Args:
            N/A

        Returns:
            Cli: a concrete implementation of the opened Cli object

        Raises:
            ScrapliConnectionError: if an exception occurs during opening

        """
        self.open()

        return self

    def __exit__(
        self,
        exception_type: Optional[BaseException],
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
        self.close(
            expect_no_reply=self.options.close_expect_no_reply,
            force=self.options.close_force,
        )

    async def __aenter__(self: "Netconf") -> "Netconf":
        """
        Enter method for context manager.

        Args:
            N/A

        Returns:
            Netconf: a concrete implementation of the opened Netconf object

        Raises:
            N/A

        """
        await self.open_async()

        return self

    async def __aexit__(
        self,
        exception_type: Optional[BaseException],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
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
        await self.close_async(
            expect_no_reply=self.options.close_expect_no_reply,
            force=self.options.close_force,
        )

    def _ptr_or_exception(self) -> DriverPointer:
        if self.ptr is None:
            raise NotOpenedException

        return self.ptr

    def _alloc(
        self,
    ) -> None:
        ptr = self.ffi_mapping.netconf_mapping.alloc(
            logger_callback=self.logger_callback,
            host=self._host,
            port=c_int(self.port),
            transport_kind=c_char_p(self.transport_options.get_transport_kind()),
        )
        if ptr == 0:  # type: ignore[comparison-overlap]
            raise AllocationException("failed to allocate netconf")

        self.ptr = ptr

    def _free(
        self,
    ) -> None:
        self.ffi_mapping.shared_mapping.free(ptr=self._ptr_or_exception())

    def _open(self) -> c_uint:
        self._alloc()

        self.options.apply(self.ffi_mapping, self._ptr_or_exception())
        self.auth_options.apply(self.ffi_mapping, self._ptr_or_exception())
        self.session_options.apply(self.ffi_mapping, self._ptr_or_exception())
        self.transport_options.apply(self.ffi_mapping, self._ptr_or_exception())

        operation_id = OperationIdPointer(c_uint(0))
        cancel = CancelPointer(c_bool(False))

        status = self.ffi_mapping.netconf_mapping.open(
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
        Open the netconf connection.

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
        Open the netconf connection.

        Args:
            N/A

        Returns:
            None

        Raises:
            OpenException: if the operation fails

        """
        operation_id = self._open()

        return await self._get_result_async(operation_id=operation_id)

    def _close(
        self,
        expect_no_reply: bool,
        force: bool,
    ) -> c_uint:
        operation_id = OperationIdPointer(c_uint(0))
        cancel = CancelPointer(c_bool(False))
        _expect_no_reply = c_bool(expect_no_reply)
        _force = c_bool(force)

        status = self.ffi_mapping.netconf_mapping.close(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
            expect_no_reply=_expect_no_reply,
            force=_force,
        )
        if status != 0:
            raise CloseException("submitting close operation")

        return c_uint(operation_id.contents.value)

    def close(
        self,
        *,
        expect_no_reply: bool = False,
        force: bool = False,
    ) -> Result:
        """
        Close the netconf connection.

        Args:
            expect_no_reply: causes the connection to send a close-session rpc but not to listen
                for that rpc's reply, and instead immediately closing the connection after sending
            force: skips sending a close-session rpc and just directly shuts down the connection

        Returns:
            None

        Raises:
            NotOpenedException: if the ptr to the netconf object is None (via _ptr_or_exception)
            CloseException: if the operation fails

        """
        operation_id = self._close(expect_no_reply=expect_no_reply, force=force)

        result = self._get_result(operation_id=operation_id)

        self._free()

        return result

    async def close_async(
        self,
        *,
        expect_no_reply: bool = False,
        force: bool = False,
    ) -> Result:
        """
        Close the netconf connection.

        Args:
            expect_no_reply: causes the connection to send a close-session rpc but not to listen
                for that rpc's reply, and instead immediately closing the connection after sending
            force: skips sending a close-session rpc and just directly shuts down the connection

        Returns:
            None

        Raises:
            NotOpenedException: if the ptr to the netconf object is None (via _ptr_or_exception)
            CloseException: if the operation fails

        """
        operation_id = self._close(expect_no_reply=expect_no_reply, force=force)

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

    def _get_result(
        self,
        operation_id: c_uint,
    ) -> Result:
        done = BoolPointer(c_bool(False))
        input_size = IntPointer(c_int())
        result_raw_size = IntPointer(c_int())
        result_size = IntPointer(c_int())
        rpc_warnings_size = IntPointer(c_int())
        rpc_errors_size = IntPointer(c_int())
        err_size = IntPointer(c_int())

        # in sync flavor we call the blocking wait to limit the number of calls to the c abi
        status = self.ffi_mapping.netconf_mapping.wait(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            done=done,
            input_size=input_size,
            result_raw_size=result_raw_size,
            result_size=result_size,
            rpc_warnings_size=rpc_warnings_size,
            rpc_errors_size=rpc_errors_size,
            err_size=err_size,
        )
        if status != 0:
            raise GetResultException("wait operation failed")

        start_time = UnixTimestampPointer(c_uint64())
        end_time = UnixTimestampPointer(c_uint64())

        input_slice = ZigSlice(size=input_size.contents)
        result_raw_slice = ZigSlice(size=result_raw_size.contents)
        result_slice = ZigSlice(size=result_size.contents)

        rpc_warnings_slice = ZigSlice(size=rpc_warnings_size.contents)
        rpc_errors_slice = ZigSlice(size=rpc_errors_size.contents)
        err_slice = ZigSlice(size=err_size.contents)

        status = self.ffi_mapping.netconf_mapping.fetch(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            start_time=start_time,
            end_time=end_time,
            input_slice=input_slice,
            result_raw_slice=result_raw_slice,
            result_slice=result_slice,
            rpc_warnings_slice=rpc_warnings_slice,
            rpc_errors_slice=rpc_errors_slice,
            err_slice=err_slice,
        )
        if status != 0:
            raise GetResultException("fetch operation failed")

        err_contents = err_slice.get_decoded_contents()
        if err_contents:
            raise OperationException(err_contents)

        return Result(
            input_=input_slice.get_decoded_contents(),
            host=self.host,
            port=self.port,
            start_time=start_time.contents.value,
            end_time=end_time.contents.value,
            result_raw=result_raw_slice.get_contents(),
            result=result_slice.get_decoded_contents(),
            rpc_warnings=rpc_warnings_slice.get_decoded_contents(),
            rpc_errors=rpc_errors_slice.get_decoded_contents(),
        )

    async def _get_result_async(
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
        input_size = IntPointer(c_int())
        result_raw_size = IntPointer(c_int())
        result_size = IntPointer(c_int())
        rpc_warnings_size = IntPointer(c_int())
        rpc_errors_size = IntPointer(c_int())
        err_size = IntPointer(c_int())

        while True:
            status = self.ffi_mapping.netconf_mapping.poll(
                ptr=self._ptr_or_exception(),
                operation_id=operation_id,
                done=done,
                input_size=input_size,
                result_raw_size=result_raw_size,
                result_size=result_size,
                rpc_warnings_size=rpc_warnings_size,
                rpc_errors_size=rpc_errors_size,
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
        end_time = UnixTimestampPointer(c_uint64())

        input_slice = ZigSlice(size=input_size.contents)
        result_raw_slice = ZigSlice(size=result_raw_size.contents)
        result_slice = ZigSlice(size=result_size.contents)

        rpc_warnings_slice = ZigSlice(size=rpc_warnings_size.contents)
        rpc_errors_slice = ZigSlice(size=rpc_errors_size.contents)
        err_slice = ZigSlice(size=err_size.contents)

        status = self.ffi_mapping.netconf_mapping.fetch(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            start_time=start_time,
            end_time=end_time,
            input_slice=input_slice,
            result_raw_slice=result_raw_slice,
            result_slice=result_slice,
            rpc_warnings_slice=rpc_warnings_slice,
            rpc_errors_slice=rpc_errors_slice,
            err_slice=err_slice,
        )
        if status != 0:
            raise GetResultException("fetch operation failed")

        err_contents = err_slice.get_decoded_contents()
        if err_contents:
            raise OperationException(err_contents)

        return Result(
            input_=input_slice.get_decoded_contents(),
            host=self.host,
            port=self.port,
            start_time=start_time.contents.value,
            end_time=end_time.contents.value,
            result_raw=result_raw_slice.get_contents(),
            result=result_slice.get_decoded_contents(),
            rpc_warnings=rpc_warnings_slice.get_decoded_contents(),
            rpc_errors=rpc_errors_slice.get_decoded_contents(),
        )

    @property
    def session_id(self) -> int:
        """
        Get the session id of the connection.

        Args:
            N/A

        Returns:
            int: session id of the connection

        Raises:
            GetResultException: if fetching the session id fails

        """
        if self._session_id is not None:
            return self._session_id

        session_id = IntPointer(c_int())

        status = self.ffi_mapping.netconf_mapping.get_session_id(
            ptr=self._ptr_or_exception(), session_id=session_id
        )
        if status != 0:
            raise GetResultException("fetch session id failed")

        self._session_id = session_id.contents.value

        return self._session_id

    def _raw_rpc(
        self,
        *,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
        payload: str,
    ) -> c_uint:
        _payload = to_c_string(payload)

        status = self.ffi_mapping.netconf_mapping.raw_rpc(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
            payload=_payload,
        )
        if status != 0:
            raise SubmitOperationException("submitting raw rpc operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def raw_rpc(
        self,
        payload: str,
        *,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a "raw" / user crafted rpc operation.

        Args:
            payload: the raw rpc payload
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

        operation_id = self._raw_rpc(operation_id=operation_id, cancel=cancel, payload=payload)

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def raw_rpc_async(
        self,
        payload: str,
        *,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a "raw" / user crafted rpc operation.

        Args:
            payload: the raw rpc payload
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

        operation_id = self._raw_rpc(operation_id=operation_id, cancel=cancel, payload=payload)

        return await self._get_result_async(operation_id=operation_id)

    def _get_config(  # noqa: PLR0913,too-many-locals
        self,
        *,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
        source: DatastoreType,
        filter_: str,
        filter_type: FilterType,
        filter_namespace_prefix: str,
        filter_namespace: str,
        defaults_type: DefaultsType,
    ) -> c_uint:
        _source = to_c_string(source)
        _filter = to_c_string(filter_)
        _filter_type = to_c_string(filter_type)
        _filter_namespace_prefix = to_c_string(filter_namespace_prefix)
        _filter_namespace = to_c_string(filter_namespace)
        _defaults_type = to_c_string(defaults_type)

        status = self.ffi_mapping.netconf_mapping.get_config(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
            source=_source,
            filter_=_filter,
            filter_type=_filter_type,
            filter_namespace_prefix=_filter_namespace_prefix,
            filter_namespace=_filter_namespace,
            defaults_type=_defaults_type,
        )
        if status != 0:
            raise SubmitOperationException("submitting get-config operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def get_config(  # noqa: PLR0913
        self,
        *,
        source: DatastoreType = DatastoreType.RUNNING,
        filter_: str = "",
        filter_type: FilterType = FilterType.SUBTREE,
        filter_namespace_prefix: str = "",
        filter_namespace: str = "",
        defaults_type: DefaultsType = DefaultsType.UNSET,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a get-config rpc operation.

        Args:
            source: source datastore to get config from
            filter_: filter to apply to the get-config (or not if empty string)
            filter_type: type of filter to apply, subtree|xpath
            filter_namespace_prefix: filter namespace prefix
            filter_namespace: filter namespace
            defaults_type: defaults type to apply to the get-config, "unset" means dont apply one
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

        operation_id = self._get_config(
            operation_id=operation_id,
            cancel=cancel,
            source=source,
            filter_=filter_,
            filter_type=filter_type,
            filter_namespace_prefix=filter_namespace_prefix,
            filter_namespace=filter_namespace,
            defaults_type=defaults_type,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def get_config_async(  # noqa: PLR0913
        self,
        *,
        source: DatastoreType = DatastoreType.RUNNING,
        filter_: str = "",
        filter_type: FilterType = FilterType.SUBTREE,
        filter_namespace_prefix: str = "",
        filter_namespace: str = "",
        defaults_type: DefaultsType = DefaultsType.UNSET,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a get-config rpc operation.

        Args:
            source: source datastore to get config from
            filter_: filter to apply to the get-config (or not if empty string)
            filter_type: type of filter to apply, subtree|xpath
            filter_namespace_prefix: filter namespace prefix
            filter_namespace: filter namespace
            defaults_type: defaults type to apply to the get-config, "unset" means dont apply one
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

        operation_id = self._get_config(
            operation_id=operation_id,
            cancel=cancel,
            source=source,
            filter_=filter_,
            filter_type=filter_type,
            filter_namespace_prefix=filter_namespace_prefix,
            filter_namespace=filter_namespace,
            defaults_type=defaults_type,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _edit_config(
        self,
        *,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
        config: str,
        target: DatastoreType,
    ) -> c_uint:
        _config = to_c_string(config)
        _target = to_c_string(target)

        status = self.ffi_mapping.netconf_mapping.edit_config(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
            config=_config,
            target=_target,
        )
        if status != 0:
            raise SubmitOperationException("submitting edit-config operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def edit_config(
        self,
        *,
        config: str = "",
        target: DatastoreType = DatastoreType.RUNNING,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute an edit-config rpc operation.

        Args:
            config: string config payload to send
            target: target datastore as DatastoreType enum
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._edit_config(
            operation_id=operation_id,
            cancel=cancel,
            config=config,
            target=target,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def edit_config_async(
        self,
        *,
        config: str = "",
        target: DatastoreType = DatastoreType.RUNNING,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute an edit-config rpc operation.

        Args:
            config: string config payload to send
            target: target datastore as DatastoreType enum
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._edit_config(
            operation_id=operation_id,
            cancel=cancel,
            config=config,
            target=target,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _copy_config(
        self,
        *,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
        target: DatastoreType,
        source: DatastoreType,
    ) -> c_uint:
        _target = to_c_string(target)
        _source = to_c_string(source)

        status = self.ffi_mapping.netconf_mapping.copy_config(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
            target=_target,
            source=_source,
        )
        if status != 0:
            raise SubmitOperationException("submitting copy-config operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def copy_config(
        self,
        *,
        target: DatastoreType = DatastoreType.RUNNING,
        source: DatastoreType = DatastoreType.STARTUP,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a copy-config rpc operation.

        Args:
            target: target to copy *to*
            source: source to copy *from*
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._copy_config(
            operation_id=operation_id,
            cancel=cancel,
            target=target,
            source=source,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def copy_config_async(
        self,
        *,
        target: DatastoreType = DatastoreType.RUNNING,
        source: DatastoreType = DatastoreType.STARTUP,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a copy-config rpc operation.

        Args:
            target: target to copy *to*
            source: source to copy *from*
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._copy_config(
            operation_id=operation_id,
            cancel=cancel,
            target=target,
            source=source,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _delete_config(
        self,
        *,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
        target: DatastoreType,
    ) -> c_uint:
        _target = to_c_string(target)

        status = self.ffi_mapping.netconf_mapping.delete_config(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
            target=_target,
        )
        if status != 0:
            raise SubmitOperationException("submitting delete-config operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def delete_config(
        self,
        *,
        target: DatastoreType = DatastoreType.RUNNING,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a delete-config rpc operation.

        Args:
            target: target datastore to delete
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._delete_config(
            operation_id=operation_id,
            cancel=cancel,
            target=target,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def delete_config_async(
        self,
        *,
        target: DatastoreType = DatastoreType.RUNNING,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a delete-config rpc operation.

        Args:
            target: target datastore to delete
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._delete_config(
            operation_id=operation_id,
            cancel=cancel,
            target=target,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _lock(
        self,
        *,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
        target: DatastoreType,
    ) -> c_uint:
        _target = to_c_string(target)

        status = self.ffi_mapping.netconf_mapping.lock(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
            target=_target,
        )
        if status != 0:
            raise SubmitOperationException("submitting lock operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def lock(
        self,
        *,
        target: DatastoreType = DatastoreType.RUNNING,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a lock rpc operation.

        Args:
            target: target datastore to lock
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._lock(
            operation_id=operation_id,
            cancel=cancel,
            target=target,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def lock_async(
        self,
        *,
        target: DatastoreType = DatastoreType.RUNNING,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a lock rpc operation.

        Args:
            target: target datastore to lock
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._lock(
            operation_id=operation_id,
            cancel=cancel,
            target=target,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _unlock(
        self,
        *,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
        target: DatastoreType,
    ) -> c_uint:
        _target = to_c_string(target)

        status = self.ffi_mapping.netconf_mapping.unlock(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
            target=_target,
        )
        if status != 0:
            raise SubmitOperationException("submitting unlock operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def unlock(
        self,
        *,
        target: DatastoreType = DatastoreType.RUNNING,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute an unlock rpc operation.

        Args:
            target: target datastore to unlock
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._unlock(
            operation_id=operation_id,
            cancel=cancel,
            target=target,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def unlock_async(
        self,
        *,
        target: DatastoreType = DatastoreType.RUNNING,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute an unlock rpc operation.

        Args:
            target: target datastore to unlock
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._unlock(
            operation_id=operation_id,
            cancel=cancel,
            target=target,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _get(  # noqa: PLR0913,too-many-locals
        self,
        *,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
        filter_: str,
        filter_type: FilterType,
        filter_namespace_prefix: str,
        filter_namespace: str,
        defaults_type: DefaultsType,
    ) -> c_uint:
        _filter = to_c_string(filter_)
        _filter_type = to_c_string(filter_type)
        _filter_namespace_prefix = to_c_string(filter_namespace_prefix)
        _filter_namespace = to_c_string(filter_namespace)
        _defaults_type = to_c_string(defaults_type)

        status = self.ffi_mapping.netconf_mapping.get(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
            filter_=_filter,
            filter_type=_filter_type,
            filter_namespace_prefix=_filter_namespace_prefix,
            filter_namespace=_filter_namespace,
            defaults_type=_defaults_type,
        )
        if status != 0:
            raise SubmitOperationException("submitting get operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def get(  # noqa: PLR0913
        self,
        *,
        filter_: str = "",
        filter_type: FilterType = FilterType.SUBTREE,
        filter_namespace_prefix: str = "",
        filter_namespace: str = "",
        defaults_type: DefaultsType = DefaultsType.UNSET,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a get rpc operation.

        Args:
            filter_: filter to apply to the get-config (or not if empty string)
            filter_type: type of filter to apply, subtree|xpath
            filter_namespace_prefix: filter namespace prefix
            filter_namespace: filter namespace
            defaults_type: defaults type to apply to the get-config, "unset" means dont apply one
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._get(
            operation_id=operation_id,
            cancel=cancel,
            filter_=filter_,
            filter_type=filter_type,
            filter_namespace_prefix=filter_namespace_prefix,
            filter_namespace=filter_namespace,
            defaults_type=defaults_type,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def get_async(  # noqa: PLR0913
        self,
        *,
        filter_: str = "",
        filter_type: FilterType = FilterType.SUBTREE,
        filter_namespace_prefix: str = "",
        filter_namespace: str = "",
        defaults_type: DefaultsType = DefaultsType.UNSET,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a get rpc operation.

        Args:
            filter_: filter to apply to the get-config (or not if empty string)
            filter_type: type of filter to apply, subtree|xpath
            filter_namespace_prefix: filter namespace prefix
            filter_namespace: filter namespace
            defaults_type: defaults type to apply to the get-config, "unset" means dont apply one
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._get(
            operation_id=operation_id,
            cancel=cancel,
            filter_=filter_,
            filter_type=filter_type,
            filter_namespace_prefix=filter_namespace_prefix,
            filter_namespace=filter_namespace,
            defaults_type=defaults_type,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _close_session(
        self,
        *,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
    ) -> c_uint:
        status = self.ffi_mapping.netconf_mapping.close_session(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
        )
        if status != 0:
            raise SubmitOperationException("submitting close-session operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def close_session(
        self,
        *,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a close-session rpc operation.

        Args:
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._close_session(
            operation_id=operation_id,
            cancel=cancel,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def close_session_async(
        self,
        *,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a close-session rpc operation.

        Args:
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._close_session(
            operation_id=operation_id,
            cancel=cancel,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _kill_session(
        self,
        *,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
        session_id: int,
    ) -> c_uint:
        status = self.ffi_mapping.netconf_mapping.kill_session(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
            session_id=c_int(session_id),
        )
        if status != 0:
            raise SubmitOperationException("submitting kill-session operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def kill_session(
        self,
        session_id: int,
        *,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a kill-session rpc operation.

        Args:
            session_id: session id to kill
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._kill_session(
            operation_id=operation_id,
            cancel=cancel,
            session_id=session_id,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def kill_session_async(
        self,
        session_id: int,
        *,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a kill-session rpc operation.

        Args:
            session_id: session id to kill
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._kill_session(
            operation_id=operation_id,
            cancel=cancel,
            session_id=session_id,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _commit(
        self,
        *,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
    ) -> c_uint:
        status = self.ffi_mapping.netconf_mapping.commit(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
        )
        if status != 0:
            raise SubmitOperationException("submitting commit operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def commit(
        self,
        *,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a commit rpc operation.

        Args:
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._commit(
            operation_id=operation_id,
            cancel=cancel,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def commit_async(
        self,
        *,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a commit rpc operation.

        Args:
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._commit(
            operation_id=operation_id,
            cancel=cancel,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _discard(
        self,
        *,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
    ) -> c_uint:
        status = self.ffi_mapping.netconf_mapping.discard(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
        )
        if status != 0:
            raise SubmitOperationException("submitting discard operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def discard(
        self,
        *,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a discard rpc operation.

        Args:
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._discard(
            operation_id=operation_id,
            cancel=cancel,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def discard_async(
        self,
        *,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a discard rpc operation.

        Args:
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._discard(
            operation_id=operation_id,
            cancel=cancel,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _cancel_commit(
        self,
        *,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
    ) -> c_uint:
        status = self.ffi_mapping.netconf_mapping.cancel_commit(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
        )
        if status != 0:
            raise SubmitOperationException("submitting cancel-commit operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def cancel_commit(
        self,
        *,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a cancel-commit rpc operation.

        Args:
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._cancel_commit(
            operation_id=operation_id,
            cancel=cancel,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def cancel_commit_async(
        self,
        *,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a cancel-commit rpc operation.

        Args:
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._cancel_commit(
            operation_id=operation_id,
            cancel=cancel,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _validate(
        self,
        *,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
        source: DatastoreType,
    ) -> c_uint:
        _source = to_c_string(source)

        status = self.ffi_mapping.netconf_mapping.validate(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
            source=_source,
        )
        if status != 0:
            raise SubmitOperationException("submitting validate operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def validate(
        self,
        *,
        source: DatastoreType = DatastoreType.RUNNING,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a validate rpc operation.

        Args:
            source: datastore to validate
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._validate(
            operation_id=operation_id,
            cancel=cancel,
            source=source,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def validate_async(
        self,
        *,
        source: DatastoreType = DatastoreType.RUNNING,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a validate rpc operation.

        Args:
            source: datastore to validate
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._validate(
            operation_id=operation_id,
            cancel=cancel,
            source=source,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _get_schema(
        self,
        *,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
        identifier: str,
        version: str,
        format_: SchemaFormat,
    ) -> c_uint:
        _identifier = to_c_string(identifier)
        _version = to_c_string(version)
        _format = to_c_string(format_)

        status = self.ffi_mapping.netconf_mapping.get_schema(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
            identifier=_identifier,
            version=_version,
            format_=_format,
        )
        if status != 0:
            raise SubmitOperationException("submitting get-schema operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def get_schema(
        self,
        identifier: str,
        *,
        version: str = "",
        format_: SchemaFormat = SchemaFormat.YANG,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a get-schema rpc operation.

        Args:
            identifier: schema identifier to get
            version: optional schema version to request
            format_: schema format to apply
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._get_schema(
            operation_id=operation_id,
            cancel=cancel,
            identifier=identifier,
            version=version,
            format_=format_,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def get_schema_async(
        self,
        identifier: str,
        *,
        version: str = "",
        format_: SchemaFormat = SchemaFormat.YANG,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a get-schema rpc operation.

        Args:
            identifier: schema identifier to get
            version: optional schema version to request
            format_: schema format to apply
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._get_schema(
            operation_id=operation_id,
            cancel=cancel,
            identifier=identifier,
            version=version,
            format_=format_,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _get_data(  # noqa: PLR0913,too-many-locals
        self,
        *,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
        source: DatastoreType,
        filter_: str,
        filter_type: FilterType,
        filter_namespace_prefix: str,
        filter_namespace: str,
        config_filter: ConfigFilter,
        origin_filters: str,
        max_depth: int,
        with_origin: bool,
        defaults_type: DefaultsType,
    ) -> c_uint:
        _source = to_c_string(source)
        _filter = to_c_string(filter_)
        _filter_type = to_c_string(filter_type)
        _filter_namespace_prefix = to_c_string(filter_namespace_prefix)
        _filter_namespace = to_c_string(filter_namespace)
        _config_filter = to_c_string(config_filter)
        _origin_filters = to_c_string(origin_filters)
        _defaults_type = to_c_string(defaults_type)

        status = self.ffi_mapping.netconf_mapping.get_data(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
            source=_source,
            filter_=_filter,
            filter_type=_filter_type,
            filter_namespace_prefix=_filter_namespace_prefix,
            filter_namespace=_filter_namespace,
            config_filter=_config_filter,
            origin_filters=_origin_filters,
            max_depth=c_int(max_depth),
            with_origin=c_bool(with_origin),
            defaults_type=_defaults_type,
        )
        if status != 0:
            raise SubmitOperationException("submitting copy-config operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def get_data(  # noqa: PLR0913
        self,
        *,
        source: DatastoreType = DatastoreType.RUNNING,
        filter_: str = "",
        filter_type: FilterType = FilterType.SUBTREE,
        filter_namespace_prefix: str = "",
        filter_namespace: str = "",
        config_filter: ConfigFilter = ConfigFilter.UNSET,
        origin_filters: str = "",
        max_depth: int = 0,
        with_origin: bool = False,
        defaults_type: DefaultsType = DefaultsType.UNSET,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a get-data rpc operation.

        Args:
            source: source datastore to get data from
            filter_: filter to apply to the get-config (or not if empty string)
            filter_type: type of filter to apply, subtree|xpath
            filter_namespace_prefix: filter namespace prefix
            filter_namespace: filter namespace
            config_filter: config filter true/false, or unset to leave up to the server
            origin_filters: fully formed origin filter xml payload to embed
            max_depth: max depth of data requested
            with_origin: include origin data
            defaults_type: defaults type to apply to the get-config, "unset" means dont apply one
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._get_data(
            operation_id=operation_id,
            cancel=cancel,
            source=source,
            filter_=filter_,
            filter_type=filter_type,
            filter_namespace_prefix=filter_namespace_prefix,
            filter_namespace=filter_namespace,
            config_filter=config_filter,
            origin_filters=origin_filters,
            max_depth=max_depth,
            with_origin=with_origin,
            defaults_type=defaults_type,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def get_data_async(  # noqa: PLR0913
        self,
        *,
        source: DatastoreType = DatastoreType.RUNNING,
        filter_: str = "",
        filter_type: FilterType = FilterType.SUBTREE,
        filter_namespace_prefix: str = "",
        filter_namespace: str = "",
        config_filter: ConfigFilter = ConfigFilter.UNSET,
        origin_filters: str = "",
        max_depth: int = 0,
        with_origin: bool = False,
        defaults_type: DefaultsType = DefaultsType.UNSET,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute a get-data rpc operation.

        Args:
            source: source datastore to get data from
            filter_: filter to apply to the get-config (or not if empty string)
            filter_type: type of filter to apply, subtree|xpath
            filter_namespace_prefix: filter namespace prefix
            filter_namespace: filter namespace
            config_filter: config filter true/false, or unset to leave up to the server
            origin_filters: fully formed origin filter xml payload to embed
            max_depth: max depth of data requested
            with_origin: include origin data
            defaults_type: defaults type to apply to the get-config, "unset" means dont apply one
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._get_data(
            operation_id=operation_id,
            cancel=cancel,
            source=source,
            filter_=filter_,
            filter_type=filter_type,
            filter_namespace_prefix=filter_namespace_prefix,
            filter_namespace=filter_namespace,
            config_filter=config_filter,
            origin_filters=origin_filters,
            max_depth=max_depth,
            with_origin=with_origin,
            defaults_type=defaults_type,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _edit_data(
        self,
        *,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
        content: str,
        target: DatastoreType,
    ) -> c_uint:
        _content = to_c_string(content)
        _target = to_c_string(target)

        status = self.ffi_mapping.netconf_mapping.edit_data(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
            content=_content,
            target=_target,
        )
        if status != 0:
            raise SubmitOperationException("submitting copy-config operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def edit_data(
        self,
        content: str,
        *,
        target: DatastoreType = DatastoreType.RUNNING,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute an edit-data rpc operation.

        Args:
            content: full payload content to send
            target: datastore to target
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._edit_data(
            operation_id=operation_id,
            cancel=cancel,
            content=content,
            target=target,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def edit_data_async(
        self,
        content: str,
        *,
        target: DatastoreType = DatastoreType.RUNNING,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute an edit-data rpc operation.

        Args:
            content: full payload content to send
            target: datastore to target
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._edit_data(
            operation_id=operation_id,
            cancel=cancel,
            content=content,
            target=target,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _action(
        self,
        *,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
        action: str,
    ) -> c_uint:
        _action = to_c_string(action)

        status = self.ffi_mapping.netconf_mapping.action(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            cancel=cancel,
            action=_action,
        )
        if status != 0:
            raise SubmitOperationException("submitting action operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def action(
        self,
        action: str,
        *,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute an action rpc operation.

        Args:
            action: action to execute
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._action(
            operation_id=operation_id,
            cancel=cancel,
            action=action,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def action_async(
        self,
        action: str,
        *,
        operation_timeout_ns: Optional[int] = None,
    ) -> Result:
        """
        Execute an action rpc operation.

        Args:
            action: action to execute
            operation_timeout_ns: optional timeout in ns for this operation

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

        operation_id = self._action(
            operation_id=operation_id,
            cancel=cancel,
            action=action,
        )

        return await self._get_result_async(operation_id=operation_id)
