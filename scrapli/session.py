"""scrapli.session"""

from ctypes import _Pointer, c_char_p, c_size_t, c_uint64, pointer
from dataclasses import dataclass, field

from scrapli.ffi_options import DriverOptions
from scrapli.ffi_types import to_c_string
from scrapli.helper import second_to_nano

DEFAULT_OPERATION_TIMEOUT_NS = 10_000_000_000


@dataclass
class Options:
    """
    Options holds session related options to pass to the ffi layer.

    Args:
        read_size: read size
        return_char: return char
        operation_timeout_s: operation timeout in s, ignored if operation_timeout_ns set
        operation_timeout_ns: operation timeout in ns
        operation_max_search_depth: operation maximum search depth
        recorder_path: path for session recorder output to write to

    Returns:
        None

    Raises:
        N/A

    """

    read_size: int | None = None
    read_min_delay_ns: int | None = None
    read_max_delay_ns: int | None = None
    return_char: str | None = None
    operation_timeout_s: int | None = None
    operation_timeout_ns: int | None = None
    operation_max_search_depth: int | None = None
    recorder_path: str | None = None

    _return_char: c_char_p | None = field(init=False, default=None, repr=False)
    _recorder_path: c_char_p | None = field(init=False, default=None, repr=False)

    def __post_init__(self) -> None:
        if self.operation_timeout_s is not None or self.operation_timeout_ns is not None:
            if self.operation_timeout_ns is None and self.operation_timeout_s is not None:
                self.operation_timeout_ns = second_to_nano(d=self.operation_timeout_s)

    def apply(self, *, options: _Pointer[DriverOptions]) -> None:
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
        if self.read_size is not None:
            options.contents.session.read_size = pointer(c_uint64(self.read_size))

        if self.read_min_delay_ns is not None:
            options.contents.session.read_min_delay_ns = pointer(c_uint64(self.read_min_delay_ns))

        if self.read_max_delay_ns is not None:
            options.contents.session.read_max_delay_ns = pointer(c_uint64(self.read_max_delay_ns))

        if self.return_char is not None:
            self._return_char = to_c_string(self.return_char)

            options.contents.session.return_char = self._return_char
            options.contents.session.return_char_len = c_size_t(len(self.return_char))

        if self.operation_timeout_ns is not None:
            options.contents.session.operation_timeout_ns = pointer(
                c_uint64(self.operation_timeout_ns)
            )

        if self.operation_max_search_depth is not None:
            options.contents.session.operation_max_search_depth = pointer(
                c_uint64(self.operation_max_search_depth)
            )

        if self.recorder_path is not None:
            self._recorder_path = to_c_string(self.recorder_path)

            options.contents.session.recorder_path = self._recorder_path
            options.contents.session.recorder_path_len = c_size_t(len(self.recorder_path))

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
            # it will probably be "canonical" to import Options as SessionOptions, so we'll make
            # the repr do that too
            f"Session{self.__class__.__name__}("
            f"read_size={self.read_size!r}, "
            f"return_char={self.return_char!r}) "
            f"operation_timeout_ns={self.operation_timeout_ns!r}) "
            f"operation_max_search_depth={self.operation_max_search_depth!r}) "
            f"recorder_path={self.recorder_path!r}) "
        )
