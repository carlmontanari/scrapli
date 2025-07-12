"""scrapli.session"""

from ctypes import c_char_p, c_uint64
from dataclasses import dataclass, field

from scrapli.exceptions import OptionsException
from scrapli.ffi_mapping import LibScrapliMapping
from scrapli.ffi_types import DriverPointer, to_c_string


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
                self.operation_timeout_ns = int(self.operation_timeout_s / 1e-9)

    def apply(self, ffi_mapping: LibScrapliMapping, ptr: DriverPointer) -> None:  # noqa: C901
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
        if self.read_size is not None:
            status = ffi_mapping.options_mapping.session.set_read_size(
                ptr, c_uint64(self.read_size)
            )
            if status != 0:
                raise OptionsException("failed to set session read size")

        if self.return_char is not None:
            self._return_char = to_c_string(self.return_char)

            status = ffi_mapping.options_mapping.session.set_return_char(ptr, self._return_char)
            if status != 0:
                raise OptionsException("failed to set session return char")

        if self.operation_timeout_ns is not None:
            status = ffi_mapping.options_mapping.session.set_operation_timeout_ns(
                ptr, c_uint64(self.operation_timeout_ns)
            )
            if status != 0:
                raise OptionsException("failed to set session operation timeout")

        if self.operation_max_search_depth is not None:
            status = ffi_mapping.options_mapping.session.set_operation_max_search_depth(
                ptr, c_uint64(self.operation_max_search_depth)
            )
            if status != 0:
                raise OptionsException("failed to set session operation max search depth")

        if self.recorder_path is not None:
            self._recorder_path = to_c_string(self.recorder_path)

            status = ffi_mapping.options_mapping.session.set_recorder_path(ptr, self._recorder_path)
            if status != 0:
                raise OptionsException("failed to set session recorder path")

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
