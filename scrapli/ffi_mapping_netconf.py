"""scrapli.ffi_mapping_cli"""

from collections.abc import Callable
from ctypes import (
    CDLL,
    c_bool,
    c_char_p,
    c_int,
    c_uint8,
    c_uint64,
    c_void_p,
)

from scrapli.ffi_types import (
    CANCEL,
    CancelPointer,
    DriverPointer,
    IntPointer,
    LibScrapliFFIResult,
    OperationId,
    OperationIdPointer,
    U8Pointer,
    U64Pointer,
    USizePointer,
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

    def __init__(self, lib: CDLL) -> None:  # noqa: PLR0915
        self._alloc: Callable[
            [
                c_char_p,
                c_void_p,
            ],
            DriverPointer,
        ] = lib.ls_netconf_alloc
        lib.ls_netconf_alloc.argtypes = [
            c_char_p,
            c_void_p,
        ]
        lib.ls_netconf_alloc.restype = DriverPointer

        self._open: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
            ],
            int,
        ] = lib.ls_netconf_open
        lib.ls_netconf_open.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
        ]
        lib.ls_netconf_open.restype = c_uint8

        self._close: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
                c_bool,
            ],
            int,
        ] = lib.ls_netconf_close
        lib.ls_netconf_close.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
            c_bool,
        ]
        lib.ls_netconf_close.restype = c_uint8

        self._fetch_sizes: Callable[
            [
                DriverPointer,
                OperationId,
                USizePointer,
                USizePointer,
                USizePointer,
                USizePointer,
                USizePointer,
                USizePointer,
                USizePointer,
            ],
            int,
        ] = lib.ls_netconf_fetch_operation_sizes
        lib.ls_netconf_fetch_operation_sizes.argtypes = [
            DriverPointer,
            OperationId,
            USizePointer,
            USizePointer,
            USizePointer,
            USizePointer,
            USizePointer,
            USizePointer,
            USizePointer,
        ]
        lib.ls_netconf_fetch_operation_sizes.restype = c_uint8

        self._fetch: Callable[
            [
                DriverPointer,
                OperationId,
                U64Pointer,
                U64Pointer,
                ZigSlicePointer,
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
            U64Pointer,
            U64Pointer,
            ZigSlicePointer,
            ZigSlicePointer,
            ZigSlicePointer,
            ZigSlicePointer,
            ZigSlicePointer,
            ZigSlicePointer,
            ZigSlicePointer,
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

        self._get_subscription_id: Callable[
            [
                c_char_p,
                U64Pointer,
            ],
            int,
        ] = lib.ls_netconf_get_subscription_id
        lib.ls_netconf_get_subscription_id.argtypes = [
            c_char_p,
            U64Pointer,
        ]
        lib.ls_netconf_get_subscription_id.restype = c_uint8

        self._get_next_notification_size: Callable[
            [
                DriverPointer,
                U64Pointer,
            ],
            int,
        ] = lib.ls_netconf_next_notification_message_size
        lib.ls_netconf_next_notification_message_size.argtypes = [
            DriverPointer,
            U64Pointer,
        ]
        lib.ls_netconf_next_notification_message_size.restype = c_uint8

        self._get_next_notification: Callable[
            [
                DriverPointer,
                ZigSlicePointer,
            ],
            int,
        ] = lib.ls_netconf_next_notification_message
        lib.ls_netconf_next_notification_message.argtypes = [
            DriverPointer,
            ZigSlicePointer,
        ]
        lib.ls_netconf_next_notification_message.restype = c_uint8

        self._get_next_subscription_size: Callable[
            [
                DriverPointer,
                c_uint64,
                U64Pointer,
            ],
            int,
        ] = lib.ls_netconf_next_subscription_message_size
        lib.ls_netconf_next_subscription_message_size.argtypes = [
            DriverPointer,
            c_uint64,
            U64Pointer,
        ]
        lib.ls_netconf_next_subscription_message_size.restype = c_uint8

        self._get_next_subscription: Callable[
            [
                DriverPointer,
                c_uint64,
                ZigSlicePointer,
            ],
            int,
        ] = lib.ls_netconf_next_subscription_message
        lib.ls_netconf_next_subscription_message.argtypes = [
            DriverPointer,
            c_uint64,
            ZigSlicePointer,
        ]
        lib.ls_netconf_next_subscription_message.restype = c_uint8

        self._raw_rpc: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
                c_char_p,
                c_char_p,
                c_char_p,
            ],
            int,
        ] = lib.ls_netconf_raw_rpc
        lib.ls_netconf_raw_rpc.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
            c_char_p,
            c_char_p,
            c_char_p,
        ]
        lib.ls_netconf_raw_rpc.restype = c_uint8

        self._get_config: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
                U8Pointer,
                c_char_p,
                U8Pointer,
                c_char_p,
                c_char_p,
                U8Pointer,
            ],
            int,
        ] = lib.ls_netconf_get_config
        lib.ls_netconf_get_config.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
            U8Pointer,
            c_char_p,
            U8Pointer,
            c_char_p,
            c_char_p,
            U8Pointer,
        ]
        lib.ls_netconf_get_config.restype = c_uint8

        self._edit_config: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
                c_char_p,
                U8Pointer,
                U8Pointer,
                U8Pointer,
                U8Pointer,
            ],
            int,
        ] = lib.ls_netconf_edit_config
        lib.ls_netconf_edit_config.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
            c_char_p,
            U8Pointer,
            U8Pointer,
            U8Pointer,
            U8Pointer,
        ]
        lib.ls_netconf_edit_config.restype = c_uint8

        self._copy_config: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
                U8Pointer,
                U8Pointer,
            ],
            int,
        ] = lib.ls_netconf_copy_config
        lib.ls_netconf_copy_config.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
            U8Pointer,
            U8Pointer,
        ]
        lib.ls_netconf_copy_config.restype = c_uint8

        self._delete_config: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
                U8Pointer,
            ],
            int,
        ] = lib.ls_netconf_delete_config
        lib.ls_netconf_delete_config.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
            U8Pointer,
        ]
        lib.ls_netconf_delete_config.restype = c_uint8

        self._lock: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
                U8Pointer,
            ],
            int,
        ] = lib.ls_netconf_lock
        lib.ls_netconf_lock.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
            U8Pointer,
        ]
        lib.ls_netconf_lock.restype = c_uint8

        self._unlock: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
                U8Pointer,
            ],
            int,
        ] = lib.ls_netconf_unlock
        lib.ls_netconf_unlock.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
            U8Pointer,
        ]
        lib.ls_netconf_unlock.restype = c_uint8

        self._get: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
                c_char_p,
                U8Pointer,
                c_char_p,
                c_char_p,
                U8Pointer,
            ],
            int,
        ] = lib.ls_netconf_get
        lib.ls_netconf_get.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
            c_char_p,
            U8Pointer,
            c_char_p,
            c_char_p,
            U8Pointer,
        ]
        lib.ls_netconf_get.restype = c_uint8

        self._close_session: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
            ],
            int,
        ] = lib.ls_netconf_close_session
        lib.ls_netconf_close_session.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
        ]
        lib.ls_netconf_close_session.restype = c_uint8

        self._kill_session: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
                c_int,
            ],
            int,
        ] = lib.ls_netconf_kill_session
        lib.ls_netconf_kill_session.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
            c_int,
        ]
        lib.ls_netconf_kill_session.restype = c_uint8

        self._commit: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
            ],
            int,
        ] = lib.ls_netconf_commit
        lib.ls_netconf_commit.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
        ]
        lib.ls_netconf_commit.restype = c_uint8

        self._discard: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
            ],
            int,
        ] = lib.ls_netconf_discard
        lib.ls_netconf_discard.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
        ]
        lib.ls_netconf_discard.restype = c_uint8

        self._cancel_commit: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
                c_char_p,
            ],
            int,
        ] = lib.ls_netconf_cancel_commit
        lib.ls_netconf_cancel_commit.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
            c_char_p,
        ]
        lib.ls_netconf_cancel_commit.restype = c_uint8

        self._validate: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
                U8Pointer,
            ],
            int,
        ] = lib.ls_netconf_validate
        lib.ls_netconf_validate.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
            U8Pointer,
        ]
        lib.ls_netconf_validate.restype = c_uint8

        self._get_schema: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
                c_char_p,
                c_char_p,
                U8Pointer,
            ],
            int,
        ] = lib.ls_netconf_get_schema
        lib.ls_netconf_get_schema.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
            c_char_p,
            c_char_p,
            U8Pointer,
        ]
        lib.ls_netconf_get_schema.restype = c_uint8

        self._get_data: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
                U8Pointer,
                c_char_p,
                U8Pointer,
                c_char_p,
                c_char_p,
                U8Pointer,
                c_char_p,
                c_int,
                c_bool,
                U8Pointer,
            ],
            int,
        ] = lib.ls_netconf_get_data
        lib.ls_netconf_get_data.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
            U8Pointer,
            c_char_p,
            U8Pointer,
            c_char_p,
            c_char_p,
            U8Pointer,
            c_char_p,
            c_int,
            c_bool,
            U8Pointer,
        ]
        lib.ls_netconf_get_data.restype = c_uint8

        self._edit_data: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
                U8Pointer,
                c_char_p,
                U8Pointer,
            ],
            int,
        ] = lib.ls_netconf_edit_data
        lib.ls_netconf_edit_data.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
            U8Pointer,
            c_char_p,
            U8Pointer,
        ]
        lib.ls_netconf_edit_data.restype = c_uint8

        self._action: Callable[
            [
                DriverPointer,
                OperationIdPointer,
                CancelPointer,
                c_char_p,
            ],
            int,
        ] = lib.ls_netconf_action
        lib.ls_netconf_action.argtypes = [
            DriverPointer,
            OperationIdPointer,
            CancelPointer,
            c_char_p,
        ]
        lib.ls_netconf_action.restype = c_uint8

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
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._alloc(
            host,
            options_ptr,
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
            ptr: the ptr to the libscrapli netconf object.
            operation_id_ptr: c_int pointer that is filled with the operation id to poll for
                completion.

        Returns:
            N/A

        Raises:
            FFIException: if submitting the open operation failed

        """
        self._open(
            ptr,
            operation_id_ptr,
            CANCEL,
        )

    def close(
        self,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
        force: c_bool,
    ) -> None:
        """
        Close the driver at ptr.

        Should (generally) not be called directly/by users.

        Args:
            ptr: the ptr to the libscrapli netconf object.
            operation_id_ptr: c_int pointer that is filled with the operation id to poll for
                completion.
            force: bool indicating if the connection should skip sending close-session rpc or not

        Returns:
            N/A

        Raises:
            FFIException: if submitting the close operation failed

        """
        LibScrapliFFIResult(
            self._close(
                ptr,
                operation_id_ptr,
                CANCEL,
                force,
            )
        ).raise_if_error(
            message="close operation failed",
        )

    def fetch_sizes(
        self,
        *,
        ptr: DriverPointer,
        operation_id_value: OperationId,
        input_size: USizePointer,
        result_raw_size: USizePointer,
        result_size: USizePointer,
        rpc_warnings_size: USizePointer,
        rpc_errors_size: USizePointer,
        err_size: USizePointer,
        last_err_str_size: USizePointer,
    ) -> None:
        """
        Fetch the sizes of a netconf operation's results.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id_value: operation id of which to poll
            input_size: int pointer to fill with the operation's input size
            result_raw_size: int pointer to fill with the operation's result raw size
            result_size:  int pointer to fill with the operation's result size
            rpc_warnings_size: int pointer to fill with the size of any rpc warning string
            rpc_errors_size: int pointer to fill with the size of any rpc error string
            err_size: int pointer to fill with the operation's error size
            last_err_str_size: int pointer to fill with the operation's last error string size

        Returns:
            N/A

        Raises:
            FFIException: if submitting the fetch sizes operation failed

        """
        LibScrapliFFIResult(
            self._fetch_sizes(
                ptr,
                operation_id_value,
                input_size,
                result_raw_size,
                result_size,
                rpc_warnings_size,
                rpc_errors_size,
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
        operation_id_value: OperationId,
        start_time: U64Pointer,
        end_time: U64Pointer,
        input_slice: ZigSlicePointer,
        result_raw_slice: ZigSlicePointer,
        result_slice: ZigSlicePointer,
        rpc_warnings_slice: ZigSlicePointer,
        rpc_errors_slice: ZigSlicePointer,
        err_slice: ZigSlicePointer,
        last_err_string: ZigSlicePointer,
    ) -> None:
        """
        Fetch the result of a cli operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id_value: operation id of which to poll
            start_time: int pointer to fill with the operation's start time
            end_time: int pointer to fill with the operation's end time
            input_slice: pre allocated slice to fill with the operations input
            result_raw_slice: pre allocated slice to fill with the operations result raw
            result_slice: pre allocated slice to fill with the operations result
            rpc_warnings_slice: pre allocated slice to fill with the rpc warnings string
            rpc_errors_slice: pre allocated slice to fill with the rpc errors string
            err_slice: pre allocated slice to fill with the operations error
            last_err_string: pre allocated slice to fill with the operations last error string

        Returns:
            N/A

        Raises:
            FFIException: if submitting the fetch operation failed

        """
        LibScrapliFFIResult(
            self._fetch(
                ptr,
                operation_id_value,
                start_time,
                end_time,
                input_slice,
                result_raw_slice,
                result_slice,
                rpc_warnings_slice,
                rpc_errors_slice,
                err_slice,
                last_err_string,
            )
        ).raise_if_error(
            message="fetching operation content failed",
        )

    def get_session_id(
        self,
        *,
        ptr: DriverPointer,
        session_id: IntPointer,
    ) -> None:
        """
        Get the session id of the Netconf object/session.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            session_id: int pointer to fill with the session id

        Returns:
            N/A

        Raises:
            FFIException: if submitting the session id operation failed

        """
        LibScrapliFFIResult(
            self._get_session_id(
                ptr,
                session_id,
            )
        ).raise_if_error(
            message="submitting getting session id failed",
        )

    def get_subscription_id(
        self,
        *,
        payload: c_char_p,
        subscription_id: U64Pointer,
    ) -> None:
        """
        Get the subscription id from the given subscription response payload.

        Should (generally) not be called directly/by users.

        Args:
            payload: payload to get the subscription id from
            subscription_id: int pointer to fill with the subscription id

        Returns:
            N/A

        Raises:
            FFIException: if submitting the get subscription id operation failed

        """
        LibScrapliFFIResult(
            self._get_subscription_id(
                payload,
                subscription_id,
            )
        ).raise_if_error(
            message="submitting getting subscription id failed",
        )

    def get_next_notification_size(
        self,
        *,
        ptr: DriverPointer,
        notification_size: U64Pointer,
    ) -> None:
        """
        Get the size of the next notification message.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            notification_size: int pointer to fill with the session id

        Returns:
            N/A

        Raises:
            FFIException: if submitting the get next notification size operation failed

        """
        LibScrapliFFIResult(
            self._get_next_notification_size(
                ptr,
                notification_size,
            )
        ).raise_if_error(
            message="submitting getting next notification size failed",
        )

    def get_next_notification(
        self,
        *,
        ptr: DriverPointer,
        notification_slice: ZigSlicePointer,
    ) -> None:
        """
        Get the next notification message.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            notification_slice: pre populted slice to fill with the notification

        Returns:
            N/A

        Raises:
            FFIException: if submitting the get next notification operation failed

        """
        LibScrapliFFIResult(
            self._get_next_notification(
                ptr,
                notification_slice,
            )
        ).raise_if_error(
            message="submitting getting next notification failed",
        )

    def get_next_subscription_size(
        self,
        *,
        ptr: DriverPointer,
        subscription_id: c_uint64,
        subscription_size: U64Pointer,
    ) -> None:
        """
        Get the size of the next subscription message for the given id.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            subscription_id: subscription id to fetch a message for
            subscription_size: int pointer to fill with the session id

        Returns:
            N/A

        Raises:
            FFIException: if submitting the get next subscription size operation failed

        """
        LibScrapliFFIResult(
            self._get_next_subscription_size(
                ptr,
                subscription_id,
                subscription_size,
            )
        ).raise_if_error(
            message="submitting getting next subscription size failed",
        )

    def get_next_subscription(
        self,
        *,
        ptr: DriverPointer,
        subscription_id: c_uint64,
        subscription_slice: ZigSlicePointer,
    ) -> None:
        """
        Get the next subscription message for the given id.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            subscription_id: subscription id to fetch a message for
            subscription_slice: pre populted slice to fill with the notification

        Returns:
            N/A

        Raises:
            FFIException: if submitting the get next subscription operation failed

        """
        LibScrapliFFIResult(
            self._get_next_subscription(
                ptr,
                subscription_id,
                subscription_slice,
            )
        ).raise_if_error(
            message="submitting getting next subscription failed",
        )

    def raw_rpc(
        self,
        *,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
        payload: c_char_p,
        base_namespace_prefix: c_char_p,
        extra_namespaces: c_char_p,
    ) -> None:
        """
        Execute a "raw" / user defined rpc operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id_ptr: int pointer to fill with the id of the submitted operation
            payload: the payload to write into the outer rpc element
            base_namespace_prefix: prefix to use for hte base/default netconf base namespace
            extra_namespaces: extra namespace::prefix pairs (using "::" as split there), and
                split by "__libscrapli__" for additional pairs. this plus the base namespace
                prefix can allow for weird cases like nxos where the base namespace must be
                prefixed and then additional namespaces indicating desired targets must be added

        Returns:
            N/A

        Raises:
            FFIException: if submitting the raw rpc operation failed

        """
        LibScrapliFFIResult(
            self._raw_rpc(
                ptr,
                operation_id_ptr,
                CANCEL,
                payload,
                base_namespace_prefix,
                extra_namespaces,
            )
        ).raise_if_error(
            message="submitting raw rpc operation failed",
        )

    def get_config(
        self,
        *,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
        source: U8Pointer,
        filter_: c_char_p,
        filter_type: U8Pointer,
        filter_namespace_prefix: c_char_p,
        filter_namespace: c_char_p,
        defaults_type: U8Pointer,
    ) -> None:
        """
        Execute a get-config rpc operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id_ptr: int pointer to fill with the id of the submitted operation
            source: source data store to get config from
            filter_: filter to apply
            filter_type: filter type (subtree|xpath)
            filter_namespace_prefix: optional prefix for filter namespace
            filter_namespace: optional namespace for filter
            defaults_type: defaults type setting

        Returns:
            N/A

        Raises:
            FFIException: if submitting the get config operation failed

        """
        LibScrapliFFIResult(
            self._get_config(
                ptr,
                operation_id_ptr,
                CANCEL,
                source,
                filter_,
                filter_type,
                filter_namespace_prefix,
                filter_namespace,
                defaults_type,
            )
        ).raise_if_error(
            message="submitting get-config operation failed",
        )

    def edit_config(
        self,
        *,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
        config: c_char_p,
        target: U8Pointer,
        default_operation: U8Pointer,
        test_option: U8Pointer,
        error_option: U8Pointer,
    ) -> None:
        """
        Execute an edit-config rpc operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id_ptr: int pointer to fill with the id of the submitted operation
            config: the config to send
            target: the target datastore
            default_operation: string that looks like default operation enum (or empty)
            test_option: test option (or empty str)
            error_option: error option (or empty str)

        Returns:
            N/A

        Raises:
            FFIException: if submitting the edit config operation failed

        """
        LibScrapliFFIResult(
            self._edit_config(
                ptr,
                operation_id_ptr,
                CANCEL,
                config,
                target,
                default_operation,
                test_option,
                error_option,
            )
        ).raise_if_error(
            message="submitting edit-config operation failed",
        )

    def copy_config(
        self,
        *,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
        target: U8Pointer,
        source: U8Pointer,
    ) -> None:
        """
        Execute a copy-config rpc operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id_ptr: int pointer to fill with the id of the submitted operation
            target: the target/destination datastore to copy to
            source: the source datastore to copy from

        Returns:
            N/A

        Raises:
            FFIException: if submitting the copy config operation failed

        """
        LibScrapliFFIResult(
            self._copy_config(
                ptr,
                operation_id_ptr,
                CANCEL,
                target,
                source,
            )
        ).raise_if_error(
            message="submitting copy-config operation failed",
        )

    def delete_config(
        self,
        *,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
        target: U8Pointer,
    ) -> None:
        """
        Execute a delete-config rpc operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id_ptr: int pointer to fill with the id of the submitted operation
            target: the target/destination datastore to delete

        Returns:
            N/A

        Raises:
            FFIException: if submitting the delete config operation failed

        """
        LibScrapliFFIResult(
            self._delete_config(
                ptr,
                operation_id_ptr,
                CANCEL,
                target,
            )
        ).raise_if_error(
            message="submitting delete-config operation failed",
        )

    def lock(
        self,
        *,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
        target: U8Pointer,
    ) -> None:
        """
        Execute a lock rpc operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id_ptr: int pointer to fill with the id of the submitted operation
            target: the target/destination datastore to lock

        Returns:
            N/A

        Raises:
            FFIException: if submitting the lock operation failed

        """
        LibScrapliFFIResult(
            self._lock(
                ptr,
                operation_id_ptr,
                CANCEL,
                target,
            )
        ).raise_if_error(
            message="submitting lock operation failed",
        )

    def unlock(
        self,
        *,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
        target: U8Pointer,
    ) -> None:
        """
        Execute an unlock rpc operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id_ptr: int pointer to fill with the id of the submitted operation
            target: the target/destination datastore to lock

        Returns:
            N/A

        Raises:
            FFIException: if submitting the unlock operation failed

        """
        LibScrapliFFIResult(
            self._unlock(
                ptr,
                operation_id_ptr,
                CANCEL,
                target,
            )
        ).raise_if_error(
            message="submitting unlock operation failed",
        )

    def get(
        self,
        *,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
        filter_: c_char_p,
        filter_type: U8Pointer,
        filter_namespace_prefix: c_char_p,
        filter_namespace: c_char_p,
        defaults_type: U8Pointer,
    ) -> None:
        """
        Execute a get rpc operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id_ptr: int pointer to fill with the id of the submitted operation
            filter_: filter to apply
            filter_type: filter type (subtree|xpath)
            filter_namespace_prefix: optional prefix for filter namespace
            filter_namespace: optional namespace for filter
            defaults_type: defaults type setting

        Returns:
            N/A

        Raises:
            FFIException: if submitting the get operation failed

        """
        LibScrapliFFIResult(
            self._get(
                ptr,
                operation_id_ptr,
                CANCEL,
                filter_,
                filter_type,
                filter_namespace_prefix,
                filter_namespace,
                defaults_type,
            )
        ).raise_if_error(
            message="submitting get operation failed",
        )

    def close_session(
        self,
        *,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
    ) -> None:
        """
        Execute a close-config rpc operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id_ptr: int pointer to fill with the id of the submitted operation

        Returns:
            N/A

        Raises:
            FFIException: if submitting the close session operation failed

        """
        LibScrapliFFIResult(
            self._close_session(
                ptr,
                operation_id_ptr,
                CANCEL,
            )
        ).raise_if_error(
            message="submitting close-session operation failed",
        )

    def kill_session(
        self,
        *,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
        session_id: c_int,
    ) -> None:
        """
        Execute a close-config rpc operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id_ptr: int pointer to fill with the id of the submitted operation
            session_id: the session id to kill

        Returns:
            N/A

        Raises:
            FFIException: if submitting the kill session operation failed

        """
        LibScrapliFFIResult(
            self._kill_session(
                ptr,
                operation_id_ptr,
                CANCEL,
                session_id,
            )
        ).raise_if_error(
            message="submitting kill-session operation failed",
        )

    def commit(
        self,
        *,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
    ) -> None:
        """
        Execute a commit rpc operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id_ptr: int pointer to fill with the id of the submitted operation

        Returns:
            N/A

        Raises:
            FFIException: if submitting the commit operation failed

        """
        LibScrapliFFIResult(
            self._commit(
                ptr,
                operation_id_ptr,
                CANCEL,
            )
        ).raise_if_error(
            message="submitting commit operation failed",
        )

    def discard(
        self,
        *,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
    ) -> None:
        """
        Execute a discard rpc operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id_ptr: int pointer to fill with the id of the submitted operation

        Returns:
            N/A

        Raises:
            FFIException: if submitting the discard operation failed

        """
        LibScrapliFFIResult(
            self._discard(
                ptr,
                operation_id_ptr,
                CANCEL,
            )
        ).raise_if_error(
            message="submitting discard operation failed",
        )

    def cancel_commit(
        self,
        *,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
        persist_id: c_char_p,
    ) -> None:
        """
        Execute a cancel-commit rpc operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id_ptr: int pointer to fill with the id of the submitted operation
            persist_id: optional string persist-id to set on the cancel commit message

        Returns:
            N/A

        Raises:
            FFIException: if submitting the cancel commit operation failed

        """
        LibScrapliFFIResult(
            self._cancel_commit(
                ptr,
                operation_id_ptr,
                CANCEL,
                persist_id,
            )
        ).raise_if_error(
            message="submitting cancel-commit operation failed",
        )

    def validate(
        self,
        *,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
        source: U8Pointer,
    ) -> None:
        """
        Execute a validate rpc operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id_ptr: int pointer to fill with the id of the submitted operation
            source: datastore to validate

        Returns:
            N/A

        Raises:
            FFIException: if submitting the validate operation failed

        """
        LibScrapliFFIResult(
            self._validate(
                ptr,
                operation_id_ptr,
                CANCEL,
                source,
            )
        ).raise_if_error(
            message="submitting validate operation failed",
        )

    def get_schema(
        self,
        *,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
        identifier: c_char_p,
        version: c_char_p,
        format_: U8Pointer,
    ) -> None:
        """
        Execute a get-schema rpc operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id_ptr: int pointer to fill with the id of the submitted operation
            identifier: schema identifier to get
            version: optional schema version to request
            format_: schema format to apply

        Returns:
            N/A

        Raises:
            FFIException: if submitting the edit schema operation failed

        """
        LibScrapliFFIResult(
            self._get_schema(
                ptr,
                operation_id_ptr,
                CANCEL,
                identifier,
                version,
                format_,
            )
        ).raise_if_error(
            message="submitting get-schema operation failed",
        )

    def get_data(
        self,
        *,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
        source: U8Pointer,
        filter_: c_char_p,
        filter_type: U8Pointer,
        filter_namespace_prefix: c_char_p,
        filter_namespace: c_char_p,
        config_filter: U8Pointer,
        origin_filters: c_char_p,
        max_depth: c_int,
        with_origin: c_bool,
        defaults_type: U8Pointer,
    ) -> None:
        """
        Execute a get-data rpc operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id_ptr: int pointer to fill with the id of the submitted operation
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

        Returns:
            N/A

        Raises:
            FFIException: if submitting the get data operation failed

        """
        LibScrapliFFIResult(
            self._get_data(
                ptr,
                operation_id_ptr,
                CANCEL,
                source,
                filter_,
                filter_type,
                filter_namespace_prefix,
                filter_namespace,
                config_filter,
                origin_filters,
                max_depth,
                with_origin,
                defaults_type,
            )
        ).raise_if_error(
            message="submitting get-data operation failed",
        )

    def edit_data(
        self,
        *,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
        target: U8Pointer,
        content: c_char_p,
        default_operation: U8Pointer,
    ) -> None:
        """
        Execute a edit-data rpc operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id_ptr: int pointer to fill with the id of the submitted operation
            target: datastore to target
            content: full payload content to send
            default_operation: string that looks like default operation enum (or empty)

        Returns:
            N/A

        Raises:
            FFIException: if submitting the edit data operation failed

        """
        LibScrapliFFIResult(
            self._edit_data(
                ptr,
                operation_id_ptr,
                CANCEL,
                target,
                content,
                default_operation,
            )
        ).raise_if_error(
            message="submitting edit-data operation failed",
        )

    def action(
        self,
        *,
        ptr: DriverPointer,
        operation_id_ptr: OperationIdPointer,
        action: c_char_p,
    ) -> None:
        """
        Execute an action rpc operation.

        Should (generally) not be called directly/by users.

        Args:
            ptr: ptr to the netconf object
            operation_id_ptr: int pointer to fill with the id of the submitted operation
            action: the action to send

        Returns:
            N/A

        Raises:
            FFIException: if submitting the action operation failed

        """
        LibScrapliFFIResult(
            self._action(
                ptr,
                operation_id_ptr,
                CANCEL,
                action,
            )
        ).raise_if_error(
            message="submitting action operation failed",
        )
