"""scrapli.transport"""

from abc import ABC, abstractmethod
from ctypes import c_bool, c_char_p, c_size_t, pointer
from dataclasses import dataclass, field
from enum import Enum

from scrapli.ffi_options import DriverOptionsPointer
from scrapli.ffi_types import to_c_string


class TransportKind(str, Enum):
    """
    Enum representing the transport kind

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    BIN = "bin"
    SSH2 = "ssh2"
    TELNET = "telnet"
    TEST = "test_"


class Options(ABC):
    """
    Options is the base class for transport related option containers.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    _transport_kind: TransportKind | None = None

    @property
    def transport_kind(self) -> TransportKind:
        """
        Returns/sets the encoded name of the selected transport kind

        Should not be called directly/by users.

        Args:
            N/A

        Returns:
            TransportKind: the selected transport kind

        Raises:
            OptionsException: if any option apply returns a non-zero return code.

        """
        if isinstance(self, BinOptions):
            self._transport_kind = TransportKind.BIN
        elif isinstance(self, Ssh2Options):
            self._transport_kind = TransportKind.SSH2
        elif isinstance(self, TelnetOptions):
            self._transport_kind = TransportKind.TELNET
        else:
            self._transport_kind = TransportKind.TEST

        return self._transport_kind

    @abstractmethod
    def apply(self, *, options: DriverOptionsPointer) -> None:
        """
        Applies the options to the given options struct.

        Should not be called directly/by users.

        Args:
            options: the options struct to write set options to

        Returns:
            None

        Raises:
            N/A

        """
        raise NotImplementedError


@dataclass
class BinOptions(Options):
    """
    Options holds bin transport options to pass to the ffi layer.

    Args:
        bin: path to binary to use for the transport
        extra_open_args: extra args to pass to the binary
        override_open_args: override all "normal" scrapli args with these args
        ssh_config_path: path to ssh config file
        known_hosts_path: path to known hosts file
        enable_strict_key: enable ssh strict key checking
        term_height: set the terminal height
        term_width: set the terminal width

    Returns:
        None

    Raises:
        N/A

    """

    bin: str | None = None
    extra_open_args: list[str] | None = None
    override_open_args: list[str] | None = None
    ssh_config_path: str | None = None
    known_hosts_path: str | None = None
    enable_strict_key: bool | None = None
    term_height: int | None = None
    term_width: int | None = None

    _bin: c_char_p | None = field(init=False, default=None, repr=False)
    _extra_open_args: c_char_p | None = field(init=False, default=None, repr=False)
    _override_open_args: c_char_p | None = field(init=False, default=None, repr=False)
    _ssh_config_path: c_char_p | None = field(init=False, default=None, repr=False)
    _known_hosts_path: c_char_p | None = field(init=False, default=None, repr=False)

    def apply(self, *, options: DriverOptionsPointer) -> None:
        """
        Applies the options to the given options struct.

        Should not be called directly/by users.

        Args:
            options: the options struct to write set options to

        Returns:
            None

        Raises:
            N/A

        """
        if self.bin is not None:
            self._bin = to_c_string(self.bin)

            options.contents.transport.bin.bin = self._bin
            options.contents.transport.bin.bin_len = c_size_t(len(self.bin))

        if self.extra_open_args is not None:
            self._extra_open_args = to_c_string(" ".join(self.extra_open_args))

            options.contents.transport.bin.extra_open_args = self._extra_open_args
            options.contents.transport.bin.extra_open_args_len = c_size_t(len(self.extra_open_args))

        if self.override_open_args is not None:
            self._override_open_args = to_c_string(" ".join(self.override_open_args))

            options.contents.transport.bin.override_open_args = self._override_open_args
            options.contents.transport.bin.override_open_args_len = c_size_t(
                len(self.override_open_args)
            )

        if self.ssh_config_path is not None:
            self._ssh_config_path = to_c_string(self.ssh_config_path)

            options.contents.transport.bin.ssh_config_path = self._ssh_config_path
            options.contents.transport.bin.ssh_config_path_len = c_size_t(len(self.ssh_config_path))

        if self.known_hosts_path is not None:
            self._known_hosts_path = to_c_string(self.known_hosts_path)

            options.contents.transport.bin.known_hosts_path = self._known_hosts_path
            options.contents.transport.bin.known_hosts_path_len = c_size_t(
                len(self.known_hosts_path)
            )

        if self.enable_strict_key is not None:
            options.contents.transport.bin.enable_strict_key = pointer(
                c_bool(self.enable_strict_key)
            )

        if self.term_height is not None:
            options.contents.transport.bin.term_height = pointer(self.term_height)

        if self.term_width is not None:
            options.contents.transport.bin.term_width = pointer(self.term_width)


@dataclass
class Ssh2Options(Options):
    """
    Options holds ssh2 transport options to pass to the ffi layer.

    Args:
        known_hosts_path: path to known hosts file
        libssh2_trace: enable libssh2 tracing
        proxy_jump_host: the end target host to proxy jump to
        proxy_jump_port: port of the end target host to proxy jump to
        proxy_jump_username: username for auth to end proxy jump host
        proxy_jump_password: password for auth to end proxy jump host
        proxy_jump_private_key_path: private key path for auth to end proxy jump host
        proxy_jump_private_key_passphrase: private key passphrase for auth to end proxy jump host
        proxy_jump_libssh2_trace: enable libssh2 tracing for the "inner" proxy jump session

    Returns:
        None

    Raises:
        N/A

    """

    known_hosts_path: str | None = None
    libssh2_trace: bool | None = None

    proxy_jump_host: str | None = None
    proxy_jump_port: int | None = None
    proxy_jump_username: str | None = None
    proxy_jump_password: str | None = None
    proxy_jump_private_key_path: str | None = None
    proxy_jump_private_key_passphrase: str | None = None
    proxy_jump_libssh2_trace: bool | None = None

    _known_hosts_path: c_char_p | None = field(init=False, default=None, repr=False)
    _proxy_jump_host: c_char_p | None = field(init=False, default=None, repr=False)
    _proxy_jump_username: c_char_p | None = field(init=False, default=None, repr=False)
    _proxy_jump_password: c_char_p | None = field(init=False, default=None, repr=False)
    _proxy_jump_private_key_path: c_char_p | None = field(init=False, default=None, repr=False)
    _proxy_jump_private_key_passphrase: c_char_p | None = field(
        init=False, default=None, repr=False
    )

    def apply(self, *, options: DriverOptionsPointer) -> None:
        """
        Applies the options to the given options struct.

        Should not be called directly/by users.

        Args:
            options: the options struct to write set options to

        Returns:
            None

        Raises:
            N/A

        """
        if self.known_hosts_path is not None:
            self._known_hosts_path = to_c_string(self.known_hosts_path)

            options.contents.transport.ssh2.known_hosts_path = self._known_hosts_path
            options.contents.transport.ssh2.known_hosts_path_len = c_size_t(
                len(self.known_hosts_path)
            )

        if self.libssh2_trace is not None:
            options.contents.transport.ssh2.libssh2_trace = pointer(c_bool(self.libssh2_trace))

        if self.proxy_jump_host is not None:
            self._proxy_jump_host = to_c_string(self.proxy_jump_host)

            options.contents.transport.ssh2.proxy_jump_host = self._proxy_jump_host
            options.contents.transport.ssh2.proxy_jump_host_len = c_size_t(
                len(self.proxy_jump_host)
            )
        else:
            # if the proxy jump host is None no reason to check anything else, also the host
            # *must* be applied first since we will check .? on the proxy jump object in the
            # ffi option apply in zig, so we will crash if the host isnt set and something else
            # is attempted to be set!
            return

        if self.proxy_jump_port is not None:
            options.contents.transport.ssh2.proxy_jump_port = pointer(self.proxy_jump_port)

        if self.proxy_jump_username is not None:
            self._proxy_jump_username = to_c_string(self.proxy_jump_host)

            options.contents.transport.ssh2.proxy_jump_username = self._proxy_jump_username
            options.contents.transport.ssh2.proxy_jump_username_len = c_size_t(
                len(self.proxy_jump_host)
            )

        if self.proxy_jump_password is not None:
            self._proxy_jump_password = to_c_string(self.proxy_jump_host)

            options.contents.transport.ssh2.proxy_jump_password = self._proxy_jump_password
            options.contents.transport.ssh2.proxy_jump_password_len = c_size_t(
                len(self.proxy_jump_password)
            )

        if self.proxy_jump_private_key_path is not None:
            self._proxy_jump_private_key_path = to_c_string(self.proxy_jump_private_key_path)

            options.contents.transport.ssh2.proxy_jump_private_key_path = (
                self._proxy_jump_private_key_path
            )
            options.contents.transport.ssh2.proxy_jump_private_key_path_len = c_size_t(
                len(self.proxy_jump_private_key_path)
            )

        if self.proxy_jump_private_key_passphrase is not None:
            self._proxy_jump_private_key_passphrase = to_c_string(
                self.proxy_jump_private_key_passphrase
            )

            options.contents.transport.ssh2.proxy_jump_private_key_prassphrase = (
                self._proxy_jump_private_key_passphrase
            )
            options.contents.transport.ssh2.proxy_jump_private_key_prassphrase_len = c_size_t(
                len(self.proxy_jump_private_key_passphrase)
            )

        if self.proxy_jump_libssh2_trace is not None:
            options.contents.transport.ssh2.proxy_jump_libssh2_trace = pointer(
                c_bool(self.proxy_jump_libssh2_trace)
            )


@dataclass
class TelnetOptions(Options):
    """
    Options holds telnet transport options to pass to the ffi layer.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def apply(self, *, options: DriverOptionsPointer) -> None:
        """
        Applies the options to the given options struct.

        Should not be called directly/by users.

        Args:
            options: the options struct to write set options to

        Returns:
            None

        Raises:
            N/A

        """
        _ = options


@dataclass
class TestOptions(Options):
    """
    Options holds test transport options to pass to the ffi layer.

    Args:
        f: the file to load/read for the transport

    Returns:
        None

    Raises:
        N/A

    """

    f: str | None = None

    _f: c_char_p | None = field(init=False, default=None, repr=False)

    def apply(self, *, options: DriverOptionsPointer) -> None:
        """
        Applies the options to the given options struct.

        Should not be called directly/by users.

        Args:
            options: the options struct to write set options to

        Returns:
            None

        Raises:
            N/A

        """
        if self.f is not None:
            self._f = to_c_string(self.f)

            options.contents.transport.test.f = self._f
            options.contents.transport.test.f_len = c_size_t(len(self.f))
