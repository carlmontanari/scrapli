"""scrapli.factory"""
import importlib
from logging import getLogger
from typing import Any, Dict

from scrapli.driver import NetworkDriver
from scrapli.exceptions import ScrapliException

LOG = getLogger("scrapli.factory")

CORE_PLATFORM_MAP = {
    "arista_eos": "EOSDriver",
    "cisco_iosxe": "IOSXEDriver",
    "cisco_iosxr": "IOSXRDriver",
    "cisco_nxos": "NXOSDriver",
    "juniper_junos": "JunosDriver",
}


def _get_core_driver(driver: str) -> NetworkDriver:
    """
    Get core driver

    Args:
        driver: Name of driver to get

    Returns:
        NetworkDriver: final driver class

    Raises:
        ScrapliException: if any issue getting core driver

    """
    try:
        final_driver: NetworkDriver = getattr(
            importlib.import_module(name="scrapli.driver.core"), driver
        )
        return final_driver
    except Exception as exc:
        msg = f"Error importing core driver `{driver}`; exception: `{exc}`"
        LOG.exception(msg)
        raise ScrapliException(msg)


def _get_driver(driver: str) -> NetworkDriver:
    """
    Parent get driver method

    Args:
        driver: Name of driver to get

    Returns:
        NetworkDriver: final driver class

    Raises:
        ScrapliException: if `platform` not in core drivers - community platforms coming soon!

    """
    core_driver = CORE_PLATFORM_MAP.get(driver, None)

    if core_driver:
        final_driver = _get_core_driver(driver=core_driver)
        msg = f"Driver `{final_driver}` selected from scrapli core drivers"
    else:
        raise ScrapliException("Community platform support/factory coming soon!")

    LOG.info(msg)
    return final_driver


class Scrapli(NetworkDriver):
    def __new__(cls, **kwargs: Dict[Any, Any]) -> "Scrapli":
        """
        Scrapli Factory method for synchronous drivers

        Args:
            cls: class object
            **kwargs: keyword arguments to pass to selected driver class plus the additional
                `driver` keyword argument which should match a core or community driver name!

        Returns:
            final_driver: synchronous driver class for provided driver

        Raises:
            ScrapliException: if `platform` not in keyword arguments

        """
        LOG.debug("Scrapli factory initialized")

        if "platform" not in kwargs.keys():
            msg = "Argument `platform` must be provided when using `Scrapli` factory!"
            LOG.exception(msg)
            raise ScrapliException(msg)
        driver = kwargs.pop("platform")

        if not isinstance(driver, str):
            raise ScrapliException(f"Argument `platform` must be `str` got `{type(driver)}`")

        final_driver = _get_driver(driver=driver)
        return final_driver(**kwargs)
