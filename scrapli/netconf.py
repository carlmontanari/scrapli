"""scrapli.netconf"""

from asyncio import sleep as async_sleep
from ctypes import c_bool, c_char_p, c_int, c_uint
from enum import Enum
from logging import getLogger
from random import randint
from typing import Callable, Optional

from scrapli.auth import Options as AuthOptions
from scrapli.exceptions import (
    AllocationException,
    CloseException,
    GetResultException,
    NotOpenedException,
    OpenException,
    OperationException,
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


class Netconf:  # pylint: disable=too-many-instance-attributes
    """
    Netconf represents a netconf connection object.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        host: str,
        *,
        logger_callback: Optional[Callable[[int, str], None]] = None,
        port: int = 830,
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

        self.auth_options = auth_options or AuthOptions()
        self.session_options = session_options or SessionOptions()
        self.transport_options = transport_options or TransportOptions()

        self.ptr: Optional[DriverPointer] = None
        self._session_id: Optional[int] = None

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
        Close the netconf connection.

        Args:
            N/A

        Returns:
            None

        Raises:
            NotOpenedException: if the ptr to the netconf object is None (via _ptr_or_exception)
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
        Close the netconf connection.

        Args:
            N/A

        Returns:
            None

        Raises:
            NotOpenedException: if the ptr to the netconf object is None (via _ptr_or_exception)
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

        start_time = IntPointer(c_int())
        end_time = IntPointer(c_int())

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

        start_time = IntPointer(c_int())
        end_time = IntPointer(c_int())

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

    def _get_config(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        *,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
        source: DatastoreType = DatastoreType.RUNNING,
        filter_: str = "",
        filter_type: FilterType = FilterType.SUBTREE,
        filter_namespace_prefix: str = "",
        filter_namespace: str = "",
        defaults_type: DefaultsType = DefaultsType.UNSET,
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
    def get_config(  # pylint: disable=too-many-arguments
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
    async def get_config_async(  # pylint: disable=too-many-arguments
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
