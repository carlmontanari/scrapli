"""scrapli.exceptions"""


class ScrapliTimeout(Exception):
    """Exception for any scrapli timeouts"""


class MissingDependencies(Exception):
    """Exception for any missing (probably optional) dependencies"""


class ScrapliAuthenticationFailed(Exception):
    """Exception for scrapli authentication failure"""


class UnknownPrivLevel(Exception):
    """Exception for encountering unknown privilege level"""


class CouldNotAcquirePrivLevel(Exception):
    """Exception for failure to acquire desired privilege level"""
