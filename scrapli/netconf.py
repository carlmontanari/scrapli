"""scrapli.netconf"""

from ctypes import c_bool, c_char_p, c_int, c_uint, c_uint64
from dataclasses import dataclass, field
from enum import Enum
from logging import getLogger
from types import TracebackType
from typing import Any

from scrapli.auth import Options as AuthOptions
from scrapli.exceptions import (
    AllocationException,
    CloseException,
    GetResultException,
    NoMessagesException,
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
    ffi_logger_wrapper,
    to_c_string,
)
from scrapli.helper import (
    wait_for_available_operation_result,
    wait_for_available_operation_result_async,
)
from scrapli.netconf_decorators import handle_operation_timeout, handle_operation_timeout_async
from scrapli.netconf_result import Result
from scrapli.session import Options as SessionOptions
from scrapli.transport import BinOptions as TransportBinOptions
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

    error_tag: str | None = None
    preferred_version: Version | None = None
    message_poll_interval_ns: int | None = None
    close_force: bool = False

    _error_tag: c_char_p | None = field(init=False, default=None, repr=False)
    _preferred_version: c_char_p | None = field(init=False, default=None, repr=False)

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
            f"close_force={self.close_force!r})"
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
        port: int = 830,
        options: Options | None = None,
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

        self.host = host
        self._host = to_c_string(host)

        self.port = port

        self.options = options or Options()
        self.auth_options = auth_options or AuthOptions()
        self.session_options = session_options or SessionOptions()
        self.transport_options = transport_options or TransportBinOptions()

        self.ptr: DriverPointer | None = None
        self.poll_fd: int = 0

        self._session_id: int | None = None

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
        exception_type: BaseException | None,
        exception_value: BaseException | None,
        traceback: TracebackType | None,
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
        await self.close_async(
            force=self.options.close_force,
        )

    def __str__(self) -> str:
        """
        Magic str method for Netconf object.

        Args:
            N/A

        Returns:
            str: str representation of Netconf

        Raises:
            N/A

        """
        return f"scrapli.Netconf {self.host}:{self.port}"

    def __repr__(self) -> str:
        """
        Magic repr method for Netconf object.

        Args:
            N/A

        Returns:
            str: repr for Netconf object

        Raises:
            N/A

        """
        return (
            f"{self.__class__.__name__}("
            f"host={self.host!r}, "
            f"port={self.port!r}, "
            f"options={self.options!r} "
            f"auth_options={self.auth_options!r} "
            f"session_options={self.auth_options!r} "
            f"transport_options={self.transport_options!r}) "
        )

    def __copy__(self, memodict: dict[Any, Any] = {}) -> "Netconf":
        # reasonably safely copy of the object... *reasonably*... basically assumes that options
        # will never be mutated during an objects lifetime, which *should* be the case. probably.
        return Netconf(
            host=self.host,
            port=self.port,
            options=self.options,
            auth_options=self.auth_options,
            session_options=self.session_options,
            transport_options=self.transport_options,
            logging_uid=self._logging_uid,
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
            transport_kind=c_char_p(self.transport_options.transport_kind.encode(encoding="utf-8")),
        )
        if ptr == 0:  # type: ignore[comparison-overlap]
            raise AllocationException("failed to allocate netconf")

        self.ptr = ptr

        poll_fd = int(
            self.ffi_mapping.shared_mapping.get_poll_fd(
                ptr=self._ptr_or_exception(),
            )
        )
        if poll_fd <= 0:
            raise AllocationException("failed to allocate netconf")

        self.poll_fd = poll_fd

    def _free(
        self,
    ) -> None:
        self.ffi_mapping.shared_mapping.free(ptr=self._ptr_or_exception())

    def _open(
        self,
        *,
        operation_id: OperationIdPointer,
    ) -> None:
        self._alloc()

        self.options.apply(self.ffi_mapping, self._ptr_or_exception())
        self.auth_options.apply(self.ffi_mapping, self._ptr_or_exception())
        self.session_options.apply(self.ffi_mapping, self._ptr_or_exception())
        self.transport_options.apply(self.ffi_mapping, self._ptr_or_exception())

        status = self.ffi_mapping.netconf_mapping.open(
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
        Open the netconf connection.

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
        Open the netconf connection.

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
        force: c_bool,
    ) -> None:
        status = self.ffi_mapping.netconf_mapping.close(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            force=force,
        )
        if status != 0:
            raise CloseException("submitting close operation")

    def close(
        self,
        *,
        force: bool = False,
    ) -> Result:
        """
        Close the netconf connection.

        Args:
            force: skips sending a close-session rpc and just directly shuts down the connection

        Returns:
            None

        Raises:
            NotOpenedException: if the ptr to the netconf object is None (via _ptr_or_exception)
            CloseException: if the operation fails

        """
        operation_id = OperationIdPointer(c_uint(0))
        _force = c_bool(force)

        self._close(operation_id=operation_id, force=_force)

        result = self._get_result(operation_id=operation_id.contents.value)

        self._free()

        return result

    async def close_async(
        self,
        *,
        force: bool = False,
    ) -> Result:
        """
        Close the netconf connection.

        Args:
            force: skips sending a close-session rpc and just directly shuts down the connection

        Returns:
            None

        Raises:
            NotOpenedException: if the ptr to the netconf object is None (via _ptr_or_exception)
            CloseException: if the operation fails

        """
        operation_id = OperationIdPointer(c_uint(0))
        _force = c_bool(force)

        self._close(operation_id=operation_id, force=_force)

        result = await self._get_result_async(operation_id=operation_id.contents.value)

        self._free()

        return result

    def _get_result(
        self,
        operation_id: c_uint,
    ) -> Result:
        wait_for_available_operation_result(self.poll_fd)

        input_size = IntPointer(c_int())
        result_raw_size = IntPointer(c_int())
        result_size = IntPointer(c_int())
        rpc_warnings_size = IntPointer(c_int())
        rpc_errors_size = IntPointer(c_int())
        err_size = IntPointer(c_int())

        status = self.ffi_mapping.netconf_mapping.fetch_sizes(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            input_size=input_size,
            result_raw_size=result_raw_size,
            result_size=result_size,
            rpc_warnings_size=rpc_warnings_size,
            rpc_errors_size=rpc_errors_size,
            err_size=err_size,
        )
        if status != 0:
            raise GetResultException("wait operation failed")

        start_time = U64Pointer(c_uint64())
        end_time = U64Pointer(c_uint64())

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
        await wait_for_available_operation_result_async(fd=self.poll_fd)

        input_size = IntPointer(c_int())
        result_raw_size = IntPointer(c_int())
        result_size = IntPointer(c_int())
        rpc_warnings_size = IntPointer(c_int())
        rpc_errors_size = IntPointer(c_int())
        err_size = IntPointer(c_int())

        status = self.ffi_mapping.netconf_mapping.fetch_sizes(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            input_size=input_size,
            result_raw_size=result_raw_size,
            result_size=result_size,
            rpc_warnings_size=rpc_warnings_size,
            rpc_errors_size=rpc_errors_size,
            err_size=err_size,
        )
        if status != 0:
            raise GetResultException("fetch operation sizes failed")

        start_time = U64Pointer(c_uint64())
        end_time = U64Pointer(c_uint64())

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

    def get_subscription_id(self, payload: str) -> int:
        """
        Get the subscription id from a rpc-reply (from an establish-subscription rpc).

        Args:
            payload: the payload to find the subscription id in

        Returns:
            int: subscription id

        Raises:
            N/A

        """
        _payload = to_c_string(payload)
        subscription_id = U64Pointer(c_uint64())

        status = self.ffi_mapping.netconf_mapping.get_subscription_id(
            payload=_payload,
            subscription_id=subscription_id,
        )
        if status != 0:
            raise GetResultException("fetch subscriptiond id failed")

        return int(subscription_id.contents.value)

    def get_next_notification(
        self,
    ) -> str:
        """
        Fetch the next notification message if available.

        Args:
            N/A

        Returns:
            str: the string content of the next notification

        Raises:
            NotOpenedException: if the ptr to the cli object is None (via _ptr_or_exception)
            SubmitOperationException: if the operation fails
            NoMessagesException: if there are no notifications to fetch

        """
        notification_size = U64Pointer(c_uint64())

        self.ffi_mapping.netconf_mapping.get_next_notification_size(
            ptr=self._ptr_or_exception(),
            notification_size=notification_size,
        )

        if notification_size.contents == 0:
            raise NoMessagesException("no notification messages available")

        notification_slice = ZigSlice(size=notification_size.contents)

        status = self.ffi_mapping.netconf_mapping.get_next_notification(
            ptr=self._ptr_or_exception(),
            notification_slice=notification_slice,
        )
        if status != 0:
            raise SubmitOperationException("submitting getting next notification failed")

        return notification_slice.get_decoded_contents()

    def get_next_subscription(
        self,
        subscription_id: int,
    ) -> str:
        """
        Fetch the next notification message if available.

        Args:
            subscription_id: subscription id to fetch a message for

        Returns:
            str: the string content of the next notification

        Raises:
            NotOpenedException: if the ptr to the cli object is None (via _ptr_or_exception)
            SubmitOperationException: if the operation fails
            NoMessagesException: if there are no notifications to fetch

        """
        subscription_size = U64Pointer(c_uint64())

        self.ffi_mapping.netconf_mapping.get_next_subscription_size(
            ptr=self._ptr_or_exception(),
            subscription_id=c_uint64(subscription_id),
            subscription_size=subscription_size,
        )

        if subscription_size.contents == 0:
            raise NoMessagesException(
                f"no subscription messages available for subscription id {subscription_id}",
            )

        subscription_slice = ZigSlice(size=subscription_size.contents)

        status = self.ffi_mapping.netconf_mapping.get_next_subscription(
            ptr=self._ptr_or_exception(),
            subscription_id=c_uint64(subscription_id),
            subscription_slice=subscription_slice,
        )
        if status != 0:
            raise SubmitOperationException("submitting getting next subscription failed")

        return subscription_slice.get_decoded_contents()

    def _raw_rpc(
        self,
        *,
        operation_id: OperationIdPointer,
        payload: c_char_p,
        base_namespace_prefix: c_char_p,
        extra_namespaces: c_char_p,
    ) -> c_uint:
        status = self.ffi_mapping.netconf_mapping.raw_rpc(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            payload=payload,
            base_namespace_prefix=base_namespace_prefix,
            extra_namespaces=extra_namespaces,
        )
        if status != 0:
            raise SubmitOperationException("submitting raw rpc operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def raw_rpc(
        self,
        payload: str,
        *,
        base_namespace_prefix: str = "",
        extra_namespaces: list[tuple[str, str]] | None = None,
        operation_timeout_ns: int | None = None,
    ) -> Result:
        """
        Execute a "raw" / user crafted rpc operation.

        Args:
            payload: the raw rpc payload
            base_namespace_prefix: prefix to use for hte base/default netconf base namespace
            extra_namespaces: optional list of pairs of prefix::namespaces. this plus the base
                namespace prefix can allow for weird cases like nxos where the base namespace must
                be prefixed and then additional namespaces indicating desired targets must be added
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

        _payload = to_c_string(payload)
        _base_namespace_prefix = to_c_string(base_namespace_prefix)

        if extra_namespaces is not None:
            _extra_namespaces = to_c_string(
                "__libscrapli__".join(["::".join(p) for p in extra_namespaces])
            )
        else:
            _extra_namespaces = to_c_string("")

        operation_id = self._raw_rpc(
            operation_id=operation_id,
            payload=_payload,
            base_namespace_prefix=_base_namespace_prefix,
            extra_namespaces=_extra_namespaces,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def raw_rpc_async(
        self,
        payload: str,
        *,
        base_namespace_prefix: str = "",
        extra_namespaces: list[tuple[str, str]] | None = None,
        operation_timeout_ns: int | None = None,
    ) -> Result:
        """
        Execute a "raw" / user crafted rpc operation.

        Args:
            payload: the raw rpc payload
            base_namespace_prefix: prefix to use for hte base/default netconf base namespace
            extra_namespaces: optional list of pairs of prefix::namespaces. this plus the base
                namespace prefix can allow for weird cases like nxos where the base namespace must
                be prefixed and then additional namespaces indicating desired targets must be added
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

        _payload = to_c_string(payload)
        _base_namespace_prefix = to_c_string(base_namespace_prefix)

        if extra_namespaces is not None:
            _extra_namespaces = to_c_string(
                "__libscrapli__".join(["::".join(p) for p in extra_namespaces])
            )
        else:
            _extra_namespaces = to_c_string("")

        operation_id = self._raw_rpc(
            operation_id=operation_id,
            payload=_payload,
            base_namespace_prefix=_base_namespace_prefix,
            extra_namespaces=_extra_namespaces,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _get_config(  # noqa: PLR0913,too-many-locals
        self,
        *,
        operation_id: OperationIdPointer,
        source: c_char_p,
        filter_: c_char_p,
        filter_type: c_char_p,
        filter_namespace_prefix: c_char_p,
        filter_namespace: c_char_p,
        defaults_type: c_char_p,
    ) -> c_uint:
        status = self.ffi_mapping.netconf_mapping.get_config(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            source=source,
            filter_=filter_,
            filter_type=filter_type,
            filter_namespace_prefix=filter_namespace_prefix,
            filter_namespace=filter_namespace,
            defaults_type=defaults_type,
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
        operation_timeout_ns: int | None = None,
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

        _source = to_c_string(source)
        _filter = to_c_string(filter_)
        _filter_type = to_c_string(filter_type)
        _filter_namespace_prefix = to_c_string(filter_namespace_prefix)
        _filter_namespace = to_c_string(filter_namespace)
        _defaults_type = to_c_string(defaults_type)

        operation_id = self._get_config(
            operation_id=operation_id,
            source=_source,
            filter_=_filter,
            filter_type=_filter_type,
            filter_namespace_prefix=_filter_namespace_prefix,
            filter_namespace=_filter_namespace,
            defaults_type=_defaults_type,
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
        operation_timeout_ns: int | None = None,
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

        _source = to_c_string(source)
        _filter = to_c_string(filter_)
        _filter_type = to_c_string(filter_type)
        _filter_namespace_prefix = to_c_string(filter_namespace_prefix)
        _filter_namespace = to_c_string(filter_namespace)
        _defaults_type = to_c_string(defaults_type)

        operation_id = self._get_config(
            operation_id=operation_id,
            source=_source,
            filter_=_filter,
            filter_type=_filter_type,
            filter_namespace_prefix=_filter_namespace_prefix,
            filter_namespace=_filter_namespace,
            defaults_type=_defaults_type,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _edit_config(
        self,
        *,
        operation_id: OperationIdPointer,
        config: c_char_p,
        target: c_char_p,
    ) -> c_uint:
        status = self.ffi_mapping.netconf_mapping.edit_config(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            config=config,
            target=target,
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
        operation_timeout_ns: int | None = None,
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

        _config = to_c_string(config)
        _target = to_c_string(target)

        operation_id = self._edit_config(
            operation_id=operation_id,
            config=_config,
            target=_target,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def edit_config_async(
        self,
        *,
        config: str = "",
        target: DatastoreType = DatastoreType.RUNNING,
        operation_timeout_ns: int | None = None,
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

        _config = to_c_string(config)
        _target = to_c_string(target)

        operation_id = self._edit_config(
            operation_id=operation_id,
            config=_config,
            target=_target,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _copy_config(
        self,
        *,
        operation_id: OperationIdPointer,
        target: c_char_p,
        source: c_char_p,
    ) -> c_uint:
        status = self.ffi_mapping.netconf_mapping.copy_config(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            target=target,
            source=source,
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
        operation_timeout_ns: int | None = None,
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

        _target = to_c_string(target)
        _source = to_c_string(source)

        operation_id = self._copy_config(
            operation_id=operation_id,
            target=_target,
            source=_source,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def copy_config_async(
        self,
        *,
        target: DatastoreType = DatastoreType.RUNNING,
        source: DatastoreType = DatastoreType.STARTUP,
        operation_timeout_ns: int | None = None,
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

        _target = to_c_string(target)
        _source = to_c_string(source)

        operation_id = self._copy_config(
            operation_id=operation_id,
            target=_target,
            source=_source,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _delete_config(
        self,
        *,
        operation_id: OperationIdPointer,
        target: c_char_p,
    ) -> c_uint:
        status = self.ffi_mapping.netconf_mapping.delete_config(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            target=target,
        )
        if status != 0:
            raise SubmitOperationException("submitting delete-config operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def delete_config(
        self,
        *,
        target: DatastoreType = DatastoreType.RUNNING,
        operation_timeout_ns: int | None = None,
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

        _target = to_c_string(target)

        operation_id = self._delete_config(
            operation_id=operation_id,
            target=_target,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def delete_config_async(
        self,
        *,
        target: DatastoreType = DatastoreType.RUNNING,
        operation_timeout_ns: int | None = None,
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

        _target = to_c_string(target)

        operation_id = self._delete_config(
            operation_id=operation_id,
            target=_target,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _lock(
        self,
        *,
        operation_id: OperationIdPointer,
        target: c_char_p,
    ) -> c_uint:
        status = self.ffi_mapping.netconf_mapping.lock(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            target=target,
        )
        if status != 0:
            raise SubmitOperationException("submitting lock operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def lock(
        self,
        *,
        target: DatastoreType = DatastoreType.RUNNING,
        operation_timeout_ns: int | None = None,
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

        _target = to_c_string(target)

        operation_id = self._lock(
            operation_id=operation_id,
            target=_target,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def lock_async(
        self,
        *,
        target: DatastoreType = DatastoreType.RUNNING,
        operation_timeout_ns: int | None = None,
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

        _target = to_c_string(target)

        operation_id = self._lock(
            operation_id=operation_id,
            target=_target,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _unlock(
        self,
        *,
        operation_id: OperationIdPointer,
        target: c_char_p,
    ) -> c_uint:
        status = self.ffi_mapping.netconf_mapping.unlock(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            target=target,
        )
        if status != 0:
            raise SubmitOperationException("submitting unlock operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def unlock(
        self,
        *,
        target: DatastoreType = DatastoreType.RUNNING,
        operation_timeout_ns: int | None = None,
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

        _target = to_c_string(target)

        operation_id = self._unlock(
            operation_id=operation_id,
            target=_target,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def unlock_async(
        self,
        *,
        target: DatastoreType = DatastoreType.RUNNING,
        operation_timeout_ns: int | None = None,
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

        _target = to_c_string(target)

        operation_id = self._unlock(
            operation_id=operation_id,
            target=_target,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _get(  # noqa: PLR0913,too-many-locals
        self,
        *,
        operation_id: OperationIdPointer,
        filter_: c_char_p,
        filter_type: c_char_p,
        filter_namespace_prefix: c_char_p,
        filter_namespace: c_char_p,
        defaults_type: c_char_p,
    ) -> c_uint:
        status = self.ffi_mapping.netconf_mapping.get(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            filter_=filter_,
            filter_type=filter_type,
            filter_namespace_prefix=filter_namespace_prefix,
            filter_namespace=filter_namespace,
            defaults_type=defaults_type,
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
        operation_timeout_ns: int | None = None,
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

        _filter = to_c_string(filter_)
        _filter_type = to_c_string(filter_type)
        _filter_namespace_prefix = to_c_string(filter_namespace_prefix)
        _filter_namespace = to_c_string(filter_namespace)
        _defaults_type = to_c_string(defaults_type)

        operation_id = self._get(
            operation_id=operation_id,
            filter_=_filter,
            filter_type=_filter_type,
            filter_namespace_prefix=_filter_namespace_prefix,
            filter_namespace=_filter_namespace,
            defaults_type=_defaults_type,
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
        operation_timeout_ns: int | None = None,
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

        _filter = to_c_string(filter_)
        _filter_type = to_c_string(filter_type)
        _filter_namespace_prefix = to_c_string(filter_namespace_prefix)
        _filter_namespace = to_c_string(filter_namespace)
        _defaults_type = to_c_string(defaults_type)

        operation_id = self._get(
            operation_id=operation_id,
            filter_=_filter,
            filter_type=_filter_type,
            filter_namespace_prefix=_filter_namespace_prefix,
            filter_namespace=_filter_namespace,
            defaults_type=_defaults_type,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _close_session(
        self,
        *,
        operation_id: OperationIdPointer,
    ) -> c_uint:
        status = self.ffi_mapping.netconf_mapping.close_session(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
        )
        if status != 0:
            raise SubmitOperationException("submitting close-session operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def close_session(
        self,
        *,
        operation_timeout_ns: int | None = None,
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

        operation_id = self._close_session(
            operation_id=operation_id,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def close_session_async(
        self,
        *,
        operation_timeout_ns: int | None = None,
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

        operation_id = self._close_session(
            operation_id=operation_id,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _kill_session(
        self,
        *,
        operation_id: OperationIdPointer,
        session_id: int,
    ) -> c_uint:
        status = self.ffi_mapping.netconf_mapping.kill_session(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
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
        operation_timeout_ns: int | None = None,
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

        operation_id = self._kill_session(
            operation_id=operation_id,
            session_id=session_id,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def kill_session_async(
        self,
        session_id: int,
        *,
        operation_timeout_ns: int | None = None,
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

        operation_id = self._kill_session(
            operation_id=operation_id,
            session_id=session_id,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _commit(
        self,
        *,
        operation_id: OperationIdPointer,
    ) -> c_uint:
        status = self.ffi_mapping.netconf_mapping.commit(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
        )
        if status != 0:
            raise SubmitOperationException("submitting commit operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def commit(
        self,
        *,
        operation_timeout_ns: int | None = None,
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

        operation_id = self._commit(
            operation_id=operation_id,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def commit_async(
        self,
        *,
        operation_timeout_ns: int | None = None,
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

        operation_id = self._commit(
            operation_id=operation_id,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _discard(
        self,
        *,
        operation_id: OperationIdPointer,
    ) -> c_uint:
        status = self.ffi_mapping.netconf_mapping.discard(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
        )
        if status != 0:
            raise SubmitOperationException("submitting discard operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def discard(
        self,
        *,
        operation_timeout_ns: int | None = None,
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

        operation_id = self._discard(
            operation_id=operation_id,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def discard_async(
        self,
        *,
        operation_timeout_ns: int | None = None,
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

        operation_id = self._discard(
            operation_id=operation_id,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _cancel_commit(
        self,
        *,
        operation_id: OperationIdPointer,
    ) -> c_uint:
        status = self.ffi_mapping.netconf_mapping.cancel_commit(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
        )
        if status != 0:
            raise SubmitOperationException("submitting cancel-commit operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def cancel_commit(
        self,
        *,
        operation_timeout_ns: int | None = None,
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

        operation_id = self._cancel_commit(
            operation_id=operation_id,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def cancel_commit_async(
        self,
        *,
        operation_timeout_ns: int | None = None,
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

        operation_id = self._cancel_commit(
            operation_id=operation_id,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _validate(
        self,
        *,
        operation_id: OperationIdPointer,
        source: c_char_p,
    ) -> c_uint:
        status = self.ffi_mapping.netconf_mapping.validate(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            source=source,
        )
        if status != 0:
            raise SubmitOperationException("submitting validate operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def validate(
        self,
        *,
        source: DatastoreType = DatastoreType.RUNNING,
        operation_timeout_ns: int | None = None,
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

        _source = to_c_string(source)

        operation_id = self._validate(
            operation_id=operation_id,
            source=_source,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def validate_async(
        self,
        *,
        source: DatastoreType = DatastoreType.RUNNING,
        operation_timeout_ns: int | None = None,
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

        _source = to_c_string(source)

        operation_id = self._validate(
            operation_id=operation_id,
            source=_source,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _get_schema(
        self,
        *,
        operation_id: OperationIdPointer,
        identifier: c_char_p,
        version: c_char_p,
        format_: c_char_p,
    ) -> c_uint:
        status = self.ffi_mapping.netconf_mapping.get_schema(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            identifier=identifier,
            version=version,
            format_=format_,
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
        operation_timeout_ns: int | None = None,
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

        _identifier = to_c_string(identifier)
        _version = to_c_string(version)
        _format = to_c_string(format_)

        operation_id = self._get_schema(
            operation_id=operation_id,
            identifier=_identifier,
            version=_version,
            format_=_format,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def get_schema_async(
        self,
        identifier: str,
        *,
        version: str = "",
        format_: SchemaFormat = SchemaFormat.YANG,
        operation_timeout_ns: int | None = None,
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

        _identifier = to_c_string(identifier)
        _version = to_c_string(version)
        _format = to_c_string(format_)

        operation_id = self._get_schema(
            operation_id=operation_id,
            identifier=_identifier,
            version=_version,
            format_=_format,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _get_data(  # noqa: PLR0913,too-many-locals
        self,
        *,
        operation_id: OperationIdPointer,
        source: c_char_p,
        filter_: c_char_p,
        filter_type: c_char_p,
        filter_namespace_prefix: c_char_p,
        filter_namespace: c_char_p,
        config_filter: c_char_p,
        origin_filters: c_char_p,
        max_depth: int,
        with_origin: bool,
        defaults_type: c_char_p,
    ) -> c_uint:
        status = self.ffi_mapping.netconf_mapping.get_data(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            source=source,
            filter_=filter_,
            filter_type=filter_type,
            filter_namespace_prefix=filter_namespace_prefix,
            filter_namespace=filter_namespace,
            config_filter=config_filter,
            origin_filters=origin_filters,
            max_depth=c_int(max_depth),
            with_origin=c_bool(with_origin),
            defaults_type=defaults_type,
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
        operation_timeout_ns: int | None = None,
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

        _source = to_c_string(source)
        _filter = to_c_string(filter_)
        _filter_type = to_c_string(filter_type)
        _filter_namespace_prefix = to_c_string(filter_namespace_prefix)
        _filter_namespace = to_c_string(filter_namespace)
        _config_filter = to_c_string(config_filter)
        _origin_filters = to_c_string(origin_filters)
        _defaults_type = to_c_string(defaults_type)

        operation_id = self._get_data(
            operation_id=operation_id,
            source=_source,
            filter_=_filter,
            filter_type=_filter_type,
            filter_namespace_prefix=_filter_namespace_prefix,
            filter_namespace=_filter_namespace,
            config_filter=_config_filter,
            origin_filters=_origin_filters,
            max_depth=max_depth,
            with_origin=with_origin,
            defaults_type=_defaults_type,
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
        operation_timeout_ns: int | None = None,
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

        _source = to_c_string(source)
        _filter = to_c_string(filter_)
        _filter_type = to_c_string(filter_type)
        _filter_namespace_prefix = to_c_string(filter_namespace_prefix)
        _filter_namespace = to_c_string(filter_namespace)
        _config_filter = to_c_string(config_filter)
        _origin_filters = to_c_string(origin_filters)
        _defaults_type = to_c_string(defaults_type)

        operation_id = self._get_data(
            operation_id=operation_id,
            source=_source,
            filter_=_filter,
            filter_type=_filter_type,
            filter_namespace_prefix=_filter_namespace_prefix,
            filter_namespace=_filter_namespace,
            config_filter=_config_filter,
            origin_filters=_origin_filters,
            max_depth=max_depth,
            with_origin=with_origin,
            defaults_type=_defaults_type,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _edit_data(
        self,
        *,
        operation_id: OperationIdPointer,
        content: c_char_p,
        target: c_char_p,
    ) -> c_uint:
        status = self.ffi_mapping.netconf_mapping.edit_data(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            content=content,
            target=target,
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
        operation_timeout_ns: int | None = None,
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

        _content = to_c_string(content)
        _target = to_c_string(target)

        operation_id = self._edit_data(
            operation_id=operation_id,
            content=_content,
            target=_target,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def edit_data_async(
        self,
        content: str,
        *,
        target: DatastoreType = DatastoreType.RUNNING,
        operation_timeout_ns: int | None = None,
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

        _content = to_c_string(content)
        _target = to_c_string(target)

        operation_id = self._edit_data(
            operation_id=operation_id,
            content=_content,
            target=_target,
        )

        return await self._get_result_async(operation_id=operation_id)

    def _action(
        self,
        *,
        operation_id: OperationIdPointer,
        action: c_char_p,
    ) -> c_uint:
        status = self.ffi_mapping.netconf_mapping.action(
            ptr=self._ptr_or_exception(),
            operation_id=operation_id,
            action=action,
        )
        if status != 0:
            raise SubmitOperationException("submitting action operation failed")

        return c_uint(operation_id.contents.value)

    @handle_operation_timeout
    def action(
        self,
        action: str,
        *,
        operation_timeout_ns: int | None = None,
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

        _action = to_c_string(action)

        operation_id = self._action(
            operation_id=operation_id,
            action=_action,
        )

        return self._get_result(operation_id=operation_id)

    @handle_operation_timeout_async
    async def action_async(
        self,
        action: str,
        *,
        operation_timeout_ns: int | None = None,
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

        _action = to_c_string(action)

        operation_id = self._action(
            operation_id=operation_id,
            action=_action,
        )

        return await self._get_result_async(operation_id=operation_id)
