"""scrapli.factory"""
import importlib
from copy import deepcopy
from io import BytesIO
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
    default_desired_privilege_level: Optional[str],
    port: Optional[int],
    auth_username: Optional[str],
    auth_password: Optional[str],
    auth_private_key: Optional[str],
    auth_private_key_passphrase: Optional[str],
    auth_strict_key: Optional[bool],
    auth_bypass: Optional[bool],
    timeout_socket: Optional[float],
    timeout_transport: Optional[float],
    timeout_ops: Optional[float],
    comms_return_char: Optional[str],
    comms_ansi: Optional[bool],
    ssh_config_file: Optional[Union[str, bool]],
    ssh_known_hosts_file: Optional[Union[str, bool]],
    on_init: Optional[Callable[..., Any]],
    on_open: Optional[Callable[..., Any]],
    on_close: Optional[Callable[..., Any]],
    transport: Optional[str],
    transport_options: Optional[Dict[str, Any]],
    channel_log: Optional[Union[str, bool, BytesIO]],
    channel_log_mode: Optional[str],
    channel_lock: Optional[bool],
    logging_uid: Optional[str],
    auth_secondary: Optional[str],
    failed_when_contains: Optional[List[str]],
    textfsm_platform: Optional[str],
    genie_platform: Optional[str],
    **kwargs: Dict[Any, Any],
) -> Dict[str, Any]:
    r"""
    Build arguments dict based on provided inputs

    This function builds the dict of keyword args to unpack and send to the driver -- in the factory
    context this also needs to convert the arguments that have defaults that evaluate to False (i.e
    ssh_config_file which defaults to False) from None which is their default in the factory, back
    to their normal default if they are still None -OR- to whatever the user provided.

    # noqa: DAR101

    Args:
        N/A

    Returns:
        dict: dictionary with user args merged with the appropriate default options

    Raises:
        N/A

    """
    # dict of all args coming from the factories
    _provided_args: Dict[str, Any] = {
        "host": host,
        "privilege_levels": privilege_levels,
        "default_desired_privilege_level": default_desired_privilege_level,
        "port": port,
        "auth_username": auth_username,
        "auth_password": auth_password,
        "auth_private_key": auth_private_key,
        "auth_private_key_passphrase": auth_private_key_passphrase,
        "auth_strict_key": auth_strict_key,
        "auth_bypass": auth_bypass,
        "timeout_socket": timeout_socket,
        "timeout_transport": timeout_transport,
        "timeout_ops": timeout_ops,
        "comms_return_char": comms_return_char,
        "comms_ansi": comms_ansi,
        "ssh_config_file": ssh_config_file,
        "ssh_known_hosts_file": ssh_known_hosts_file,
        "on_init": on_init,
        "on_open": on_open,
        "on_close": on_close,
        "transport": transport,
        "transport_options": transport_options,
        "channel_log": channel_log,
        "channel_log_mode": channel_log_mode,
        "channel_lock": channel_lock,
        "logging_uid": logging_uid,
        "auth_secondary": auth_secondary,
        "failed_when_contains": failed_when_contains,
        "textfsm_platform": textfsm_platform,
        "genie_platform": genie_platform,
    }

    # add back in the None/False args
    _provided_args = {key: value for key, value in _provided_args.items() if value is not None}

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
        default_desired_privilege_level: Optional[str] = None,
        port: Optional[int] = None,
        auth_username: Optional[str] = None,
        auth_password: Optional[str] = None,
        auth_private_key: Optional[str] = None,
        auth_private_key_passphrase: Optional[str] = None,
        auth_strict_key: Optional[bool] = None,
        auth_bypass: Optional[bool] = None,
        timeout_socket: Optional[float] = None,
        timeout_transport: Optional[float] = None,
        timeout_ops: Optional[float] = None,
        comms_return_char: Optional[str] = None,
        comms_ansi: Optional[bool] = None,
        ssh_config_file: Optional[Union[str, bool]] = None,
        ssh_known_hosts_file: Optional[Union[str, bool]] = None,
        on_init: Optional[Callable[..., Any]] = None,
        on_open: Optional[Callable[..., Any]] = None,
        on_close: Optional[Callable[..., Any]] = None,
        transport: Optional[str] = None,
        transport_options: Optional[Dict[str, Any]] = None,
        channel_log: Optional[Union[str, bool, BytesIO]] = None,
        channel_lock: Optional[bool] = None,
        channel_log_mode: Optional[str] = None,
        logging_uid: Optional[str] = None,
        auth_secondary: Optional[str] = None,
        failed_when_contains: Optional[List[str]] = None,
        textfsm_platform: Optional[str] = None,
        genie_platform: Optional[str] = None,
        variant: Optional[str] = None,
        **kwargs: Dict[Any, Any],
    ) -> "Scrapli":
        r"""
        Scrapli Factory method for synchronous drivers

        Args:
            platform: name of the scrapli platform to return a connection object for; should be
                one of the "core" platforms or a valid community platform name
            host: host ip/name to connect to
            port: port to connect to
            auth_username: username for authentication
            auth_private_key: path to private key for authentication
            auth_private_key_passphrase: passphrase for decrypting ssh key if necessary
            auth_password: password for authentication
            auth_strict_key: strict host checking or not
            auth_bypass: bypass "in channel" authentication -- only supported with telnet,
                asynctelnet, and system transport plugins
            timeout_socket: timeout for establishing socket/initial connection in seconds
            timeout_transport: timeout for ssh|telnet transport in seconds
            timeout_ops: timeout for ssh channel operations
            comms_return_char: character to use to send returns to host
            comms_ansi: True/False strip comms_ansi characters from output, generally the default
                value of False should be fine
            ssh_config_file: string to path for ssh config file, True to use default ssh config file
                or False to ignore default ssh config file
            ssh_known_hosts_file: string to path for ssh known hosts file, True to use default known
                file locations. Only applicable/needed if `auth_strict_key` is set to True
            on_init: callable that accepts the class instance as its only argument. this callable,
                if provided, is executed as the last step of object instantiation -- its purpose is
                primarily to provide a mechanism for scrapli community platforms to have an easy way
                to modify initialization arguments/object attributes without needing to create a
                class that extends the driver, instead allowing the community platforms to simply
                build from the GenericDriver or NetworkDriver classes, and pass this callable to do
                things such as appending to a username (looking at you RouterOS!!). Note that this
                is *always* a synchronous function (even for asyncio drivers)!
            on_open: callable that accepts the class instance as its only argument. this callable,
                if provided, is executed immediately after authentication is completed. Common use
                cases for this callable would be to disable paging or accept any kind of banner
                message that prompts a user upon connection
            on_close: callable that accepts the class instance as its only argument. this callable,
                if provided, is executed immediately prior to closing the underlying transport.
                Common use cases for this callable would be to save configurations prior to exiting,
                or to logout properly to free up vtys or similar
            transport: name of the transport plugin to use for the actual telnet/ssh/netconf
                connection. Available "core" transports are:
                    - system
                    - telnet
                    - asynctelnet
                    - ssh2
                    - paramiko
                    - asyncssh
                Please see relevant transport plugin section for details. Additionally third party
                transport plugins may be available.
            transport_options: dictionary of options to pass to selected transport class; see
                docs for given transport class for details of what to pass here
            channel_lock: True/False to lock the channel (threading.Lock/asyncio.Lock) during
                any channel operations, defaults to False
            channel_log: True/False or a string path to a file of where to write out channel logs --
                these are not "logs" in the normal logging module sense, but only the output that is
                read from the channel. In other words, the output of the channel log should look
                similar to what you would see as a human connecting to a device
            channel_log_mode: "write"|"append", all other values will raise ValueError,
                does what it sounds like it should by setting the channel log to the provided mode
            logging_uid: unique identifier (string) to associate to log messages; useful if you have
                multiple connections to the same device (i.e. one console, one ssh, or one to each
                supervisor module, etc.)
            failed_when_contains: list of strings indicating command/config failure
            textfsm_platform: string to use to fetch ntc-templates templates for textfsm parsing
            genie_platform: string to use to fetch genie parser templates
            privilege_levels: optional user provided privilege levels, if left None will default to
                scrapli standard privilege levels
            default_desired_privilege_level: string of name of default desired priv, this is the
                priv level that is generally used to disable paging/set terminal width and things
                like that upon first login, and is also the priv level scrapli will try to acquire
                for normal "command" operations (`send_command`, `send_commands`)
            auth_secondary: password to use for secondary authentication (enable)
            failed_when_contains: List of strings that indicate a command/config has failed
            variant: name of the community platform variant if desired
            **kwargs: should be unused, but here to accept any additional kwargs from users

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
            channel_log_mode=channel_log_mode,
            channel_lock=channel_lock,
            logging_uid=logging_uid,
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
            platform_details=platform_details, variant=variant, _async=True
        )

        return final_driver, final_platform_kwargs

    @classmethod
    def _get_driver(
        cls, platform: str, variant: Optional[str]
    ) -> Tuple[Union[Type[AsyncNetworkDriver], Type[AsyncGenericDriver]], Dict[str, Any]]:
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
        default_desired_privilege_level: Optional[str] = None,
        port: Optional[int] = None,
        auth_username: Optional[str] = None,
        auth_password: Optional[str] = None,
        auth_private_key: Optional[str] = None,
        auth_private_key_passphrase: Optional[str] = None,
        auth_strict_key: Optional[bool] = None,
        auth_bypass: Optional[bool] = None,
        timeout_socket: Optional[float] = None,
        timeout_transport: Optional[float] = None,
        timeout_ops: Optional[float] = None,
        comms_return_char: Optional[str] = None,
        comms_ansi: Optional[bool] = None,
        ssh_config_file: Optional[Union[str, bool]] = None,
        ssh_known_hosts_file: Optional[Union[str, bool]] = None,
        on_init: Optional[Callable[..., Any]] = None,
        on_open: Optional[Callable[..., Any]] = None,
        on_close: Optional[Callable[..., Any]] = None,
        transport: Optional[str] = None,
        transport_options: Optional[Dict[str, Any]] = None,
        channel_log: Optional[Union[str, bool, BytesIO]] = None,
        channel_log_mode: Optional[str] = None,
        channel_lock: Optional[bool] = None,
        logging_uid: Optional[str] = None,
        auth_secondary: Optional[str] = None,
        failed_when_contains: Optional[List[str]] = None,
        textfsm_platform: Optional[str] = None,
        genie_platform: Optional[str] = None,
        variant: Optional[str] = None,
        **kwargs: Dict[Any, Any],
    ) -> "AsyncScrapli":
        r"""
        Scrapli Factory method for asynchronous drivers

        Args:
            platform: name of the scrapli platform to return a connection object for; should be
                one of the "core" platforms or a valid community platform name
            host: host ip/name to connect to
            port: port to connect to
            auth_username: username for authentication
            auth_private_key: path to private key for authentication
            auth_private_key_passphrase: passphrase for decrypting ssh key if necessary
            auth_password: password for authentication
            auth_strict_key: strict host checking or not
            auth_bypass: bypass "in channel" authentication -- only supported with telnet,
                asynctelnet, and system transport plugins
            timeout_socket: timeout for establishing socket/initial connection in seconds
            timeout_transport: timeout for ssh|telnet transport in seconds
            timeout_ops: timeout for ssh channel operations
            comms_return_char: character to use to send returns to host
            comms_ansi: True/False strip comms_ansi characters from output, generally the default
                value of False should be fine
            ssh_config_file: string to path for ssh config file, True to use default ssh config file
                or False to ignore default ssh config file
            ssh_known_hosts_file: string to path for ssh known hosts file, True to use default known
                file locations. Only applicable/needed if `auth_strict_key` is set to True
            on_init: callable that accepts the class instance as its only argument. this callable,
                if provided, is executed as the last step of object instantiation -- its purpose is
                primarily to provide a mechanism for scrapli community platforms to have an easy way
                to modify initialization arguments/object attributes without needing to create a
                class that extends the driver, instead allowing the community platforms to simply
                build from the GenericDriver or NetworkDriver classes, and pass this callable to do
                things such as appending to a username (looking at you RouterOS!!). Note that this
                is *always* a synchronous function (even for asyncio drivers)!
            on_open: callable that accepts the class instance as its only argument. this callable,
                if provided, is executed immediately after authentication is completed. Common use
                cases for this callable would be to disable paging or accept any kind of banner
                message that prompts a user upon connection
            on_close: callable that accepts the class instance as its only argument. this callable,
                if provided, is executed immediately prior to closing the underlying transport.
                Common use cases for this callable would be to save configurations prior to exiting,
                or to logout properly to free up vtys or similar
            transport: name of the transport plugin to use for the actual telnet/ssh/netconf
                connection. Available "core" transports are:
                    - system
                    - telnet
                    - asynctelnet
                    - ssh2
                    - paramiko
                    - asyncssh
                Please see relevant transport plugin section for details. Additionally third party
                transport plugins may be available.
            transport_options: dictionary of options to pass to selected transport class; see
                docs for given transport class for details of what to pass here
            channel_lock: True/False to lock the channel (threading.Lock/asyncio.Lock) during
                any channel operations, defaults to False
            channel_log: True/False or a string path to a file of where to write out channel logs --
                these are not "logs" in the normal logging module sense, but only the output that is
                read from the channel. In other words, the output of the channel log should look
                similar to what you would see as a human connecting to a device
            channel_log_mode: "write"|"append", all other values will raise ValueError,
                does what it sounds like it should by setting the channel log to the provided mode
            logging_uid: unique identifier (string) to associate to log messages; useful if you have
                multiple connections to the same device (i.e. one console, one ssh, or one to each
                supervisor module, etc.)
            failed_when_contains: list of strings indicating command/config failure
            textfsm_platform: string to use to fetch ntc-templates templates for textfsm parsing
            genie_platform: string to use to fetch genie parser templates
            privilege_levels: optional user provided privilege levels, if left None will default to
                scrapli standard privilege levels
            default_desired_privilege_level: string of name of default desired priv, this is the
                priv level that is generally used to disable paging/set terminal width and things
                like that upon first login, and is also the priv level scrapli will try to acquire
                for normal "command" operations (`send_command`, `send_commands`)
            auth_secondary: password to use for secondary authentication (enable)
            failed_when_contains: List of strings that indicate a command/config has failed
            variant: name of the community platform variant if desired
            **kwargs: should be unused, but here to accept any additional kwargs from users

        Returns:
            final_driver: asynchronous driver class for provided driver

        Raises:
            ScrapliValueError: if provided transport is asyncio
            ScrapliTypeError: if `platform` not in keyword arguments

        """
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
            channel_log_mode=channel_log_mode,
            channel_lock=channel_lock,
            logging_uid=logging_uid,
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
