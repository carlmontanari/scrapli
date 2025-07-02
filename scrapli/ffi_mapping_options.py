"""scrapli.ffi_mapping_options"""

from collections.abc import Callable
from ctypes import (
    CDLL,
    c_char_p,
    c_int,
    c_uint8,
    c_uint64,
)

from scrapli.ffi_types import (
    DriverPointer,
)


class LibScrapliNetconfOptionsMapping:
    """
    Mapping to libscrapli netconf option setter exported functions.

    Should not be used/called directly.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(self, lib: CDLL) -> None:
        self._set_error_tag: Callable[[DriverPointer, c_char_p], int] = (
            lib.ls_option_netconf_error_tag
        )
        lib.ls_option_netconf_error_tag.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_netconf_error_tag.restype = c_uint8

        self._set_preferred_version: Callable[[DriverPointer, c_char_p], int] = (
            lib.ls_option_netconf_preferred_version
        )
        lib.ls_option_netconf_preferred_version.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_netconf_preferred_version.restype = c_uint8

        self._set_message_poll_interva_ns: Callable[[DriverPointer, c_int], int] = (
            lib.ls_option_netconf_message_poll_interval
        )
        lib.ls_option_netconf_message_poll_interval.argtypes = [
            DriverPointer,
            c_int,
        ]
        lib.ls_option_netconf_message_poll_interval.restype = c_uint8

    def set_error_tag(self, ptr: DriverPointer, error_tag: c_char_p) -> int:
        """
        Set the error tag substring.

        Should not be used/called directly.

        Args:
            ptr: ptr to the netconf object
            error_tag: error tag substring

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_error_tag(ptr, error_tag)

    def set_preferred_version(self, ptr: DriverPointer, version: c_char_p) -> int:
        """
        Set the preferred netconf version.

        Should not be used/called directly.

        Args:
            ptr: ptr to the netconf object
            version: version string

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_preferred_version(ptr, version)

    def set_message_poll_interva_ns(self, ptr: DriverPointer, interval: c_int) -> int:
        """
        Set the netconf message poll interval.

        Should not be used/called directly.

        Args:
            ptr: ptr to the netconf object
            interval: interval in ns

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_message_poll_interva_ns(ptr, interval)


class LibScrapliSessionOptionsMapping:
    """
    Mapping to libscrapli session option setter exported functions.

    Should not be used/called directly.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(self, lib: CDLL) -> None:
        self._set_read_size: Callable[
            [
                DriverPointer,
                c_uint64,
            ],
            int,
        ] = lib.ls_option_session_read_size
        lib.ls_option_session_read_size.argtypes = [
            DriverPointer,
            c_uint64,
        ]
        lib.ls_option_session_read_size.restype = c_uint8

        self._set_return_char: Callable[
            [
                DriverPointer,
                c_char_p,
            ],
            int,
        ] = lib.ls_option_session_return_char
        lib.ls_option_session_return_char.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_session_return_char.restype = c_uint8

        self._set_operation_timeout_ns: Callable[
            [
                DriverPointer,
                c_uint64,
            ],
            int,
        ] = lib.ls_option_session_operation_timeout_ns
        lib.ls_option_session_operation_timeout_ns.argtypes = [
            DriverPointer,
            c_uint64,
        ]
        lib.ls_option_session_operation_timeout_ns.restype = c_uint8

        self._set_operation_max_search_depth: Callable[
            [
                DriverPointer,
                c_uint64,
            ],
            int,
        ] = lib.ls_option_session_operation_max_search_depth
        lib.ls_option_session_operation_max_search_depth.argtypes = [
            DriverPointer,
            c_uint64,
        ]
        lib.ls_option_session_operation_max_search_depth.restype = c_uint8

        self._set_recorder_path: Callable[
            [
                DriverPointer,
                c_char_p,
            ],
            int,
        ] = lib.ls_option_session_record_destination
        lib.ls_option_session_record_destination.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_session_record_destination.restype = c_uint8

    def set_read_size(self, ptr: DriverPointer, read_size: c_uint64) -> int:
        """
        Set the session read size.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            read_size: read size

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_read_size(ptr, read_size)

    def set_return_char(self, ptr: DriverPointer, return_char: c_char_p) -> int:
        r"""
        Set the session return char

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            return_char: return char to use in the session (usually \n, could be \r\n)

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_return_char(ptr, return_char)

    def set_operation_timeout_ns(
        self, ptr: DriverPointer, set_operation_timeout_ns: c_uint64
    ) -> int:
        """
        Set the session operation timeout in ns.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            set_operation_timeout_ns: operation timeout in ns

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_operation_timeout_ns(ptr, set_operation_timeout_ns)

    def set_operation_max_search_depth(
        self, ptr: DriverPointer, set_operation_max_search_depth: c_uint64
    ) -> int:
        """
        Set the session maximum prompt search depth

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            set_operation_max_search_depth: maximum prompt search depth (in count of chars)

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_operation_max_search_depth(ptr, set_operation_max_search_depth)

    def set_recorder_path(self, ptr: DriverPointer, set_recorder_path: c_char_p) -> int:
        """
        Set the session recorder output path

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            set_recorder_path: file path to write session recorder output to

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_recorder_path(ptr, set_recorder_path)


class LibScrapliAuthOptionsMapping:
    """
    Mapping to libscrapli auth option setter exported functions.

    Should not be used/called directly.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(self, lib: CDLL) -> None:
        self._set_username: Callable[[DriverPointer, c_char_p], int] = lib.ls_option_auth_username
        lib.ls_option_auth_username.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_auth_username.restype = c_uint8

        self._set_password: Callable[[DriverPointer, c_char_p], int] = lib.ls_option_auth_password
        lib.ls_option_auth_password.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_auth_password.restype = c_uint8

        self._set_private_key_path: Callable[[DriverPointer, c_char_p], int] = (
            lib.ls_option_auth_private_key_path
        )
        lib.ls_option_auth_private_key_path.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_auth_private_key_path.restype = c_uint8

        self._set_private_key_passphrase: Callable[[DriverPointer, c_char_p], int] = (
            lib.ls_option_auth_private_key_passphrase
        )
        lib.ls_option_auth_private_key_passphrase.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_auth_private_key_passphrase.restype = c_uint8

        self._set_lookup_key_value: Callable[[DriverPointer, c_char_p, c_char_p], int] = (
            lib.ls_option_auth_set_lookup_key_value
        )
        lib.ls_option_auth_set_lookup_key_value.argtypes = [
            DriverPointer,
            c_char_p,
            c_char_p,
        ]
        lib.ls_option_auth_set_lookup_key_value.restype = c_uint8

        self._set_force_in_session_auth: Callable[[DriverPointer], int] = (
            lib.ls_option_auth_force_in_session_auth
        )
        lib.ls_option_auth_force_in_session_auth.argtypes = [
            DriverPointer,
        ]
        lib.ls_option_auth_force_in_session_auth.restype = c_uint8

        self._set_bypass_in_session_auth: Callable[[DriverPointer], int] = (
            lib.ls_option_auth_bypass_in_session_auth
        )
        lib.ls_option_auth_bypass_in_session_auth.argtypes = [
            DriverPointer,
        ]
        lib.ls_option_auth_bypass_in_session_auth.restype = c_uint8

        self._set_username_pattern: Callable[[DriverPointer, c_char_p], int] = (
            lib.ls_option_auth_username_pattern
        )
        lib.ls_option_auth_username_pattern.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_auth_username_pattern.restype = c_uint8

        self._set_password_pattern: Callable[[DriverPointer, c_char_p], int] = (
            lib.ls_option_auth_password_pattern
        )
        lib.ls_option_auth_password_pattern.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_auth_password_pattern.restype = c_uint8

        self._set_private_key_passphrase_pattern: Callable[[DriverPointer, c_char_p], int] = (
            lib.ls_option_auth_private_key_passphrase_pattern
        )
        lib.ls_option_auth_private_key_passphrase_pattern.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_auth_private_key_passphrase_pattern.restype = c_uint8

    def set_username(self, ptr: DriverPointer, username: c_char_p) -> int:
        """
        Set the username.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            username: username string

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_username(ptr, username)

    def set_password(self, ptr: DriverPointer, password: c_char_p) -> int:
        """
        Set the password.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            password: password string

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_password(ptr, password)

    def set_private_key_path(self, ptr: DriverPointer, private_key_path: c_char_p) -> int:
        """
        Set the private key path.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            private_key_path: private key path string

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_private_key_path(ptr, private_key_path)

    def set_private_key_passphrase(
        self, ptr: DriverPointer, private_key_passphrase: c_char_p
    ) -> int:
        """
        Set the private key passphrase.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            private_key_passphrase: private key passphrase string

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_private_key_passphrase(ptr, private_key_passphrase)

    def set_lookup_key_value(
        self,
        ptr: DriverPointer,
        key: c_char_p,
        value: c_char_p,
    ) -> int:
        """
        Set a lookup key/value pair.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            key: the name of the key
            value: the value of the key

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_lookup_key_value(ptr, key, value)

    def set_force_in_session_auth(
        self,
        ptr: DriverPointer,
    ) -> int:
        """
        Force in session auth.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_force_in_session_auth(
            ptr,
        )

    def set_bypass_in_session_auth(
        self,
        ptr: DriverPointer,
    ) -> int:
        """
        Enable the in session auth bypass.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_bypass_in_session_auth(
            ptr,
        )

    def set_username_pattern(self, ptr: DriverPointer, pattern: c_char_p) -> int:
        """
        Set the username pattern.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            pattern: username pattern string

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_username_pattern(ptr, pattern)

    def set_password_pattern(self, ptr: DriverPointer, pattern: c_char_p) -> int:
        """
        Set the password pattern.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            pattern: password pattern string

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_password_pattern(ptr, pattern)

    def set_private_key_passphrase_pattern(self, ptr: DriverPointer, pattern: c_char_p) -> int:
        """
        Set the private key passphrase pattern.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            pattern: private key passphrase pattern string

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_private_key_passphrase_pattern(ptr, pattern)


class LibScrapliTransportBinOptionsMapping:
    """
    Mapping to libscrapli bin (default) transport option setter exported functions.

    Should not be used/called directly.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(self, lib: CDLL) -> None:
        self._set_bin: Callable[[DriverPointer, c_char_p], int] = lib.ls_option_transport_bin_bin
        lib.ls_option_transport_bin_bin.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_transport_bin_bin.restype = c_uint8

        self._set_extra_open_args: Callable[[DriverPointer, c_char_p], int] = (
            lib.ls_option_transport_bin_extra_open_args
        )
        lib.ls_option_transport_bin_extra_open_args.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_transport_bin_extra_open_args.restype = c_uint8

        self._set_override_open_args: Callable[[DriverPointer, c_char_p], int] = (
            lib.ls_option_transport_bin_override_open_args
        )
        lib.ls_option_transport_bin_override_open_args.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_transport_bin_override_open_args.restype = c_uint8

        self._set_ssh_config_path: Callable[[DriverPointer, c_char_p], int] = (
            lib.ls_option_transport_bin_ssh_config_path
        )
        lib.ls_option_transport_bin_ssh_config_path.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_transport_bin_ssh_config_path.restype = c_uint8

        self._set_known_hosts_path: Callable[[DriverPointer, c_char_p], int] = (
            lib.ls_option_transport_bin_known_hosts_path
        )
        lib.ls_option_transport_bin_known_hosts_path.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_transport_bin_known_hosts_path.restype = c_uint8

        self._set_enable_strict_key: Callable[[DriverPointer], int] = (
            lib.ls_option_transport_bin_enable_strict_key
        )
        lib.ls_option_transport_bin_enable_strict_key.argtypes = [
            DriverPointer,
        ]
        lib.ls_option_transport_bin_enable_strict_key.restype = c_uint8

        self._set_term_height: Callable[[DriverPointer, c_int], int] = (
            lib.ls_option_transport_bin_term_height
        )
        lib.ls_option_transport_bin_term_height.argtypes = [
            DriverPointer,
            c_int,
        ]
        lib.ls_option_transport_bin_term_height.restype = c_uint8

        self._set_term_width: Callable[[DriverPointer, c_int], int] = (
            lib.ls_option_transport_bin_term_width
        )
        lib.ls_option_transport_bin_term_width.argtypes = [
            DriverPointer,
            c_int,
        ]
        lib.ls_option_transport_bin_term_width.restype = c_uint8

    def set_bin(self, ptr: DriverPointer, bin_: c_char_p) -> int:
        """
        Set bin transport binary file to exec.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            bin_: path to the bin to use

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_bin(ptr, bin_)

    def set_extra_open_args(
        self,
        ptr: DriverPointer,
        extra_open_args: c_char_p,
    ) -> int:
        """
        Set bin transport extra open args.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            extra_open_args: extra open args

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_extra_open_args(
            ptr,
            extra_open_args,
        )

    def set_override_open_args(
        self,
        ptr: DriverPointer,
        override_open_args: c_char_p,
    ) -> int:
        """
        Set bin transport extra open args.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            override_open_args: override open args

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_override_open_args(
            ptr,
            override_open_args,
        )

    def set_ssh_config_path(self, ptr: DriverPointer, path: c_char_p) -> int:
        """
        Set bin transport ssh config file path.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            path: the path to the ssh config file

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_ssh_config_path(ptr, path)

    def set_known_hosts_path(self, ptr: DriverPointer, path: c_char_p) -> int:
        """
        Set bin transport known hosts file path.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            path: the path to the known hosts file

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_known_hosts_path(ptr, path)

    def set_enable_strict_key(
        self,
        ptr: DriverPointer,
    ) -> int:
        """
        Set bin transport strict key checking

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_enable_strict_key(
            ptr,
        )

    def set_term_height(self, ptr: DriverPointer, height: c_int) -> int:
        """
        Set bin transport terminal height

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            height: size of terminal height

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_term_height(ptr, height)

    def set_term_width(self, ptr: DriverPointer, width: c_int) -> int:
        """
        Set bin transport terminal width

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            width: size of terminal width

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_term_width(ptr, width)


class LibScrapliTransportSsh2OptionsMapping:
    """
    Mapping to libscrapli ssh2 transport option setter exported functions.

    Should not be used/called directly.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(self, lib: CDLL) -> None:
        self._set_known_hosts_path: Callable[[DriverPointer, c_char_p], int] = (
            lib.ls_option_transport_ssh2_known_hosts_path
        )
        lib.ls_option_transport_ssh2_known_hosts_path.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_transport_ssh2_known_hosts_path.restype = c_uint8

        self._set_libssh2_trace: Callable[[DriverPointer], int] = (
            lib.ls_option_transport_ssh2_libssh2trace
        )
        lib.ls_option_transport_ssh2_libssh2trace.argtypes = [
            DriverPointer,
        ]
        lib.ls_option_transport_ssh2_libssh2trace.restype = c_uint8

    def set_known_hosts_path(self, ptr: DriverPointer, path: c_char_p) -> int:
        """
        Set ssh2 transport known hosts file path.

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            path: the path to the known hosts file

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_known_hosts_path(ptr, path)

    def set_libssh2_trace(self, ptr: DriverPointer) -> int:
        """
        Set ssh2 transport libssh2 trace

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_libssh2_trace(ptr)


class LibScrapliTransportTelnetOptionsMapping:
    """
    Mapping to libscrapli telnet transport option setter exported functions.

    Should not be used/called directly.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(self, lib: CDLL) -> None:
        _ = lib


class LibScrapliTransportTestOptionsMapping:
    """
    Mapping to libscrapli test transport option setter exported functions.

    Should not be used/called directly.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(self, lib: CDLL) -> None:
        self._set_f: Callable[[DriverPointer, c_char_p], int] = lib.ls_option_transport_test_f
        lib.ls_option_transport_test_f.argtypes = [
            DriverPointer,
            c_char_p,
        ]
        lib.ls_option_transport_test_f.restype = c_int

    def set_f(self, ptr: DriverPointer, f: c_char_p) -> int:
        """
        Set test transport f

        Should not be used/called directly.

        Args:
            ptr: ptr to the cli/netconf object
            f: file to read/load

        Returns:
            int: return code, non-zero value indicates an error. technically a c_uint8 converted by
                ctypes.

        Raises:
            N/A

        """
        return self._set_f(ptr, f)


class LibScrapliOptionsMapping:
    """
    Mapping to libscrapli option setter exported functions.

    Should not be used/called directly.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(self, lib: CDLL) -> None:
        self.netconf = LibScrapliNetconfOptionsMapping(lib)
        self.session = LibScrapliSessionOptionsMapping(lib)
        self.auth = LibScrapliAuthOptionsMapping(lib)
        self.transport_bin = LibScrapliTransportBinOptionsMapping(lib)
        self.transport_ssh2 = LibScrapliTransportSsh2OptionsMapping(lib)
        self.transport_telnet = LibScrapliTransportTelnetOptionsMapping(lib)
        self.transport_test = LibScrapliTransportTestOptionsMapping(lib)
