"""scrapli.ffi_types"""

from ctypes import (
    CFUNCTYPE,
    POINTER,
    Structure,
    c_bool,
    c_char_p,
    c_int,
    c_size_t,
    c_uint,
    c_uint8,
    c_uint64,
    c_void_p,
    cast,
)
from typing import TypeAlias

DriverPointer = c_void_p
OperationId = c_uint

# mypy seems to dislike the pointer bits, but these do accurately reflect the api surface,
# so... we'll just tell mypy to chill out on these
OperationIdPointer: TypeAlias = POINTER(OperationId)  # type: ignore[valid-type]
CancelPointer: TypeAlias = POINTER(c_bool)  # type: ignore[valid-type]
ZigSlicePointer: TypeAlias = POINTER("ZigSlice")  # type: ignore[valid-type, call-overload]
StringPointer: TypeAlias = POINTER(c_char_p)  # type: ignore[valid-type]
IntPointer: TypeAlias = POINTER(c_int)  # type: ignore[valid-type]
U64Pointer: TypeAlias = POINTER(c_uint64)  # type: ignore[valid-type]
BoolPointer: TypeAlias = POINTER(c_bool)  # type: ignore[valid-type]


class ZigU64Slice(Structure):
    """
    A struct representing a slice of u64 in zig.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    # fields must be declared this way to be c types compatible
    _fields_ = [  # noqa: RUF012
        ("ptr", POINTER(c_uint64)),
        ("len", c_size_t),
    ]

    def __init__(self, size: c_int):
        self.ptr = cast((c_uint64 * size.value)(), POINTER(c_uint64))
        self.len = size.value

        super().__init__()

    def get_contents(self) -> list[int]:
        """
        Return the contents of the slice as a list of ints.

        Args:
            N/A

        Returns:
            list[int]: the slice contents

        Raises:
            N/A

        """
        return [self.ptr[i] for i in range(self.len)]


class ZigSlice(Structure):
    """
    A struct representing a slice of u8 (a string) in zig.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    _fields_ = [  # noqa: RUF012
        ("ptr", POINTER(c_uint8)),
        ("len", c_size_t),
        ("value", c_char_p),
    ]

    def __init__(self, size: c_int):
        self.ptr = cast((c_uint8 * size.value)(), POINTER(c_uint8))
        self.len = size.value

        super().__init__()

    def get_contents(self) -> bytes:
        """
        Return the contents of the slice as bytes.

        Args:
            N/A

        Returns:
            bytes: the slice contents

        Raises:
            N/A

        """
        return bytes(cast(self.ptr, POINTER(c_uint8 * self.len)).contents)

    def get_decoded_contents(self) -> str:
        """
        Return the contents of the slice as str.

        Args:
            N/A

        Returns:
            bytes: the slice contents

        Raises:
            N/A

        """
        return self.get_contents().decode()


def to_c_string(s: str) -> c_char_p:
    """
    Accepts a string and converts it to a c_char_p.

    Args:
        s: the string-like thing to convert to a c_char_p

    Returns:
        c_char_p: the converted string

    Raises:
        N/A

    """
    return c_char_p(s.encode(encoding="utf-8"))


LogFuncCallback: TypeAlias = CFUNCTYPE(None, c_uint8, POINTER(ZigSlice))  # type: ignore[valid-type]
