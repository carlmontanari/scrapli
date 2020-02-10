"""scrapli.driver.core.juniper_junos.helper"""
from scrapli.driver import NetworkDriver


def disable_paging(cls: NetworkDriver) -> None:
    """
    Disable paging and set screen width for Junos

    Args:
        cls: SSH2NetSocket connection object

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A
    """
    cls.channel.send_inputs("set cli screen-length 0")
    cls.channel.send_inputs("set cli screen-width 511")
