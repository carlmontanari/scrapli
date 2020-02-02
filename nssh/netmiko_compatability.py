"""nssh.netmiko_compatibility"""
import warnings
from io import TextIOWrapper
from typing import Any, Dict, List, Union

from nssh.driver import NetworkDriver
from nssh.driver.core import IOSXEDriver
from nssh.driver.core.cisco_iosxe.driver import IOSXE_ARG_MAPPER
from nssh.helper import _textfsm_get_template, textfsm_parse

VALID_NSSH_KWARGS = {
    "host",
    "port",
    "auth_username",
    "auth_password",
    "auth_public_key",
    "auth_strict_key",
    "timeout_socket",
    "timeout_ssh",
    "timeout_ops",
    "comms_prompt_pattern",
    "comms_return_char",
    "comms_ansi",
    "session_pre_login_handler",
    "session_disable_paging",
    "ssh_config_file",
    "driver",
}


class NetmikoIOSXEDriver(IOSXEDriver):
    def __init__(self, **kwargs: Dict[str, Any]) -> None:
        """
        Create Netmiko friendly IOSXE Driver

        Args:
            N/A  # noqa

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa

        """
        auth_secondary = kwargs.pop("auth_secondary", "")
        if not isinstance(auth_secondary, str):
            raise TypeError(f"Argument 'auth_secondary' must be string, got {type(auth_secondary)}")
        super().__init__(auth_secondary, **kwargs)

    def find_prompt(self) -> str:
        """
        Patch `find_prompt` in netmiko connect handler to `get_prompt` in nssh

        Args:
            N/A  # noqa

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa

        """
        return self.get_prompt()

    def send_command(
        self, command_string: Union[str, List[str]], **kwargs: Dict[str, Any]
    ) -> Union[str, List[Any], Dict[str, Any]]:
        """
        Patch `send_command` in netmiko connect handler

        Patch and support strip_prompt, use_textfsm, and textfsm_template args. Return a single
        string to match netmiko functionality (instead of nssh result object)

        Args:
            command_string: string or list of strings to send as commands
            **kwargs: keyword arguments to support other netmiko args without blowing up

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa

        """
        provided_strip_prompt = kwargs.pop("strip_prompt", None)
        if not isinstance(provided_strip_prompt, bool):
            strip_prompt = True
        expect_string = kwargs.pop("expect_string", None)
        use_textfsm = kwargs.pop("use_textfsm", False)
        textfsm_template = kwargs.pop("textfsm_template", None)

        if expect_string:
            err = "nssh netmiko interoperability does not support expect_string!"
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

    def send_command_timing(
        self, command_string: Union[str, List[str]], **kwargs: Dict[str, Any]
    ) -> Union[str, List[Any], Dict[str, Any]]:
        """
        Patch `send_command_timing` in netmiko connect handler

        Really just a shim to send_command, nssh doesnt support/need timing mechanics -- adjust the
        timers on the connection object if needed, or adjust them on the fly in your code.

        Args:
            command_string: string or list of strings to send as commands
            **kwargs: keyword arguments to support other netmiko args without blowing up

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa

        """
        return self.send_command(command_string, **kwargs)

    def send_config_set(
        self, config_commands: Union[str, List[str]], **kwargs: Dict[str, Any]
    ) -> str:
        """
        Patch `send_config_set` in netmiko connect handler

        Note: nssh strips commands always (as it retains them in the result object anyway), so there
        is no interesting output from this as there would be in netmiko.

        Args:
            config_commands: configuration command(s) to send to device
            **kwargs: keyword arguments to support other netmiko args without blowing up

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa

        """
        provided_strip_prompt = kwargs.pop("strip_prompt", None)
        if not isinstance(provided_strip_prompt, bool):
            strip_prompt = True
        enter_config_mode = kwargs.pop("enter_config_mode", True)
        exit_config_mode = kwargs.pop("exit_config_mode", True)

        if not enter_config_mode:
            results = self.send_commands(config_commands, strip_prompt)
        elif not exit_config_mode:
            self.acquire_priv("configuration")
            results = self.channel.send_inputs(config_commands, strip_prompt)
        else:
            results = self.send_configs(config_commands, strip_prompt)
        # nssh always strips command, so there isn't typically anything useful coming back from this
        result = "\n".join([r.result for r in results])
        return result

    def send_config_from_file(self, config_file: str, **kwargs: Dict[str, Any]) -> str:
        """
        Patch `send_config_from_file` in netmiko connect handler

        Note: nssh strips commands always (as it retains them in the result object anyway), so there
        is no interesting output from this as there would be in netmiko.

        Args:
            config_file: path to text file; will send each line as a config
            **kwargs: keyword arguments to support other netmiko args without blowing up

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa

        """
        with open(config_file, "r") as f:
            config_commands = list(f)
        return self.send_config_set(config_commands, **kwargs)


NETMIKO_DEVICE_TYPE_MAPPER = {
    "cisco_ios": NetmikoIOSXEDriver,
    "cisco_xe": NetmikoIOSXEDriver,
}

NETMIKO_ARG_MAPPER = {
    "cisco_ios": IOSXE_ARG_MAPPER,
    "cisco_xe": IOSXE_ARG_MAPPER,
}


def connect_handler(auto_open: bool = True, **kwargs: Dict[str, Any]) -> NetworkDriver:
    """
    Convert netmiko style "ConnectHandler" device creation to nssh style

    Args:
        auto_open: auto open connection or not (primarily for testing purposes)
        **kwargs: keyword arguments

    Returns:
        NetworkDriver: NSSH connection object for specified device-type

    Raises:
        TypeError: if unsupported netmiko device type is provided

    """
    if kwargs["device_type"] not in NETMIKO_DEVICE_TYPE_MAPPER.keys():
        raise TypeError(f"Unsupported netmiko device type for nssh: {kwargs['device_type']}")

    netmiko_device_type = kwargs["device_type"]
    if not isinstance(netmiko_device_type, str):
        raise TypeError(f"Argument 'device_type' must be string, got {type(netmiko_device_type)}")
    driver_class = NETMIKO_DEVICE_TYPE_MAPPER.get(netmiko_device_type)
    driver_args = NETMIKO_ARG_MAPPER.get(netmiko_device_type)
    kwargs.pop("device_type")

    transformed_kwargs = transform_netmiko_kwargs(kwargs)
    final_kwargs = {**transformed_kwargs, **driver_args}

    driver = driver_class(**final_kwargs)

    if auto_open:
        driver.open()

    return driver


def transform_netmiko_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform netmiko style ConnectHandler arguments to nssh style

    Args:
        kwargs: netmiko-style ConnectHandler kwargs to transform to nssh style

    Returns:
        transformed_kwargs: converted keyword arguments

    Raises:
        N/A  # noqa

    """
    host = kwargs.pop("host", None)
    ip = kwargs.pop("ip", None)
    kwargs["host"] = host if host is not None else ip
    kwargs["port"] = kwargs.pop("port", 22)
    kwargs["setup_timeout"] = 5
    kwargs["setup_ssh_config_file"] = kwargs.pop("ssh_config_file", False)
    if "global_delay_factor" in kwargs.keys():
        kwargs["timeout_ssh"] = kwargs["global_delay_factor"] * 5000
        kwargs.pop("global_delay_factor")
    else:
        kwargs["timeout_ssh"] = 5000
    kwargs["auth_username"] = kwargs.pop("username")
    kwargs["auth_password"] = kwargs.pop("password", None)
    kwargs["auth_public_key"] = kwargs.pop("key_file", "")
    kwargs["auth_secondary"] = kwargs.pop("secret", "")
    kwargs["comms_prompt_pattern"] = ""
    kwargs["comms_operation_timeout"] = 10
    kwargs["comms_return_char"] = ""
    kwargs["session_pre_login_handler"] = ""
    kwargs["session_disable_paging"] = ""

    transformed_kwargs = {k: v for (k, v) in kwargs.items() if k in VALID_NSSH_KWARGS}

    return transformed_kwargs
