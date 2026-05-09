"""scrapli.exceptions"""


class ScrapliException(Exception):
    """Base Exception for all scrapli exceptions"""


class LibScrapliException(ScrapliException):
    """Exception raised when encountering errors loading libscrapli shared library"""


class OptionsException(ScrapliException):
    """Exception raised when encountering errors applying options"""


class AllocationException(ScrapliException):
    """Exception raised when encountering errors allocating a cli/netconf object"""


class FFIException(ScrapliException):
    """Exception raised when encountering errors at the ffi boundary"""


class NotOpenedException(ScrapliException):
    """Exception raised when attempting to call methods of cli/netconf object and ptr is None"""


class OperationException(ScrapliException):
    """Exception raised when an error is returned from an operation"""


class ParsingException(ScrapliException):
    """Exception raised when parsing (usually cli) output fails"""


class NoMessagesException(ScrapliException):
    """Exception raised when attempting to request notifications or subscriptions and none exist"""


class OutOfMememoryException(ScrapliException, MemoryError):
    """Exception raised when allocations in libscrapli fail"""


class EOFException(ScrapliException, EOFError):
    """Exception raised when libscrapli returns an EOF"""


class CancelledException(ScrapliException):
    """Exception raised when libscrapli returns an error due to an operation being cancelled"""


class TimeoutException(ScrapliException, TimeoutError):
    """Exception raised when libscrapli returns an error due to an operation being timed out"""


class DriverException(ScrapliException):
    """Exception raised when libscrapli returns a driver error"""


class SessionException(ScrapliException):
    """Exception raised when libscrapli returns a session error"""


class TransportException(ScrapliException):
    """Exception raised when libscrapli returns a transport error"""


class InvalidArgumentException(ScrapliException):
    """Exception raised when libscrapli returns an invalid argument error"""
