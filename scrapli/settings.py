"""scrapli.settings"""


class Settings:
    # supress user warnings for things like strict key
    SUPPRESS_USER_WARNINGS = False
    # when true, do *not* terminate connections when timeouts occur
    NO_TERMINATE_ON_TIMEOUT = False
