"""scrapli.netmiko_compatibility"""
import types
import warnings
from io import TextIOWrapper
from typing import Any, Dict, List, Union

from scrapli.driver import NetworkDriver
from scrapli.driver.core.arista_eos.driver import EOS_ARG_MAPPER, EOSDriver
from scrapli.driver.core.cisco_iosxe.driver import IOSXE_ARG_MAPPER, IOSXEDriver
from scrapli.driver.core.cisco_iosxr.driver import IOSXR_ARG_MAPPER, IOSXRDriver
from scrapli.driver.core.cisco_nxos.driver import NXOS_ARG_MAPPER, NXOSDriver
from scrapli.driver.core.juniper_junos.driver import JUNOS_ARG_MAPPER, JunosDriver
from scrapli.helper import _textfsm_get_template, textfsm_parse

VALID_SCRAPLI_KWARGS = {
    "host",
    "port",
    "auth_username",
    "auth_password",
    "auth_public_key",
    "auth_strict_key",
    "timeout_socket",
    "timeout_transport",
    "timeout_ops",
    "comms_prompt_pattern",
    "comms_return_char",
    "comms_ansi",
    "session_pre_login_handler",
    "session_disable_paging",
    "ssh_config_file",
    "driver",
}


NETMIKO_DEVICE_TYPE_MAPPER = {
    "arista_eos": {"driver": EOSDriver, "arg_mapper": EOS_ARG_MAPPER},
    "cisco_ios": {"driver": IOSXEDriver, "arg_mapper": IOSXE_ARG_MAPPER},
    "cisco_xe": {"driver": IOSXEDriver, "arg_mapper": IOSXE_ARG_MAPPER},
    "cisco_xr": {"driver": IOSXRDriver, "arg_mapper": IOSXR_ARG_MAPPER},
    "cisco_nxos": {"driver": NXOSDriver, "arg_mapper": NXOS_ARG_MAPPER},
    "juniper_junos": {"driver": JunosDriver, "arg_mapper": JUNOS_ARG_MAPPER},
}


class NetmikoNetworkDriver(NetworkDriver):
    def send_command(
        self: NetworkDriver, command_string: Union[str, List[str]], **kwargs: Dict[str, Any]
    ) -> Union[str, List[Any], Dict[str, Any]]:
        """
        Netmiko style NetworkDriver with send_command method to appease typing

        Patch `send_command_timing` in netmiko connect handler

        Really just a shim to send_command, scrapli doesnt support/need timing mechanics -- adjust
        the timers on the connection object if needed, or adjust them on the fly in your code.

        Args:
            command_string: string or list of strings to send as commands
            **kwargs: keyword arguments to support other netmiko args without blowing up

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """


def connect_handler(auto_open: bool = True, **kwargs: Dict[str, Any]) -> NetmikoNetworkDriver:
    """
    Convert netmiko style "ConnectHandler" device creation to scrapli style

    Args:
        auto_open: auto open connection or not (primarily for testing purposes)
        **kwargs: keyword arguments

    Returns:
        NetmikoNetworkDriver: Scrape connection object for specified device-type

    Raises:
        TypeError: if unsupported netmiko device type is provided

    """
    netmiko_device_type = kwargs["device_type"]
    if not isinstance(netmiko_device_type, str):
        raise TypeError(f"Argument 'device_type' must be string, got {type(netmiko_device_type)}")

    if netmiko_device_type not in NETMIKO_DEVICE_TYPE_MAPPER.keys():
        raise TypeError(f"Unsupported netmiko device type for scrapli: {kwargs['device_type']}")

    driver_class = NETMIKO_DEVICE_TYPE_MAPPER.get(netmiko_device_type).get("driver")
    driver_args = NETMIKO_DEVICE_TYPE_MAPPER.get(netmiko_device_type).get("arg_mapper")

    kwargs.pop("device_type")
    transformed_kwargs = transform_netmiko_kwargs(kwargs)

    final_kwargs = {**transformed_kwargs, **driver_args}
    driver = driver_class(**final_kwargs)

    if auto_open:
        driver.open()

    # Below is a dirty way to patch netmiko methods into scrapli without having a factory function
    # and a million classes... as this is just for testing interoperability we'll let this slide...
    driver.find_prompt = types.MethodType(netmiko_find_prompt, driver)
    driver.send_command = types.MethodType(netmiko_send_command, driver)
    driver.send_command_timing = types.MethodType(netmiko_send_command_timing, driver)
    driver.send_config_set = types.MethodType(netmiko_send_config_set, driver)

    return driver


def transform_netmiko_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform netmiko style ConnectHandler arguments to scrapli style

    Args:
        kwargs: netmiko-style ConnectHandler kwargs to transform to scrapli style

    Returns:
        transformed_kwargs: converted keyword arguments

    Raises:
        N/A

    """
    host = kwargs.pop("host", None)
    ip = kwargs.pop("ip", None)
    kwargs["host"] = host if host is not None else ip
    kwargs["port"] = kwargs.pop("port", 22)
    kwargs["setup_timeout"] = 5
    kwargs["setup_ssh_config_file"] = kwargs.pop("ssh_config_file", False)
    if "global_delay_factor" in kwargs.keys():
        kwargs["timeout_socket"] = kwargs["global_delay_factor"] * 5
        kwargs["timeout_transport"] = kwargs["global_delay_factor"] * 5000
        kwargs["timeout_ops"] = kwargs["global_delay_factor"] * 10
        kwargs.pop("global_delay_factor")
    else:
        kwargs["timeout_transport"] = 5000
    kwargs["auth_username"] = kwargs.pop("username")
    kwargs["auth_password"] = kwargs.pop("password", None)
    kwargs["auth_public_key"] = kwargs.pop("key_file", "")
    kwargs["auth_secondary"] = kwargs.pop("secret", "")
    kwargs["comms_prompt_pattern"] = ""
    kwargs["comms_operation_timeout"] = 10
    kwargs["comms_return_char"] = ""
    kwargs["session_pre_login_handler"] = ""
    kwargs["session_disable_paging"] = ""

    transformed_kwargs = {k: v for (k, v) in kwargs.items() if k in VALID_SCRAPLI_KWARGS}

    return transformed_kwargs


def netmiko_find_prompt(self: NetmikoNetworkDriver) -> str:
    """
    Patch `find_prompt` in netmiko connect handler to `get_prompt` in scrapli

    Args:
        self: NetmikoNetworkDriver object -- `self` as this gets shoe-horned into NetworkDriver via
            types MethodType

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A

    """
    return self.get_prompt()


def netmiko_send_command(
    self: NetmikoNetworkDriver, command_string: Union[str, List[str]], **kwargs: Dict[str, Any]
) -> Union[str, List[Any], Dict[str, Any]]:
    """
    Patch `send_command` in netmiko connect handler

    Patch and support strip_prompt, use_textfsm, and textfsm_template args. Return a single
    string to match netmiko functionality (instead of scrapli result object)

    Args:
        self: NetmikoNetworkDriver object -- `self` as this gets shoe-horned into NetworkDriver via
            types MethodType
        command_string: string or list of strings to send as commands
        **kwargs: keyword arguments to support other netmiko args without blowing up

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A

    """
    provided_strip_prompt = kwargs.pop("strip_prompt", None)
    if not isinstance(provided_strip_prompt, bool):
        strip_prompt = True
    else:
        strip_prompt = provided_strip_prompt
    expect_string = kwargs.pop("expect_string", None)
    use_textfsm = kwargs.pop("use_textfsm", False)
    textfsm_template = kwargs.pop("textfsm_template", None)

    if expect_string:
        err = "scrapli netmiko interoperability does not support expect_string!"
        msg = f"***** {err} {'*' * (80 - len(err))}"
        fix = (
            f"To resolve this issue, use native or driver mode with `send_inputs_interact` "
            " method."
        )
        warning = "\n" + msg + "\n" + fix + "\n" + msg
        warnings.warn(warning)

    if isinstance(command_string, list):
        err = "netmiko does not support sending list of commands, using only the first command!"
        msg = f"***** {err} {'*' * (80 - len(err))}"
        fix = f"To resolve this issue, use native or driver mode with `send_inputs` method."
        warning = "\n" + msg + "\n" + fix + "\n" + msg
        warnings.warn(warning)
        command = command_string[0]
    else:
        command = command_string

    results = self.send_commands(command, strip_prompt)
    # netmiko supports sending single commands only and has no "result" object
    # peel out just result
    result = results[0].result

    if use_textfsm:
        structured_result = None
        if isinstance(textfsm_template, (str, TextIOWrapper)):
            structured_result = textfsm_parse(textfsm_template, result)
        else:
            gathered_textfsm_template = _textfsm_get_template(self.textfsm_platform, command)
            if isinstance(gathered_textfsm_template, TextIOWrapper):
                structured_result = textfsm_parse(gathered_textfsm_template, result)
        # netmiko returns unstructured data if no structured data was generated
        if structured_result:
            return structured_result
    return result


def netmiko_send_command_timing(
    self: NetmikoNetworkDriver, command_string: Union[str, List[str]], **kwargs: Dict[str, Any]
) -> Union[str, List[Any], Dict[str, Any]]:
    """
    Patch `send_command_timing` in netmiko connect handler

    Really just a shim to send_command, scrapli doesnt support/need timing mechanics -- adjust the
    timers on the connection object if needed, or adjust them on the fly in your code.

    Args:
        self: NetmikoNetworkDriver object -- `self` as this gets shoe-horned into NetworkDriver via
            types MethodType
        command_string: string or list of strings to send as commands
        **kwargs: keyword arguments to support other netmiko args without blowing up

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A

    """
    return self.send_command(command_string, **kwargs)


def netmiko_send_config_set(
    self: NetmikoNetworkDriver, config_commands: Union[str, List[str]], **kwargs: Dict[str, Any]
) -> str:
    """
    Patch `send_config_set` in netmiko connect handler

    Note: scrapli strips commands always (as it retains them in the result object anyway), so there
    is no interesting output from this as there would be in netmiko.

    Args:
        self: NetmikoNetworkDriver object -- `self` as this gets shoe-horned into NetworkDriver via
            types MethodType
        config_commands: configuration command(s) to send to device
        **kwargs: keyword arguments to support other netmiko args without blowing up

    Returns:
        N/A  # noqa: DAR202

    Raises:
        N/A

    """
    provided_strip_prompt = kwargs.pop("strip_prompt", None)
    if not isinstance(provided_strip_prompt, bool):
        strip_prompt = True
    else:
        strip_prompt = provided_strip_prompt
    enter_config_mode = kwargs.pop("enter_config_mode", True)
    exit_config_mode = kwargs.pop("exit_config_mode", True)

    if not enter_config_mode:
        results = self.send_commands(config_commands, strip_prompt)
    elif not exit_config_mode:
        self.acquire_priv("configuration")
        results = self.channel.send_inputs(config_commands, strip_prompt)
    else:
        results = self.send_configs(config_commands, strip_prompt)
    # scrapli always strips command, so there isn't typically anything useful coming back from this
    result = "\n".join([r.result for r in results])
    return result
