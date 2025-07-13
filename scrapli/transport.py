"""scrapli.transport"""

from abc import ABC, abstractmethod
from ctypes import c_char_p, c_int
from dataclasses import dataclass, field
from enum import Enum

from scrapli.exceptions import OptionsException
from scrapli.ffi_mapping import LibScrapliMapping
from scrapli.ffi_types import (
    DriverPointer,
    to_c_string,
)


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

    def apply(  # noqa: C901, PLR0912
        self, ffi_mapping: LibScrapliMapping, ptr: DriverPointer
    ) -> None:
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
        if self.bin is not None:
            self._bin = to_c_string(self.bin)

            status = ffi_mapping.options_mapping.transport_bin.set_bin(ptr, self._bin)
            if status != 0:
                raise OptionsException("failed to set bin transport bin")

        if self.extra_open_args is not None:
            self._extra_open_args = to_c_string(" ".join(self.extra_open_args))

            status = ffi_mapping.options_mapping.transport_bin.set_extra_open_args(
                ptr, self._extra_open_args
            )
            if status != 0:
                raise OptionsException("failed to set bin transport extra open args")

        if self.override_open_args is not None:
            self._override_open_args = to_c_string(" ".join(self.override_open_args))

            status = ffi_mapping.options_mapping.transport_bin.set_override_open_args(
                ptr, self._override_open_args
            )
            if status != 0:
                raise OptionsException("failed to set bin transport override open args")

        if self.ssh_config_path is not None:
            self._ssh_config_path = to_c_string(self.ssh_config_path)

            status = ffi_mapping.options_mapping.transport_bin.set_ssh_config_path(
                ptr, self._ssh_config_path
            )
            if status != 0:
                raise OptionsException("failed to set bin transport ssh config path")

        if self.known_hosts_path is not None:
            self._known_hosts_path = to_c_string(self.known_hosts_path)

            status = ffi_mapping.options_mapping.transport_bin.set_known_hosts_path(
                ptr, self._known_hosts_path
            )
            if status != 0:
                raise OptionsException("failed to set bin transport ssh known hosts path")

        if self.enable_strict_key is not None:
            status = ffi_mapping.options_mapping.transport_bin.set_enable_strict_key(ptr)
            if status != 0:
                raise OptionsException("failed to set bin transport enable strict key")

        if self.term_height is not None:
            status = ffi_mapping.options_mapping.transport_bin.set_term_height(
                ptr, c_int(self.term_height)
            )
            if status != 0:
                raise OptionsException("failed to set bin transport term height")

        if self.term_width is not None:
            status = ffi_mapping.options_mapping.transport_bin.set_term_width(
                ptr, c_int(self.term_width)
            )
            if status != 0:
                raise OptionsException("failed to set bin transport term width")


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

    def apply(  # noqa: C901,PLR0912
        self, ffi_mapping: LibScrapliMapping, ptr: DriverPointer
    ) -> None:
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
        if self.known_hosts_path is not None:
            status = ffi_mapping.options_mapping.transport_ssh2.set_known_hosts_path(
                ptr,
                to_c_string(self.known_hosts_path),
            )
            if status != 0:
                raise OptionsException("failed to set ssh2 transport known hosts path")

        if self.libssh2_trace is not None:
            status = ffi_mapping.options_mapping.transport_ssh2.set_libssh2_trace(ptr)
            if status != 0:
                raise OptionsException("failed to set ssh2 transport trace")

        if self.proxy_jump_host is not None:
            status = ffi_mapping.options_mapping.transport_ssh2.set_proxy_jump_host(
                ptr,
                to_c_string(self.proxy_jump_host),
            )
            if status != 0:
                raise OptionsException("failed to set ssh2 transport proxy jump host")
        else:
            # if the proxy jump host is None no reason to check anything else, also the host
            # *must* be applied first since we will check .? on the proxy jump object in the
            # ffi option apply in zig, so we will crash if the host isnt set and something else
            # is attempted to be set!
            return

        if self.proxy_jump_port is not None:
            status = ffi_mapping.options_mapping.transport_ssh2.set_proxy_jump_port(
                ptr,
                c_int(self.proxy_jump_port),
            )
            if status != 0:
                raise OptionsException("failed to set ssh2 transport proxy jump port")

        if self.proxy_jump_username is not None:
            status = ffi_mapping.options_mapping.transport_ssh2.set_proxy_jump_username(
                ptr,
                to_c_string(self.proxy_jump_username),
            )
            if status != 0:
                raise OptionsException("failed to set ssh2 transport proxy jump username")

        if self.proxy_jump_password is not None:
            status = ffi_mapping.options_mapping.transport_ssh2.set_proxy_jump_password(
                ptr,
                to_c_string(self.proxy_jump_password),
            )
            if status != 0:
                raise OptionsException("failed to set ssh2 transport proxy jump password")

        if self.proxy_jump_private_key_path is not None:
            status = ffi_mapping.options_mapping.transport_ssh2.set_proxy_jump_private_key_path(
                ptr,
                to_c_string(self.proxy_jump_private_key_path),
            )
            if status != 0:
                raise OptionsException("failed to set ssh2 transport proxy jump private key path")

        if self.proxy_jump_private_key_passphrase is not None:
            status = (
                ffi_mapping.options_mapping.transport_ssh2.set_proxy_jump_private_key_passphrase(
                    ptr,
                    to_c_string(self.proxy_jump_private_key_passphrase),
                )
            )
            if status != 0:
                raise OptionsException(
                    "failed to set ssh2 transport proxy jump private key passphrase"
                )

        if self.proxy_jump_libssh2_trace is not None:
            status = ffi_mapping.options_mapping.transport_ssh2.set_proxy_jump_libssh2_trace(ptr)
            if status != 0:
                raise OptionsException("failed to set ssh2 transport proxy jump trace")


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
        _, _ = ffi_mapping, ptr


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
        if self.f is not None:
            self._f = to_c_string(self.f)

            status = ffi_mapping.options_mapping.transport_test.set_f(ptr, self._f)
            if status != 0:
                raise OptionsException("failed to set test transport f")
