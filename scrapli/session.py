"""scrapli.session"""

from ctypes import c_char_p, c_int
from dataclasses import dataclass, field
from typing import Optional

from scrapli.exceptions import OptionsException
from scrapli.ffi_mapping import LibScrapliMapping
from scrapli.ffi_types import DriverPointer, to_c_string


@dataclass
class Options:  # pylint: disable=too-many-instance-attributes
    """
    Options holds session related options to pass to the ffi layer.

    Args:
        read_size: read size
        read_delay_min_ns: minimum read delay in ns
        read_delay_max_ns: maximum read delay in ns
        read_delay_backoff_factor: read delay backoff factor
        return_char: return char
        operation_timeout_ns: operation timeout in ns
        operation_max_search_depth: operation maximum search depth
        recorder_path: path for session recorder output to write to

    Returns:
        None

    Raises:
        N/A

    """

    read_size: Optional[int] = None
    read_delay_min_ns: Optional[int] = None
    read_delay_max_ns: Optional[int] = None
    read_delay_backoff_factor: Optional[int] = None
    return_char: Optional[str] = None
    operation_timeout_ns: Optional[int] = None
    operation_max_search_depth: Optional[int] = None
    recorder_path: Optional[str] = None

    _return_char: Optional[c_char_p] = field(init=False, default=None, repr=False)
    _recorder_path: Optional[c_char_p] = field(init=False, default=None, repr=False)

    def apply(  # pylint: disable=too-many-branches
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
        if self.read_size is not None:
            status = ffi_mapping.options_mapping.session.set_read_size(ptr, c_int(self.read_size))
            if status != 0:
                raise OptionsException("failed to set session read size")

        if self.read_delay_min_ns is not None:
            status = ffi_mapping.options_mapping.session.set_read_delay_min_ns(
                ptr, c_int(self.read_delay_min_ns)
            )
            if status != 0:
                raise OptionsException("failed to set session read delay min")

        if self.read_delay_max_ns is not None:
            status = ffi_mapping.options_mapping.session.set_read_delay_max_ns(
                ptr, c_int(self.read_delay_max_ns)
            )
            if status != 0:
                raise OptionsException("failed to set session read delay max")

        if self.read_delay_backoff_factor is not None:
            status = ffi_mapping.options_mapping.session.set_read_delay_backoff_factor(
                ptr, c_int(self.read_delay_backoff_factor)
            )
            if status != 0:
                raise OptionsException("failed to set session read delay backoff factor")

        if self.return_char is not None:
            self._return_char = to_c_string(self.return_char)

            status = ffi_mapping.options_mapping.session.set_return_char(ptr, self._return_char)
            if status != 0:
                raise OptionsException("failed to set session return char")

        if self.operation_timeout_ns is not None:
            status = ffi_mapping.options_mapping.session.set_operation_timeout_ns(
                ptr, c_int(self.operation_timeout_ns)
            )
            if status != 0:
                raise OptionsException("failed to set session operation timeout")

        if self.operation_max_search_depth is not None:
            status = ffi_mapping.options_mapping.session.set_operation_max_search_depth(
                ptr, c_int(self.operation_max_search_depth)
            )
            if status != 0:
                raise OptionsException("failed to set session operation max search depth")

        if self.recorder_path is not None:
            self._recorder_path = to_c_string(self.recorder_path)

            status = ffi_mapping.options_mapping.session.set_recorder_path(ptr, self._recorder_path)
            if status != 0:
                raise OptionsException("failed to set session recorder path")
