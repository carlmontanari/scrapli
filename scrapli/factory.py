"""scrapli.factory"""
import importlib
from copy import deepcopy
from logging import getLogger
from typing import Any, Dict, Optional, Tuple, Type, Union

from scrapli.driver import AsyncGenericDriver, AsyncNetworkDriver, GenericDriver, NetworkDriver
from scrapli.driver.base_driver import ASYNCIO_TRANSPORTS
from scrapli.driver.core import (
    AsyncEOSDriver,
    AsyncIOSXEDriver,
    AsyncIOSXRDriver,
    AsyncJunosDriver,
    AsyncNXOSDriver,
    EOSDriver,
    IOSXEDriver,
    IOSXRDriver,
    JunosDriver,
    NXOSDriver,
)
from scrapli.exceptions import ScrapliException

LOG = getLogger("scrapli.factory")

ASYNC_CORE_PLATFORM_MAP = {
    "arista_eos": AsyncEOSDriver,
    "cisco_iosxe": AsyncIOSXEDriver,
    "cisco_iosxr": AsyncIOSXRDriver,
    "cisco_nxos": AsyncNXOSDriver,
    "juniper_junos": AsyncJunosDriver,
}
SYNC_CORE_PLATFORM_MAP = {
    "arista_eos": EOSDriver,
    "cisco_iosxe": IOSXEDriver,
    "cisco_iosxr": IOSXRDriver,
    "cisco_nxos": NXOSDriver,
    "juniper_junos": JunosDriver,
}
ASYNC_DRIVER_MAP = {"network": AsyncNetworkDriver, "generic": AsyncGenericDriver}
SYNC_DRIVER_MAP = {"network": NetworkDriver, "generic": GenericDriver}


def _get_community_platform_details(community_platform_name: str) -> Dict[str, Any]:
    """
    Parent get driver method

    Args:
        community_platform_name: name of community

    Returns:
        platform_details: dict of details about community platform from scrapli_community library

    Raises:
        ModuleNotFoundError: if scrapli_community is not importable
        ModuleNotFoundError: if provided community_platform_name package is not importable
        ScrapliException: if community platform is missing "SCRAPLI_PLATFORM" attribute
        ScrapliException: for any unknown exception during community platform import

    """
    try:
        importlib.import_module(name="scrapli_community")
    except ModuleNotFoundError as exc:
        err = f"Module '{exc.name}' not found!"
        msg = f"***** {err} {'*' * (80 - len(err))}"
        fix = (
            "To resolve this issue, ensure you have the scrapli community package installed."
            " You can install this with pip: `pip install scrapli_community`."
        )
        warning = "\n" + msg + "\n" + fix + "\n" + msg
        raise ModuleNotFoundError(warning) from exc

    try:
        # replace any underscores in platform name with "."; should support any future platforms
        # that dont have "child" os types -- i.e. just "cisco" instead of "cisco_iosxe"
        scrapli_community_platform = importlib.import_module(
            name=f"scrapli_community.{community_platform_name.replace('_', '.')}"
        )
    except ModuleNotFoundError as exc:
        err = f"Platform '{community_platform_name}' not found!"
        msg = f"***** {err} {'*' * (80 - len(err))}"
        fix = (
            "To resolve this issue, ensure you have the correct platform name, and that a scrapli "
            " community platform of that name exists!"
        )
        warning = "\n" + msg + "\n" + fix + "\n" + msg
        raise ModuleNotFoundError(warning) from exc
    except Exception as exc:
        msg = "Unknown error occurred"
        raise ScrapliException(msg) from exc

    platform_details_original = getattr(scrapli_community_platform, "SCRAPLI_PLATFORM", {})
    if not platform_details_original:
        msg = "Community platform missing required attribute `SCRAPLI_PLATFORM`"
        raise ScrapliException(msg)
    platform_details: Dict[str, Any] = deepcopy(platform_details_original)
    return platform_details


def _get_driver_class(
    platform_details: Dict[str, Any], variant: Optional[str], _async: bool = False
) -> Union[
    Type[AsyncNetworkDriver], Type[AsyncGenericDriver], Type[NetworkDriver], Type[GenericDriver]
]:
    """
    Parent get driver method

    Args:
        platform_details: dict of details about community platform from scrapli_community library
        variant: optional name of variant of community platform
        _async: True/False this is for an asyncio transport driver

    Returns:
        NetworkDriver: final driver class

    Raises:
        N/A

    """
    if variant and platform_details["variants"][variant].get("driver_type"):
        variant_final_driver: Union[
            Type[AsyncNetworkDriver],
            Type[AsyncGenericDriver],
            Type[NetworkDriver],
            Type[GenericDriver],
        ]
        variant_driver_data = platform_details["variants"][variant].pop("driver_type")
        if _async is False:
            variant_final_driver = variant_driver_data["sync"]
        else:
            variant_final_driver = variant_driver_data["async"]
        return variant_final_driver

    if isinstance(platform_details["driver_type"], str):
        driver_type = platform_details["driver_type"]
        if _async is False:
            standard_final_driver = SYNC_DRIVER_MAP.get(driver_type, None)
        else:
            standard_final_driver = ASYNC_DRIVER_MAP.get(driver_type, None)
        if standard_final_driver:
            return standard_final_driver

    custom_base_final_driver: Union[
        Type[AsyncNetworkDriver],
        Type[AsyncGenericDriver],
        Type[NetworkDriver],
        Type[GenericDriver],
    ]
    if _async is False:
        custom_base_final_driver = platform_details["driver_type"]["sync"]
    else:
        custom_base_final_driver = platform_details["driver_type"]["async"]
    return custom_base_final_driver


def _get_driver_kwargs(
    platform_details: Dict[str, Any], variant: Optional[str], _async: bool = False
) -> Dict[str, Any]:
    """
    Parent get driver method

    Args:
        platform_details: dict of details about community platform from scrapli_community library
        variant: optional name of variant of community platform
        _async: True/False this is for an asyncio transport driver

    Returns:
        final_platform_kwargs: dict of final driver kwargs

    Raises:
        N/A

    """
    platform_kwargs = platform_details["defaults"]

    if variant:
        variant_kwargs = platform_details["variants"][variant]
        final_platform_kwargs = {**platform_kwargs, **variant_kwargs}
    else:
        final_platform_kwargs = platform_kwargs

    if not _async:
        # remove unnecessary asyncio things
        final_platform_kwargs.pop("async_on_open")
        final_platform_kwargs.pop("async_on_close")
        # rename sync_on_(open|close) keys to just "on_open"/"on_close"
        final_platform_kwargs["on_open"] = final_platform_kwargs.pop("sync_on_open")
        final_platform_kwargs["on_close"] = final_platform_kwargs.pop("sync_on_close")
    else:
        # remove unnecessary sync things
        final_platform_kwargs.pop("sync_on_open")
        final_platform_kwargs.pop("sync_on_close")
        # rename sync_on_(open|close) keys to just "on_open"/"on_close"
        final_platform_kwargs["on_open"] = final_platform_kwargs.pop("async_on_open")
        final_platform_kwargs["on_close"] = final_platform_kwargs.pop("async_on_close")

    return final_platform_kwargs


def _get_community_driver(
    community_platform_name: str, variant: Optional[str], _async: bool = False
) -> Tuple[
    Union[
        Type[AsyncNetworkDriver], Type[AsyncGenericDriver], Type[NetworkDriver], Type[GenericDriver]
    ],
    Dict[str, Any],
]:
    """
    Get community driver

    Args:
        community_platform_name: name of community
        variant: optional name of variant of community platform
        _async: True/False this is for an asyncio transport driver

    Returns:
        NetworkDriver: final driver class

    Raises:
        N/A

    """
    platform_details = _get_community_platform_details(
        community_platform_name=community_platform_name
    )

    final_driver = _get_driver_class(
        platform_details=platform_details, variant=variant, _async=_async
    )
    final_platform_kwargs = _get_driver_kwargs(
        platform_details=platform_details, variant=variant, _async=_async
    )

    return final_driver, final_platform_kwargs


def _get_driver(
    platform: str, variant: Optional[str], _async: bool = False
) -> Tuple[Union[Type[NetworkDriver], Type[GenericDriver]], Dict[str, Any]]:
    """
    Parent get driver function

    Args:
        platform: name of target platform; i.e. `cisco_iosxe`, `arista_eos`, etc.
        variant: name of the target platform variant
        _async: True/False this is for an asyncio transport driver

    Returns:
        NetworkDriver: final driver class; generally NetworkDriver, but for some community platforms
            could be GenericDriver

    Raises:
        N/A

    """
    additional_kwargs: Dict[str, Any] = {}

    if platform in SYNC_CORE_PLATFORM_MAP:
        if _async is False:
            final_driver = SYNC_CORE_PLATFORM_MAP[platform]
        else:
            final_driver = ASYNC_CORE_PLATFORM_MAP[platform]
        msg = f"Driver `{final_driver}` selected from scrapli core drivers"
    else:
        final_driver, additional_kwargs = _get_community_driver(
            community_platform_name=platform, variant=variant, _async=_async
        )
        msg = (
            f"Driver `{final_driver}` selected from scrapli community platforms, with the following"
            f" platform arguments: `{additional_kwargs}`"
        )

    LOG.info(msg)
    return final_driver, additional_kwargs


class Scrapli(NetworkDriver):
    def __new__(
        cls, platform: str, variant: Optional[str] = None, **kwargs: Dict[Any, Any]
    ) -> "Scrapli":
        """
        Scrapli Factory method for synchronous drivers

        Args:
            cls: class object
            platform: name of target platform; i.e. `cisco_iosxe`, `arista_eos`, etc.
            variant: optional name of variant of community platform
            **kwargs: keyword arguments to pass to selected driver class

        Returns:
            final_driver: synchronous driver class for provided driver

        Raises:
            ScrapliException: if provided transport is asyncio
            ScrapliException: if `platform` not in keyword arguments

        """
        LOG.debug("Scrapli factory initialized")

        if kwargs.get("transport", "system") in ASYNCIO_TRANSPORTS:
            raise ScrapliException("Use `AsyncScrapli` if using an async transport!")

        if not isinstance(platform, str):
            raise ScrapliException(f"Argument `platform` must be `str` got `{type(platform)}`")

        final_driver, additional_kwargs = _get_driver(
            platform=platform, variant=variant, _async=False
        )

        # at this point will need to merge the additional kwargs in (for community drivers),
        # ensure that kwargs passed by user supersede the ones coming from community platform
        if additional_kwargs:
            final_kwargs = {**additional_kwargs, **kwargs}
        else:
            final_kwargs = kwargs

        # mypy was displeased about NetworkDriver not being callable, fix later probably :)
        final_conn: "Scrapli" = final_driver(**final_kwargs)  # type: ignore
        return final_conn


class AsyncScrapli(AsyncNetworkDriver):
    def __new__(
        cls, platform: str, variant: Optional[str] = None, **kwargs: Dict[Any, Any]
    ) -> "AsyncScrapli":
        """
        Scrapli Factory method for asynchronous drivers

        Args:
            cls: class object
            platform: name of target platform; i.e. `cisco_iosxe`, `arista_eos`, etc.
            variant: optional name of variant of community platform
            **kwargs: keyword arguments to pass to selected driver class

        Returns:
            final_driver: synchronous driver class for provided driver

        Raises:
            ScrapliException: if provided transport is not asyncio
            ScrapliException: if `platform` not in keyword arguments

        """
        LOG.debug("Scrapli factory initialized")

        if kwargs.get("transport", "system") not in ASYNCIO_TRANSPORTS:
            raise ScrapliException("Use `Scrapli` if using a synchronous transport!")

        if not isinstance(platform, str):
            raise ScrapliException(f"Argument `platform` must be `str` got `{type(platform)}`")

        final_driver, additional_kwargs = _get_driver(
            platform=platform, variant=variant, _async=True
        )

        # at this point will need to merge the additional kwargs in (for community drivers),
        # ensure that kwargs passed by user supersede the ones coming from community platform
        if additional_kwargs:
            final_kwargs = {**additional_kwargs, **kwargs}
        else:
            final_kwargs = kwargs

        # mypy was displeased about NetworkDriver not being callable, fix later probably :)
        final_conn: "AsyncScrapli" = final_driver(**final_kwargs)  # type: ignore
        return final_conn
