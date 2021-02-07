"""scrapli.exceptions"""
from typing import Optional


class ScrapliException(Exception):
    """Base Exception for all scrapli exceptions"""


class ScrapliModuleNotFound(ScrapliException):
    """ModuleNotFound but for scrapli related issues"""


class ScrapliTypeError(ScrapliException):
    """TypeError but for scrapli related typing issues"""


class ScrapliValueError(ScrapliException):
    """ValueError but for scrapli related value issues"""


class ScrapliUnsupportedPlatform(ScrapliException):
    """Exception for unsupported platform; i.e. using system transport on windows"""


class ScrapliTransportPluginError(ScrapliException):
    """Exception for transport plugin issues"""


class ScrapliConnectionNotOpened(ScrapliException):
    """Exception for trying to operate on a transport which has not been opened"""

    def __init__(
        self,
        message: Optional[str] = None,
    ) -> None:
        """
        Scrapli connection not opened exception

        Args:
            message: optional message

        Returns:
            None

        Raises:
            N/A

        """
        if not message:
            self.message = (
                "connection not opened, but attempting to call a method that requires an open "
                "connection, do you need to call 'open()'?"
            )
        else:
            self.message = message
        super().__init__(self.message)


class ScrapliAuthenticationFailed(ScrapliException):
    """Exception for scrapli authentication issues"""


class ScrapliConnectionError(ScrapliException):
    """Exception for underlying connection issues"""


class ScrapliTimeout(ScrapliException):
    """Exception for any scrapli timeouts"""


class ScrapliCommandFailure(ScrapliException):
    """Exception for scrapli command/config failures"""


class ScrapliPrivilegeError(ScrapliException):
    """Exception for all privilege related scrapli issues"""
