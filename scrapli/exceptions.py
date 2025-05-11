"""scrapli.exceptions"""


class ScrapliException(Exception):
    """Base Exception for all scrapli exceptions"""


class LibScrapliException(ScrapliException):
    """Exception raised when encountering errors loading libscrapli shared library"""


class OptionsException(ScrapliException):
    """Exception raised when encountering errors applying options"""


class AllocationException(ScrapliException):
    """Exception raised when encountering errors allocating a cli/netconf object"""


class OpenException(ScrapliException):
    """Exception raised when encountering errors opening a cli/netconf object"""


class CloseException(ScrapliException):
    """Exception raised when encountering errors closing a cli/netconf object"""


class GetResultException(ScrapliException):
    """Exception raised when encountering errors polling/fetching an operation result"""


class SubmitOperationException(ScrapliException):
    """Exception raised when encountering errors submitting an operation result"""


class NotOpenedException(ScrapliException):
    """Exception raised when attempting to call methods of cli/netconf object and ptr is None"""


class OperationException(ScrapliException):
    """Exception raised when an error is returned from an operation"""
