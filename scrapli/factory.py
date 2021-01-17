"""scrapli.factory"""
import importlib
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union, cast

from scrapli.driver import AsyncGenericDriver, AsyncNetworkDriver, GenericDriver, NetworkDriver
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
from scrapli.driver.network.base_driver import PrivilegeLevel
from scrapli.exceptions import (
    ScrapliException,
    ScrapliModuleNotFound,
    ScrapliTypeError,
    ScrapliValueError,
)
from scrapli.helper import format_user_warning
from scrapli.logging import logger
from scrapli.transport import ASYNCIO_TRANSPORTS


def _build_provided_kwargs_dict(  # pylint: disable=R0914
    host: str,
    privilege_levels: Optional[Dict[str, PrivilegeLevel]],
    default_desired_privilege_level: str,
    port: int,
    auth_username: str,
    auth_password: str,
    auth_private_key: str,
    auth_private_key_passphrase: str,
    auth_strict_key: Optional[bool],
    auth_bypass: Optional[bool],
    timeout_socket: float,
    timeout_transport: float,
    timeout_ops: float,
    comms_return_char: str,
    comms_ansi: Optional[bool],
    ssh_config_file: Optional[Union[str, bool]],
    ssh_known_hosts_file: Optional[Union[str, bool]],
    on_init: Optional[Callable[..., Any]],
    on_open: Optional[Callable[..., Any]],
    on_close: Optional[Callable[..., Any]],
    transport: str,
    transport_options: Optional[Dict[str, Any]],
    channel_log: Optional[Union[str, bool]],
    channel_lock: Optional[bool],
    auth_secondary: str,
    failed_when_contains: Optional[List[str]],
    textfsm_platform: str,
    genie_platform: str,
    **kwargs: Dict[Any, Any],
) -> Dict[str, Any]:
    """
    Build arguments dict based on provided inputs

    This function builds the dict of keyword args to unpack and send to the driver -- in the factory
    context this also needs to convert the arguments that have defaults that evaluate to False (i.e
    ssh_config_file which defaults to False) from None which is their default in the factory, back
    to their normal default if they are still None -OR- to whatever the user provided.

    TODO args/returns/etc.
    """
    # handle the args that would be None/False so we dont strip them out if not provided
    auth_strict_key = auth_strict_key if auth_strict_key is not None else True
    auth_bypass = auth_bypass if auth_bypass is not None else False
    comms_ansi = comms_ansi if comms_ansi is not None else False
    ssh_config_file = ssh_config_file if ssh_config_file is not None else False
    ssh_known_hosts_file = ssh_known_hosts_file if ssh_known_hosts_file is not None else False
    channel_log = channel_log if channel_log is not None else False
    channel_lock = channel_lock if channel_lock is not None else False

    # dict of all args coming from the factories minus the None/False args above
    _provided_args = {
        "host": host,
        "privilege_levels": privilege_levels,
        "default_desired_privilege_level": default_desired_privilege_level,
        "port": port,
        "auth_username": auth_username,
        "auth_password": auth_password,
        "auth_private_key": auth_private_key,
        "auth_private_key_passphrase": auth_private_key_passphrase,
        "timeout_socket": timeout_socket,
        "timeout_transport": timeout_transport,
        "timeout_ops": timeout_ops,
        "comms_return_char": comms_return_char,
        "on_init": on_init,
        "on_open": on_open,
        "on_close": on_close,
        "transport": transport,
        "transport_options": transport_options,
        "auth_secondary": auth_secondary,
        "failed_when_contains": failed_when_contains,
        "textfsm_platform": textfsm_platform,
        "genie_platform": genie_platform,
    }

    # add back in the None/False args
    _provided_args = {key: value for key, value in _provided_args.items() if value}
    _provided_args["auth_strict_key"] = auth_strict_key
    _provided_args["auth_bypass"] = auth_bypass
    _provided_args["comms_ansi"] = comms_ansi
    _provided_args["ssh_config_file"] = ssh_config_file
    _provided_args["ssh_known_hosts_file"] = ssh_known_hosts_file
    _provided_args["channel_log"] = channel_log
    _provided_args["channel_lock"] = channel_lock

    # merge in any kwargs that maybe need to get passed down
    all_provided_args = {**_provided_args, **kwargs}
    return all_provided_args


def _get_community_platform_details(community_platform_name: str) -> Dict[str, Any]:
    """
    Fetch community platform details

    Args:
        community_platform_name: name of community

    Returns:
        platform_details: dict of details about community platform from scrapli_community library

    Raises:
        ScrapliModuleNotFound: if scrapli_community is not importable
        ScrapliModuleNotFound: if provided community_platform_name package is not importable
        ScrapliException: if community platform is missing "SCRAPLI_PLATFORM" attribute

    """
    try:
        importlib.import_module(name="scrapli_community")
    except ModuleNotFoundError as exc:
        title = "Module not found!"
        message = (
            "Scrapli Community package is not installed!\n"
            "To resolve this issue, install the transport plugin. You can do this in one of "
            "the following ways:\n"
            "1: 'pip install -r requirements-community.txt'\n"
            "2: 'pip install scrapli[community]'"
        )
        warning = format_user_warning(title=title, message=message)
        raise ScrapliModuleNotFound(warning) from exc

    try:
        # replace any underscores in platform name with "."; should support any future platforms
        # that dont have "child" os types -- i.e. just "cisco" instead of "cisco_iosxe"
        scrapli_community_platform = importlib.import_module(
            name=f"scrapli_community.{community_platform_name.replace('_', '.')}"
        )
    except ModuleNotFoundError as exc:
        title = "Module not found!"
        message = (
            f"Scrapli Community platform '{community_platform_name}` not found!\n"
            "To resolve this issue, ensure you have the correct platform name, and that a scrapli "
            " community platform of that name exists!"
        )
        warning = format_user_warning(title=title, message=message)
        raise ScrapliModuleNotFound(warning) from exc

    platform_details_original = getattr(scrapli_community_platform, "SCRAPLI_PLATFORM", {})
    if not platform_details_original:
        msg = "Community platform missing required attribute `SCRAPLI_PLATFORM`"
        raise ScrapliException(msg)
    platform_details: Dict[str, Any] = deepcopy(platform_details_original)
    return platform_details


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


class Scrapli(NetworkDriver):
    CORE_PLATFORM_MAP = {
        "arista_eos": EOSDriver,
        "cisco_iosxe": IOSXEDriver,
        "cisco_iosxr": IOSXRDriver,
        "cisco_nxos": NXOSDriver,
        "juniper_junos": JunosDriver,
    }
    DRIVER_MAP = {"network": NetworkDriver, "generic": GenericDriver}

    @classmethod
    def _get_driver_class(
        cls, platform_details: Dict[str, Any], variant: Optional[str]
    ) -> Union[Type[NetworkDriver], Type[GenericDriver]]:
        """
        Fetch community driver class based on platform details

        Args:
            platform_details: dict of details about community platform from scrapli_community
                library
            variant: optional name of variant of community platform

        Returns:
            NetworkDriver: final driver class

        Raises:
            N/A

        """
        final_driver: Union[
            Type[NetworkDriver],
            Type[GenericDriver],
        ]

        if variant and platform_details["variants"][variant].get("driver_type"):
            variant_driver_data = platform_details["variants"][variant].pop("driver_type")
            final_driver = variant_driver_data["sync"]
            return final_driver

        if isinstance(platform_details["driver_type"], str):
            driver_type = platform_details["driver_type"]
            standard_final_driver = cls.DRIVER_MAP.get(driver_type, None)
            if standard_final_driver:
                return standard_final_driver

        final_driver = platform_details["driver_type"]["sync"]
        return final_driver

    @classmethod
    def _get_community_driver(
        cls, community_platform_name: str, variant: Optional[str]
    ) -> Tuple[Union[Type[NetworkDriver], Type[GenericDriver]], Dict[str, Any]]:
        """
        Get community driver

        Args:
            community_platform_name: name of community
            variant: optional name of variant of community platform

        Returns:
            NetworkDriver: final driver class

        Raises:
            N/A

        """
        platform_details = _get_community_platform_details(
            community_platform_name=community_platform_name
        )

        final_driver = cls._get_driver_class(platform_details=platform_details, variant=variant)
        final_platform_kwargs = _get_driver_kwargs(
            platform_details=platform_details, variant=variant, _async=False
        )

        return final_driver, final_platform_kwargs

    @classmethod
    def _get_driver(
        cls, platform: str, variant: Optional[str]
    ) -> Tuple[Union[Type[NetworkDriver], Type[GenericDriver]], Dict[str, Any]]:
        """
        Parent get driver method for sync Scrapli

        Args:
            platform: name of target platform; i.e. `cisco_iosxe`, `arista_eos`, etc.
            variant: name of the target platform variant

        Returns:
            NetworkDriver: final driver class; generally NetworkDriver, but for some community
                platforms could be GenericDriver, also returns any additional kwargs comming from
                the community platform (if any)

        Raises:
            N/A

        """
        additional_kwargs: Dict[str, Any] = {}
        final_driver: Union[Type[GenericDriver], Type[NetworkDriver]]

        if platform in cls.CORE_PLATFORM_MAP:
            final_driver = cls.CORE_PLATFORM_MAP[platform]
            msg = f"Driver '{final_driver}' selected from scrapli core drivers"
        else:
            final_driver, additional_kwargs = cls._get_community_driver(
                community_platform_name=platform, variant=variant
            )
            msg = (
                f"Driver '{final_driver}' selected from scrapli community platforms, with the "
                f"following platform arguments: '{additional_kwargs}'"
            )

        logger.info(msg)
        return final_driver, additional_kwargs

    def __new__(  # pylint: disable=R0914
        cls,
        platform: str,
        host: str,
        privilege_levels: Optional[Dict[str, PrivilegeLevel]] = None,
        default_desired_privilege_level: str = "",
        port: int = 22,
        auth_username: str = "",
        auth_password: str = "",
        auth_private_key: str = "",
        auth_private_key_passphrase: str = "",
        auth_strict_key: Optional[bool] = None,
        auth_bypass: Optional[bool] = None,
        timeout_socket: float = 15.0,
        timeout_transport: float = 30.0,
        timeout_ops: float = 30.0,
        comms_return_char: str = "\n",
        comms_ansi: Optional[bool] = None,
        ssh_config_file: Optional[Union[str, bool]] = None,
        ssh_known_hosts_file: Optional[Union[str, bool]] = None,
        on_init: Optional[Callable[..., Any]] = None,
        on_open: Optional[Callable[..., Any]] = None,
        on_close: Optional[Callable[..., Any]] = None,
        transport: str = "",
        transport_options: Optional[Dict[str, Any]] = None,
        channel_log: Optional[Union[str, bool]] = None,
        channel_lock: Optional[bool] = None,
        auth_secondary: str = "",
        failed_when_contains: Optional[List[str]] = None,
        textfsm_platform: str = "",
        genie_platform: str = "",
        variant: Optional[str] = None,
        **kwargs: Dict[Any, Any],
    ) -> "Scrapli":
        """
        Scrapli Factory method for synchronous drivers

        Args:
            platform: name of target platform; i.e. `cisco_iosxe`, `arista_eos`, etc.
            variant: optional name of variant of community platform
            **kwargs: keyword arguments to pass to selected driver class

        Returns:
            final_driver: synchronous driver class for provided driver

        Raises:
            ScrapliValueError: if provided transport is asyncio
            ScrapliTypeError: if `platform` not in keyword arguments

        """
        logger.debug("Scrapli factory initialized")

        if transport in ASYNCIO_TRANSPORTS:
            raise ScrapliValueError("Use 'AsyncScrapli' if using an async transport!")

        if not isinstance(platform, str):
            raise ScrapliTypeError(f"Argument 'platform' must be 'str' got '{type(platform)}'")

        provided_kwargs = _build_provided_kwargs_dict(
            host=host,
            port=port,
            auth_username=auth_username,
            auth_password=auth_password,
            auth_private_key=auth_private_key,
            auth_private_key_passphrase=auth_private_key_passphrase,
            auth_strict_key=auth_strict_key,
            auth_bypass=auth_bypass,
            timeout_socket=timeout_socket,
            timeout_transport=timeout_transport,
            timeout_ops=timeout_ops,
            comms_return_char=comms_return_char,
            comms_ansi=comms_ansi,
            ssh_config_file=ssh_config_file,
            ssh_known_hosts_file=ssh_known_hosts_file,
            on_init=on_init,
            on_open=on_open,
            on_close=on_close,
            transport=transport,
            transport_options=transport_options,
            channel_log=channel_log,
            channel_lock=channel_lock,
            privilege_levels=privilege_levels,
            default_desired_privilege_level=default_desired_privilege_level,
            auth_secondary=auth_secondary,
            failed_when_contains=failed_when_contains,
            textfsm_platform=textfsm_platform,
            genie_platform=genie_platform,
            **kwargs,
        )

        final_driver, additional_kwargs = cls._get_driver(platform=platform, variant=variant)

        # at this point will need to merge the additional kwargs in (for community drivers),
        # ensure that kwargs passed by user supersede the ones coming from community platform
        if additional_kwargs:
            final_kwargs = {**additional_kwargs, **provided_kwargs}
        else:
            final_kwargs = provided_kwargs

        final_conn = final_driver(**final_kwargs)
        # cast the final conn to type Scrapli to appease mypy -- we know it will be a NetworkDriver
        # or GenericDriver, but thats ok =)
        final_conn = cast(Scrapli, final_conn)
        return final_conn


class AsyncScrapli(AsyncNetworkDriver):
    CORE_PLATFORM_MAP = {
        "arista_eos": AsyncEOSDriver,
        "cisco_iosxe": AsyncIOSXEDriver,
        "cisco_iosxr": AsyncIOSXRDriver,
        "cisco_nxos": AsyncNXOSDriver,
        "juniper_junos": AsyncJunosDriver,
    }
    DRIVER_MAP = {"network": AsyncNetworkDriver, "generic": AsyncGenericDriver}

    @classmethod
    def _get_driver_class(
        cls, platform_details: Dict[str, Any], variant: Optional[str]
    ) -> Union[Type[AsyncNetworkDriver], Type[AsyncGenericDriver]]:
        """TODO"""
        final_driver: Union[
            Type[AsyncNetworkDriver],
            Type[AsyncGenericDriver],
        ]

        if variant and platform_details["variants"][variant].get("driver_type"):
            variant_driver_data = platform_details["variants"][variant].pop("driver_type")
            final_driver = variant_driver_data["async"]
            return final_driver

        if isinstance(platform_details["driver_type"], str):
            driver_type = platform_details["driver_type"]
            standard_final_driver = cls.DRIVER_MAP.get(driver_type, None)
            if standard_final_driver:
                return standard_final_driver

        final_driver = platform_details["driver_type"]["async"]
        return final_driver

    @classmethod
    def _get_community_driver(
        cls, community_platform_name: str, variant: Optional[str]
    ) -> Tuple[Union[Type[AsyncNetworkDriver], Type[AsyncGenericDriver]], Dict[str, Any]]:
        """TODO"""
        platform_details = _get_community_platform_details(
            community_platform_name=community_platform_name
        )

        final_driver = cls._get_driver_class(platform_details=platform_details, variant=variant)
        final_platform_kwargs = _get_driver_kwargs(
            platform_details=platform_details, variant=variant, _async=True
        )

        return final_driver, final_platform_kwargs

    @classmethod
    def _get_driver(
        cls, platform: str, variant: Optional[str]
    ) -> Tuple[Union[Type[AsyncNetworkDriver], Type[AsyncGenericDriver]], Dict[str, Any]]:
        """TODO"""
        additional_kwargs: Dict[str, Any] = {}
        final_driver: Union[Type[AsyncGenericDriver], Type[AsyncNetworkDriver]]

        if platform in cls.CORE_PLATFORM_MAP:
            final_driver = cls.CORE_PLATFORM_MAP[platform]
            msg = f"Driver '{final_driver}' selected from scrapli core drivers"
        else:
            final_driver, additional_kwargs = cls._get_community_driver(
                community_platform_name=platform, variant=variant
            )
            msg = (
                f"Driver '{final_driver}' selected from scrapli community platforms, with the "
                f"following platform arguments: '{additional_kwargs}'"
            )

        logger.info(msg)
        return final_driver, additional_kwargs

    def __new__(  # pylint: disable=R0914
        cls,
        platform: str,
        host: str,
        privilege_levels: Optional[Dict[str, PrivilegeLevel]] = None,
        default_desired_privilege_level: str = "",
        port: int = 22,
        auth_username: str = "",
        auth_password: str = "",
        auth_private_key: str = "",
        auth_private_key_passphrase: str = "",
        auth_strict_key: Optional[bool] = None,
        auth_bypass: Optional[bool] = None,
        timeout_socket: float = 15.0,
        timeout_transport: float = 30.0,
        timeout_ops: float = 30.0,
        comms_return_char: str = "\n",
        comms_ansi: Optional[bool] = None,
        ssh_config_file: Optional[Union[str, bool]] = None,
        ssh_known_hosts_file: Optional[Union[str, bool]] = None,
        on_init: Optional[Callable[..., Any]] = None,
        on_open: Optional[Callable[..., Any]] = None,
        on_close: Optional[Callable[..., Any]] = None,
        transport: str = "",
        transport_options: Optional[Dict[str, Any]] = None,
        channel_log: Optional[Union[str, bool]] = None,
        channel_lock: Optional[bool] = None,
        auth_secondary: str = "",
        failed_when_contains: Optional[List[str]] = None,
        textfsm_platform: str = "",
        genie_platform: str = "",
        variant: Optional[str] = None,
        **kwargs: Dict[Any, Any],
    ) -> "AsyncScrapli":
        """TODO"""
        logger.debug("AsyncScrapli factory initialized")

        if transport not in ASYNCIO_TRANSPORTS:
            raise ScrapliValueError("Use 'Scrapli' if using a synchronous transport!")

        if not isinstance(platform, str):
            raise ScrapliTypeError(f"Argument 'platform' must be 'str' got '{type(platform)}'")

        provided_kwargs = _build_provided_kwargs_dict(
            host=host,
            port=port,
            auth_username=auth_username,
            auth_password=auth_password,
            auth_private_key=auth_private_key,
            auth_private_key_passphrase=auth_private_key_passphrase,
            auth_strict_key=auth_strict_key,
            auth_bypass=auth_bypass,
            timeout_socket=timeout_socket,
            timeout_transport=timeout_transport,
            timeout_ops=timeout_ops,
            comms_return_char=comms_return_char,
            comms_ansi=comms_ansi,
            ssh_config_file=ssh_config_file,
            ssh_known_hosts_file=ssh_known_hosts_file,
            on_init=on_init,
            on_open=on_open,
            on_close=on_close,
            transport=transport,
            transport_options=transport_options,
            channel_log=channel_log,
            channel_lock=channel_lock,
            privilege_levels=privilege_levels,
            default_desired_privilege_level=default_desired_privilege_level,
            auth_secondary=auth_secondary,
            failed_when_contains=failed_when_contains,
            textfsm_platform=textfsm_platform,
            genie_platform=genie_platform,
            **kwargs,
        )

        final_driver, additional_kwargs = cls._get_driver(platform=platform, variant=variant)

        # at this point will need to merge the additional kwargs in (for community drivers),
        # ensure that kwargs passed by user supersede the ones coming from community platform
        if additional_kwargs:
            final_kwargs = {**additional_kwargs, **provided_kwargs}
        else:
            final_kwargs = provided_kwargs

        final_conn = final_driver(**final_kwargs)
        # cast the final conn to type Scrapli to appease mypy -- we know it will be a NetworkDriver
        # or GenericDriver, but thats ok =)
        final_conn = cast(AsyncScrapli, final_conn)
        return final_conn
