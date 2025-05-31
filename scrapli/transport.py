"""scrapli.transport"""

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


@dataclass
class BinOptions:
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
class Ssh2Options:
    """
    Options holds ssh2 transport options to pass to the ffi layer.

    Args:
        libssh2_trace: enable libssh2 tracing

    Returns:
        None

    Raises:
        N/A

    """

    libssh2_trace: bool | None = None

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
        if self.libssh2_trace is not None:
            status = ffi_mapping.options_mapping.transport_ssh2.set_libssh2_trace(ptr)
            if status != 0:
                raise OptionsException("failed to set ssh2 transport trace")


@dataclass
class TelnetOptions:
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
class TestOptions:
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


@dataclass
class Options:
    """
    Options holds transport options to pass to the ffi layer.

    Only one flavor of transport options can be set at a time. The active option determines the
    transport to be used for the connection.

    Args:
        bin: the bin transport options
        ssh2: the ssh2 transport options
        telnet: the telnet transport options
        test: the test transport options

    Returns:
        None

    Raises:
        N/A

    """

    bin: BinOptions | None = None
    ssh2: Ssh2Options | None = None
    telnet: TelnetOptions | None = None
    test: TestOptions | None = None

    _transport_kind: bytes | None = field(init=False, default=None, repr=False)

    def __post_init__(self) -> None:
        _set_fields = [f for f in [self.bin, self.ssh2, self.telnet, self.test] if f is not None]

        if len(_set_fields) == 0:
            self.bin = BinOptions()

            return

        if len(_set_fields) == 1:
            return

        raise OptionsException("more than one transport set")

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
        if self.bin:
            self.bin.apply(ffi_mapping, ptr)
        elif self.ssh2:
            self.ssh2.apply(ffi_mapping, ptr)
        elif self.telnet:
            self.telnet.apply(ffi_mapping, ptr)
        elif self.test:
            self.test.apply(ffi_mapping, ptr)

    def get_transport_kind(self) -> bytes:
        """
        Returns the encoded name of the selected transport kind

        Should not be called directly/by users.

        Args:
            N/A

        Returns:
            bytes: the encoded name of the selected transport kind

        Raises:
            OptionsException: if any option apply returns a non-zero return code.

        """
        if self.bin:
            self._transport_kind = TransportKind.BIN.encode(encoding="utf-8")
        elif self.ssh2:
            self._transport_kind = TransportKind.SSH2.encode(encoding="utf-8")
        elif self.telnet:
            self._transport_kind = TransportKind.TELNET.encode(encoding="utf-8")
        else:
            self._transport_kind = TransportKind.TEST.encode(encoding="utf-8")

        return self._transport_kind

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
        if self.bin:
            return (
                # it will probably be "canonical" to import Options as SessionOptions, so we'll make
                # the repr do that too
                f"Transport{self.__class__.__name__}("
                f"bin={self.bin!r}, "
            )

        if self.ssh2:
            return f"Transport{self.__class__.__name__}(" f"ssh2={self.ssh2!r}, "

        if self.telnet:
            return f"Transport{self.__class__.__name__}(" f"telnet={self.telnet!r}, "

        return f"Transport{self.__class__.__name__}(" f"test={self.test!r}, "
