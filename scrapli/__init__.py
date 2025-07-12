"""scrapli"""

from scrapli.auth import LookupKeyValue
from scrapli.auth import Options as AuthOptions
from scrapli.cli import Cli, ReadCallback
from scrapli.netconf import Netconf
from scrapli.netconf import Options as NetconfOptions
from scrapli.session import Options as SessionOptions
from scrapli.transport import BinOptions as TransportBinOptions
from scrapli.transport import Ssh2Options as TransportSsh2Options
from scrapli.transport import TelnetOptions as TransportTelnetOptions
from scrapli.transport import TestOptions as TransportTestOptions

__version__ = "2.0.0-alpha.5"
__calendar_version__ = "2025.7.12"
__definitions_version__ = "c38ec6d"

__all__ = (
    "AuthOptions",
    "Cli",
    "LookupKeyValue",
    "Netconf",
    "NetconfOptions",
    "ReadCallback",
    "SessionOptions",
    "TransportBinOptions",
    "TransportSsh2Options",
    "TransportTelnetOptions",
    "TransportTestOptions",
)
