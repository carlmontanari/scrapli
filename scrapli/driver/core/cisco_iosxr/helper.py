"""scrapli.driver.core.cisco_iosxr.helper"""
import time

from scrapli.driver import NetworkDriver


def comms_pre_login_handler(cls: NetworkDriver) -> None:  # pylint: disable=W0613
    """
    IOSXR default pre login handler

    Args:
        cls: IOSXRDriver object

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A

    """
    # sleep for session to establish; without this we never find base prompt
    time.sleep(1)
