"""scrapli.exceptions"""


class ScrapliException(Exception):
    """Base Exception for scrapli"""


class SSHNotFound(ScrapliException):
    """Exception for system transport unable to find ssh executable"""


class ScrapliCommandFailure(ScrapliException):
    """Exception for scrapli command/config failures"""


class ScrapliTimeout(ScrapliException):
    """Exception for any scrapli timeouts"""


class ScrapliKeepaliveFailure(ScrapliException):
    """Exception for scrapli missing keepalives"""


class MissingDependencies(ScrapliException):
    """Exception for any missing (probably optional) dependencies"""


class KeyVerificationFailed(ScrapliException):
    """Exception for scrapli public key verification failure"""


class ScrapliAuthenticationFailed(ScrapliException):
    """Exception for scrapli authentication failure"""


class UnknownPrivLevel(ScrapliException):
    """Exception for encountering unknown privilege level"""


class CouldNotAcquirePrivLevel(ScrapliException):
    """Exception for failure to acquire desired privilege level"""


class TransportPluginError(ScrapliException):
    """Exception for transport plugin loading errors"""


class ConnectionNotOpened(ScrapliException):
    """Exception for failures due to connection not being open"""


class UnsupportedPlatform(ScrapliException):
    """Exception for unsupported platform; i.e. using system transport on windows"""
