"""scrapli.netconf"""

from typing import Callable, Optional

from scrapli.auth import Options as AuthOptions
from scrapli.exceptions import NotOpenedException
from scrapli.ffi_mapping import LibScrapliMapping
from scrapli.ffi_types import (
    DriverPointer,
    LogFuncCallback,
    to_c_string,
)
from scrapli.session import Options as SessionOptions
from scrapli.transport import Options as TransportOptions


class Netconf:  # pylint: disable=too-many-instance-attributes
    """
    Netconf represents a netconf connection object.

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        host: str,
        *,
        logger_callback: Optional[Callable[[int, str], None]] = None,
        port: int = 830,
        auth_options: Optional[AuthOptions] = None,
        session_options: Optional[SessionOptions] = None,
        transport_options: Optional[TransportOptions] = None,
    ) -> None:
        self.ffi_mapping = LibScrapliMapping()

        self.host = host
        self._host = to_c_string(host)

        self.logger_callback = (
            LogFuncCallback(logger_callback) if logger_callback else LogFuncCallback(0)
        )

        self.port = port

        self.auth_options = auth_options or AuthOptions()
        self.session_options = session_options or SessionOptions()
        self.transport_options = transport_options or TransportOptions()

        self.ptr: Optional[DriverPointer] = None

    def _ptr_or_exception(self) -> DriverPointer:
        if self.ptr is None:
            raise NotOpenedException

        return self.ptr
