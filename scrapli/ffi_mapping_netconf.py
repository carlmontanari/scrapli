"""scrapli.ffi_mapping_cli"""  # pylint: disable=too-many-lines,too-many-arguments,too-many-instance-attributes

from ctypes import (
    CDLL,
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
    ZigSlice,
    ZigSlicePointer,
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
        self._alloc: Callable[
            [
                LogFuncCallback,
                c_char_p,
                c_int,
                c_char_p,
            ],
            DriverPointer,
        ] = lib.ls_alloc_netconf
        lib.ls_alloc_netconf.argtypes = [
            LogFuncCallback,
            c_char_p,
            c_int,
            c_char_p,
        ]
        lib.ls_alloc_netconf.restype = DriverPointer

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
        ] = lib.ls_netconf_poll_operation
        lib.ls_netconf_poll_operation.argtypes = [
            DriverPointer,
            OperationId,
            BoolPointer,
            IntPointer,
            IntPointer,
            IntPointer,
            IntPointer,
            IntPointer,
            IntPointer,
        ]
        lib.ls_netconf_poll_operation.restype = c_uint8

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
        ] = lib.ls_netconf_wait_operation
        lib.ls_netconf_wait_operation.argtypes = [
            DriverPointer,
            OperationId,
            BoolPointer,
            IntPointer,
            IntPointer,
            IntPointer,
            IntPointer,
            IntPointer,
            IntPointer,
        ]
        lib.ls_netconf_wait_operation.restype = c_uint8

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
                ZigSlicePointer,
            ],
            int,
        ] = lib.ls_netconf_fetch_operation
        lib.ls_netconf_fetch_operation.argtypes = [
            DriverPointer,
            OperationId,
            IntPointer,
            IntPointer,
            POINTER(ZigSlice),
            POINTER(ZigSlice),
            POINTER(ZigSlice),
            POINTER(ZigSlice),
            POINTER(ZigSlice),
            POINTER(ZigSlice),
        ]
        lib.ls_netconf_fetch_operation.restype = c_uint8

        self._get_session_id: Callable[
            [
                DriverPointer,
                IntPointer,
            ],
            int,
        ] = lib.ls_netconf_get_session_id
        lib.ls_netconf_get_session_id.argtypes = [
            DriverPointer,
            IntPointer,
        ]
        lib.ls_netconf_get_session_id.restype = c_uint8

        self._raw_rpc: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
                c_char_p,
            ],
            int,
        ] = lib.ls_netconf_raw_rpc
        lib.ls_netconf_raw_rpc.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
            c_char_p,
        ]
        lib.ls_netconf_raw_rpc.restype = c_uint8

        self._get_config: Callable[
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
            ],
            int,
        ] = lib.ls_netconf_get_config
        lib.ls_netconf_get_config.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
            c_char_p,
            c_char_p,
            c_char_p,
            c_char_p,
            c_char_p,
            c_char_p,
        ]
        lib.ls_netconf_get_config.restype = c_uint8

    def alloc(
        self,
        *,
        logger_callback: LogFuncCallback,
        host: c_char_p,
        port: c_int,
        transport_kind: c_char_p,
    ) -> DriverPointer:
        """
        Allocate a Netconf object.

        Should (generally) not be called directly/by users.

        Args:
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
        return self._alloc(logger_callback, host, port, transport_kind)

    def poll(
        self,
        *,
        ptr: DriverPointer,
        operation_id: OperationId,
        done: BoolPointer,
        input_size: IntPointer,
        result_raw_size: IntPointer,
        result_size: IntPointer,
        rpc_warnings_size: IntPointer,
        rpc_errors_size: IntPointer,
        err_size: IntPointer,
    ) -> int:
        """
        Poll for the result of a netconf operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id: operation id of which to poll
            done: bool pointer that is set to true if the operation has completed
            input_size: int pointer to fill with the operation's input size
            result_raw_size: int pointer to fill with the operation's result raw size
            result_size:  int pointer to fill with the operation's result size
            rpc_warnings_size: int pointer to fill with the size of any rpc warning string
            rpc_errors_size: int pointer to fill with the size of any rpc error string
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
            rpc_warnings_size,
            rpc_errors_size,
            err_size,
        )

    def wait(
        self,
        *,
        ptr: DriverPointer,
        operation_id: OperationId,
        done: BoolPointer,
        input_size: IntPointer,
        result_raw_size: IntPointer,
        result_size: IntPointer,
        rpc_warnings_size: IntPointer,
        rpc_errors_size: IntPointer,
        err_size: IntPointer,
    ) -> int:
        """
        Wait for the result of a netconf operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id: operation id of which to poll
            done: bool pointer that is set to true if the operation has completed
            input_size: int pointer to fill with the operation's input size
            result_raw_size: int pointer to fill with the operation's result raw size
            result_size:  int pointer to fill with the operation's result size
            rpc_warnings_size: int pointer to fill with the size of any rpc warning string
            rpc_errors_size: int pointer to fill with the size of any rpc error string
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
            input_size,
            result_raw_size,
            result_size,
            rpc_warnings_size,
            rpc_errors_size,
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
        rpc_warnings_slice: ZigSlicePointer,
        rpc_errors_slice: ZigSlicePointer,
        err_slice: ZigSlicePointer,
    ) -> int:
        """
        Fetch the result of a cli operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id: operation id of which to poll
            start_time: int pointer to fill with the operation's start time
            end_time: int pointer to fill with the operation's end time
            input_slice: pre allocated slice to fill with the operations input
            result_raw_slice: pre allocated slice to fill with the operations result raw
            result_slice: pre allocated slice to fill with the operations result
            rpc_warnings_slice: pre allocated slice to fill with the rpc warnings string
            rpc_errors_slice: pre allocated slice to fill with the rpc errors string
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
            rpc_warnings_slice,
            rpc_errors_slice,
            err_slice,
        )

    def get_session_id(
        self,
        *,
        ptr: DriverPointer,
        session_id: IntPointer,
    ) -> int:
        """
        Get the session id of the Netconf object/session.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            session_id: int pointer to fill with the session id

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._get_session_id(
            ptr,
            session_id,
        )

    def raw_rpc(
        self,
        *,
        ptr: DriverPointer,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
        payload: c_char_p,
    ) -> int:
        """
        Execute a "raw" / user defined rpc operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id: int pointer to fill with the id of the submitted operation
            cancel: bool pointer that can be set to true to cancel the operation
            payload: the payload to write into the outer rpc element

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._raw_rpc(
            ptr,
            operation_id,
            cancel,
            payload,
        )

    def get_config(
        self,
        *,
        ptr: DriverPointer,
        operation_id: OperationIdPointer,
        cancel: CancelPointer,
        source: c_char_p,
        filter_: c_char_p,
        filter_type: c_char_p,
        filter_namespace_prefix: c_char_p,
        filter_namespace: c_char_p,
        defaults_type: c_char_p,
    ) -> int:
        """
        Execute a get-config rpc operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id: int pointer to fill with the id of the submitted operation
            cancel: bool pointer that can be set to true to cancel the operation

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._get_config(
            ptr,
            operation_id,
            cancel,
            source,
            filter_,
            filter_type,
            filter_namespace_prefix,
            filter_namespace,
            defaults_type,
        )
