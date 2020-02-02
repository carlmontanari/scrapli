"""nssh.driver.core.juniper_junos.helper"""
from nssh.driver import NetworkDriver


def disable_paging(cls: NetworkDriver) -> None:
    """
    Disable paging and set screen width for Junos

    Args:
        cls: SSH2NetSocket connection object

    Returns:
        N/A  # noqa

    Raises:
        N/A  # noqa
    """
    cls.channel.send_inputs("set cli screen-length 0")
    cls.channel.send_inputs("set cli screen-width 511")
