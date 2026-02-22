"""scrapli.ffi_types"""

import xml.etree.ElementTree as ET
from collections.abc import Callable
from ctypes import (
    CFUNCTYPE,
    POINTER,
    Structure,
)
from ctypes import _CFuncPtr as FuncPtr  # type: ignore[attr-defined]
from ctypes import (
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
    create_string_buffer,
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
    USizePointer: TypeAlias = _Pointer[c_size_t]

    StringPointer: TypeAlias = _Pointer[c_char_p]

else:
    OperationIdPointer: TypeAlias = POINTER(OperationId)

    CancelPointer: TypeAlias = POINTER(c_bool)
    BoolPointer: TypeAlias = POINTER(c_bool)

    IntPointer: TypeAlias = POINTER(c_int)
    U16Pointer: TypeAlias = POINTER(c_uint16)
    U32Pointer: TypeAlias = POINTER(c_uint32)
    U64Pointer: TypeAlias = POINTER(c_uint64)
    USizePointer: TypeAlias = POINTER(c_size_t)

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


if TYPE_CHECKING:
    ZigU64SlicePointer: TypeAlias = _Pointer[ZigU64Slice]
else:
    ZigU64SlicePointer: TypeAlias = POINTER(ZigU64Slice)


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
    ]

    def __init__(self, size: c_size_t | c_uint64):
        self.ptr = cast(create_string_buffer(size.value), POINTER(c_uint8))
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


LoggerCallbackC = CFUNCTYPE(None, c_uint8, ZigSlicePointer)
LoggerCallback: TypeAlias = FuncPtr


def ffi_logger_callback_wrapper(logger: Logger) -> LoggerCallback:
    """
    Closure that accepts logger instance and returns a ffi logger callback

    Args:
        logger: the logger to wrap for use in the zig bits

    Returns:
        LogerCallback: the logger callback

    Raises:
        N/A

    """

    def _cb(level: c_uint8, message: ZigSlicePointer) -> None:
        v = message.contents
        if v is None:
            return

        m = v.get_decoded_contents()

        match level:
            case 0:
                # no "trace" level in std logger, so just format to be clear which ones are trace
                logger.debug("TRACE: %s", m)
            case 1:
                logger.debug(m)
            case 2:
                logger.info(m)
            case 3:
                logger.warning(m)
            case 4:
                logger.critical(m)
            case 5:
                logger.fatal(m)
            case _:
                return

    return LoggerCallbackC(_cb)


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


RecorderCallbackC = CFUNCTYPE(None, ZigSlicePointer)
RecorderCallback: TypeAlias = FuncPtr


def recorder_callback_wrapper(cb: Callable[[str], None]) -> RecorderCallback:
    """
    Closure that accepts a session recorder callback and returns an ffi compatible wrapper

    Args:
        cb: the recorder to wrap for use in the zig bits

    Returns:
        RecorderCallback: the recorder callback

    Raises:
        N/A

    """

    def _cb(buf: ZigSlicePointer) -> None:
        v = buf.contents
        if not v:
            return

        return cb(v.get_decoded_contents())

    return RecorderCallbackC(_cb)


NetconfCapabilitesCallbackC = CFUNCTYPE(c_char_p, StringPointer)
NetconfCapabilitesCallback: TypeAlias = FuncPtr


def capabilities_callback_wrapper(
    cb: Callable[[list[str]], list[str]],
) -> NetconfCapabilitesCallback:
    """
    Closure that accepts a netconf capabillities callback and returns an ffi compatible wrapper

    Args:
        cb: the capabilities handler to wrap for use in the zig bits

    Returns:
        NetconfCapabilitesCallback: the capabilities callback

    Raises:
        N/A

    """

    def _cb(server_hello: StringPointer) -> c_char_p:
        # mypy will be upset because its a pointer so could be none, but it wont. its ok mypy
        server_capabilities: bytes = server_hello.contents.value or b""

        root = ET.fromstring(server_capabilities)

        caps = [
            elem.text or ""
            for elem in root.findall(
                ".//nc:capability", {"nc": "urn:ietf:params:xml:ns:netconf:base:1.0"}
            )
        ]

        user_capabilities = cb(caps)

        out_elems = []

        for cap in user_capabilities:
            el = ET.Element("capability")
            el.text = cap
            out_elems.append(ET.tostring(el, encoding="unicode"))

        return c_char_p("".join(out_elems).encode())

    return NetconfCapabilitesCallbackC(_cb)
