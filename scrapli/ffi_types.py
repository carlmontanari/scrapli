"""scrapli.ffi_types"""

from ctypes import (
    POINTER,
    PYFUNCTYPE,
    Structure,
    _Pointer,
    c_bool,
    c_char_p,
    c_int,
    c_size_t,
    c_uint8,
    c_uint16,
    c_uint32,
    c_uint64,
    c_void_p,
    cast,
)
from logging import CRITICAL, DEBUG, FATAL, INFO, NOTSET, WARN, Logger
from typing import TYPE_CHECKING, Any, ClassVar, TypeAlias

DriverPointer = c_void_p
OperationId: TypeAlias = c_uint32

if TYPE_CHECKING:
    OperationIdPointer: TypeAlias = _Pointer[OperationId]

    CancelPointer: TypeAlias = _Pointer[c_bool]
    BoolPointer: TypeAlias = _Pointer[c_bool]

    IntPointer: TypeAlias = _Pointer[c_int]
    U16Pointer: TypeAlias = _Pointer[c_uint16]
    U32Pointer: TypeAlias = _Pointer[c_uint32]
    U64Pointer: TypeAlias = _Pointer[c_uint64]

    StringPointer: TypeAlias = _Pointer[c_char_p]

else:
    OperationIdPointer: TypeAlias = POINTER(OperationId)

    CancelPointer: TypeAlias = POINTER(c_bool)
    BoolPointer: TypeAlias = POINTER(c_bool)

    IntPointer: TypeAlias = POINTER(c_int)
    U16Pointer: TypeAlias = POINTER(c_uint16)
    U32Pointer: TypeAlias = POINTER(c_uint32)
    U64Pointer: TypeAlias = POINTER(c_uint64)

    StringPointer: TypeAlias = POINTER(c_char_p)


# cancellation is handled via timeout in python (vs context cancellation in go), so just have
# an always false cancellation pointer
CANCEL = CancelPointer(c_bool(False))


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
    _fields_: ClassVar[list[tuple[str, Any]]] = [
        ("ptr", POINTER(c_uint64)),
        ("len", c_size_t),
    ]

    def __init__(self, size: c_uint64):
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

    _fields_: ClassVar[list[tuple[str, Any]]] = [
        (
            "ptr",
            POINTER(c_uint8),
        ),
        ("len", c_size_t),
        ("value", c_char_p),
    ]

    def __init__(self, size: c_uint64):
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
        return bytes(cast(self.ptr, POINTER(c_uint8 * self.len)).contents[0 : self.len])

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


if TYPE_CHECKING:
    ZigSlicePointer: TypeAlias = _Pointer[ZigSlice]
else:
    ZigSlicePointer: TypeAlias = POINTER(ZigSlice)


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


# PYFUNCTYPE holds the gil during the call which *seems* to matter/be important since
# the zig bits will be tickling the logger (via the callback)
LogFuncCallback: TypeAlias = PYFUNCTYPE(None, c_uint8, POINTER(ZigSlice))  # type: ignore[valid-type]


def ffi_logger_wrapper(logger: Logger) -> LogFuncCallback:
    """
    Closure that accepts logger instance and returns a ffi logger callback

    Args:
        logger: the logger to wrap for use in the zig bits

    Returns:
        LogFuncCallback: the logger callback

    Raises:
        N/A

    """

    def _cb(level: c_uint8, message: ZigSlice) -> None:
        match level:
            case 0:
                # no "trace" level in std logger, so just format to be clear which ones are trace
                logger.debug("TRACE: %s", message.contents.get_decoded_contents())
            case 1:
                logger.debug(message.contents.get_decoded_contents())
            case 2:
                logger.info(message.contents.get_decoded_contents())
            case 3:
                logger.warning(message.contents.get_decoded_contents())
            case 4:
                logger.critical(message.contents.get_decoded_contents())
            case 5:
                logger.fatal(message.contents.get_decoded_contents())
            case _:
                return

    return LogFuncCallback(_cb)


def ffi_logger_level(logger: Logger) -> c_char_p:  # noqa: PLR0911
    """
    Returns a c string matching a libscrapli log level based on the given loggers configuration

    Args:
        logger: the logger we are getting the level from

    Returns:
        c_char_p: the level as a c string

    Raises:
        N/A

    """
    level = logger.getEffectiveLevel()

    if level == NOTSET:
        return c_char_p(b"trace")
    elif level == DEBUG:
        return c_char_p(b"debug")
    elif level == INFO:
        return c_char_p(b"info")
    elif level == WARN:
        return c_char_p(b"warn")
    elif level == CRITICAL:
        return c_char_p(b"critical")
    elif level == FATAL:
        return c_char_p(b"fatal")
    else:
        return c_char_p(b"warn")
