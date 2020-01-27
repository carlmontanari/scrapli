"""nssh.exceptions"""


class NSSHTimeout(Exception):
    """Exception for any nssh timeouts"""


class MissingDependencies(Exception):
    """Exception for any missing (probably optional) dependencies"""


class NSSHAuthenticationFailed(Exception):
    """Exception for nssh authentication failure"""


class UnknownPrivLevel(Exception):
    """Exception for encountering unknown privilege level"""


class CouldNotAcquirePrivLevel(Exception):
    """Exception for failure to acquire desired privilege level"""
