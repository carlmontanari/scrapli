"""scrapli.exceptions"""


class ScrapliTimeout(Exception):
    """Exception for any scrapli timeouts"""


class ScrapliKeepaliveFailure(Exception):
    """Exception for scrapli missing keepalives"""


class MissingDependencies(Exception):
    """Exception for any missing (probably optional) dependencies"""


class KeyVerificationFailed(Exception):
    """Exception for scrapli public key verification failure"""


class ScrapliAuthenticationFailed(Exception):
    """Exception for scrapli authentication failure"""


class UnknownPrivLevel(Exception):
    """Exception for encountering unknown privilege level"""


class CouldNotAcquirePrivLevel(Exception):
    """Exception for failure to acquire desired privilege level"""
