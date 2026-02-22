"""scrapli.ffi_options"""

from ctypes import POINTER, Structure, _Pointer, c_char_p, c_size_t, c_uint16, pointer
from typing import TYPE_CHECKING, Any, ClassVar, TypeAlias

from scrapli.exceptions import OptionsException
from scrapli.ffi_types import (
    BoolPointer,
    LoggerCallback,
    LoggerCallbackC,
    NetconfCapabilitesCallbackC,
    RecorderCallbackC,
    StringPointer,
    U16Pointer,
    U64Pointer,
)

if TYPE_CHECKING:
    DriverOptionsPointer: TypeAlias = _Pointer["DriverOptions"]
else:
    DriverOptionsPointer: TypeAlias = POINTER("DriverOptions")


class CLI(Structure):
    """
    The cli section of the driver options struct.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    _fields_: ClassVar[list[tuple[str, Any]]] = [
        ("definition_str", c_char_p),
        ("definition_str_len", c_size_t),
    ]


class Netconf(Structure):
    """
    The netconf section of the driver options struct.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    _fields_: ClassVar[list[tuple[str, Any]]] = [
        ("error_tag", c_char_p),
        ("error_tag_len", c_size_t),
        ("preferred_version", c_char_p),
        ("preferred_version_len", c_size_t),
        ("message_poll_interval", U64Pointer),
        ("capabilities_callback", NetconfCapabilitesCallbackC),
    ]


class Session(Structure):
    """
    The session section of the driver options struct.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    _fields_: ClassVar[list[tuple[str, Any]]] = [
        ("read_size", U64Pointer),
        ("read_min_delay_ns", U64Pointer),
        ("read_max_delay_ns", U64Pointer),
        ("return_char", c_char_p),
        ("return_char_len", c_size_t),
        ("operation_timeout_ns", U64Pointer),
        ("operation_max_search_depth", U64Pointer),
        ("record_destination", c_char_p),
        ("record_destination_len", c_size_t),
        ("record_callback", RecorderCallbackC),
    ]


class AuthLookups(Structure):
    """
    The auth lookups section of the driver options struct.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    _fields_: ClassVar[list[tuple[str, Any]]] = [
        ("keys", StringPointer),
        ("key_lens", U16Pointer),
        ("vals", StringPointer),
        ("val_lens", U16Pointer),
        ("count", c_size_t),
    ]


class Auth(Structure):
    """
    The auth section of the driver options struct.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    _fields_: ClassVar[list[tuple[str, Any]]] = [
        ("username", c_char_p),
        ("username_len", c_size_t),
        ("password", c_char_p),
        ("password_len", c_size_t),
        ("private_key_path", c_char_p),
        ("private_key_path_len", c_size_t),
        ("private_key_passphrase", c_char_p),
        ("private_key_passphrase_len", c_size_t),
        ("lookups", AuthLookups),
        ("force_in_session_auth", BoolPointer),
        ("bypass_in_session_auth", BoolPointer),
        ("username_pattern", c_char_p),
        ("username_pattern_len", c_size_t),
        ("password_pattern", c_char_p),
        ("password_pattern_len", c_size_t),
        ("private_key_passphrase_pattern", c_char_p),
        ("private_key_passphrase_pattern_len", c_size_t),
    ]


class TransportBin(Structure):
    """
    The bin transport section of the driver options struct.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    _fields_: ClassVar[list[tuple[str, Any]]] = [
        ("bin", c_char_p),
        ("bin_len", c_size_t),
        ("extra_open_args", c_char_p),
        ("extra_open_args_len", c_size_t),
        ("override_open_args", c_char_p),
        ("override_open_args_len", c_size_t),
        ("ssh_config_path", c_char_p),
        ("ssh_config_path_len", c_size_t),
        ("known_hosts_path", c_char_p),
        ("known_hosts_path_len", c_size_t),
        ("enable_strict_key", BoolPointer),
        ("term_height", U16Pointer),
        ("term_width", U16Pointer),
    ]


class TransportSSH2(Structure):
    """
    The ssh2 transport section of the driver options struct.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    _fields_: ClassVar[list[tuple[str, Any]]] = [
        ("known_hosts_path", c_char_p),
        ("known_hosts_path_len", c_size_t),
        ("libssh2trace", BoolPointer),
        ("proxy_jump_host", c_char_p),
        ("proxy_jump_host_len", c_size_t),
        ("proxy_jump_port", U16Pointer),
        ("proxy_jump_username", c_char_p),
        ("proxy_jump_username_len", c_size_t),
        ("proxy_jump_password", c_char_p),
        ("proxy_jump_password_len", c_size_t),
        ("proxy_jump_private_key_path", c_char_p),
        ("proxy_jump_private_key_path_len", c_size_t),
        ("proxy_jump_private_key_passphrase", c_char_p),
        ("proxy_jump_private_key_passphrase_len", c_size_t),
        ("proxy_jump_libssh2trace", BoolPointer),
    ]


class TransportTest(Structure):
    """
    The test transport section of the driver options struct.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    _fields_: ClassVar[list[tuple[str, Any]]] = [
        ("f", c_char_p),
        ("f_len", c_size_t),
    ]


class Transport(Structure):
    """
    The transport section of the driver options struct.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    _fields_: ClassVar[list[tuple[str, Any]]] = [
        ("bin", TransportBin),
        ("ssh2", TransportSSH2),
        ("test", TransportTest),
    ]


class DriverOptions(Structure):
    """
    The driver options struct.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    _fields_: ClassVar[list[tuple[str, Any]]] = [
        ("logger_callback", LoggerCallbackC),
        ("logger_level", c_char_p),
        ("logger_level_len", c_size_t),
        ("port", U16Pointer),
        ("transport_kind", c_char_p),
        ("transport_kind_len", c_size_t),
        ("cli", CLI),
        ("netconf", Netconf),
        ("session", Session),
        ("auth", Auth),
        ("transport", Transport),
    ]

    def apply(
        self,
        *,
        logger_callback: LoggerCallback,
        logger_level: c_char_p,
        port: int,
        transport_kind: c_char_p,
        cli_definition_string: c_char_p | None = None,
    ) -> None:
        """
        Applies the top-level options.

        Args:
            logger_callback: the wrapped logger callback to pass to zig things
            logger_level: the level to pass to the zig logger
            port: the port as set in the cli/netconf object, None is acceptable as the zig bits will
                handle picking default port
            transport_kind: enum value to be mapped to c-string and passed to zig
            cli_definition_string: only applicable to cli objects, bytes of the loaded definition

        Returns:
            None

        Raises:
            OptionsException: if any of the c types values are None

        """
        if not logger_level.value:
            raise OptionsException("logger level value is None, this is a bug")

        if not transport_kind.value:
            raise OptionsException("transport kind value is None, this is a bug")

        self.logger_callback = logger_callback
        self.logger_level = logger_level
        self.logger_level_len = c_size_t(len(logger_level.value))

        self.port = pointer(c_uint16(port))

        self.transport_kind = transport_kind
        self.transport_kind_len = c_size_t(len(transport_kind.value))

        if cli_definition_string:
            if not cli_definition_string.value:
                raise OptionsException("cli defintion value is None, this is a bug")

            self.cli.definition_str = cli_definition_string
            self.cli.definition_str_len = c_size_t(len(cli_definition_string.value))
