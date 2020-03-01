"""scrapli.netmiko_compatibility"""
import warnings
from typing import Any, Dict, List, Union

from scrapli.driver import NetworkDriver
from scrapli.driver.core.arista_eos.driver import EOS_ARG_MAPPER, EOSDriver
from scrapli.driver.core.cisco_iosxe.driver import IOSXE_ARG_MAPPER, IOSXEDriver
from scrapli.driver.core.cisco_iosxr.driver import IOSXR_ARG_MAPPER, IOSXRDriver
from scrapli.driver.core.cisco_nxos.driver import NXOS_ARG_MAPPER, NXOSDriver
from scrapli.driver.core.juniper_junos.driver import JUNOS_ARG_MAPPER, JunosDriver

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


class NetmikoNetworkDriver:
    def __init__(self, scrapli_driver: NetworkDriver) -> None:
        """
        Scrapli NetmikoNetworkDriver

        Args:
            scrapli_driver: string command to send to device


        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.scrapli_driver = scrapli_driver

    def open(self) -> None:
        """
        Open scrapli connection

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.scrapli_driver.open()

    def find_prompt(self) -> str:
        """
        Scrapli netmiko find_prompt

        Map netmiko find_prompt to scrapli get_prompt

        Args:
            N/A

        Returns:
            str: string representing the device prompt

        Raises:
            N/A

        """
        return self.scrapli_driver.get_prompt()

    def send_command(
        self, command_string: str, strip_prompt: bool = True, **kwargs: Dict[str, Any]
    ) -> Union[str, List[Any], Dict[str, Any]]:
        """
        Scrapli netmiko send_command

        Map some netmiko send_command args into scrapli; used for allowing folks to test scrapli
        more easily if they are already using netmiko

        Args:
            command_string: string command to send to device
            strip_prompt: True/False strip prompt -- same in scrapli as in netmiko
            kwargs: allows for not blowing up will letting users pass in netmiko args that can
                safely be ignored

        Returns:
            result: text result or structured result if `use_textfsm` is true and parsing successful

        Raises:
            N/A

        """
        expect_string = kwargs.pop("expect_string", None)
        use_textfsm = kwargs.pop("use_textfsm", False)

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

        scrapli_result = self.scrapli_driver.send_command(command, strip_prompt=strip_prompt)

        if use_textfsm:
            structured_result = scrapli_result.textfsm_parse_output()
            if structured_result:
                return structured_result

        return scrapli_result.result

    def send_command_timing(
        self, command_string: str, strip_prompt: bool = True, **kwargs: Dict[str, Any]
    ) -> Union[str, List[Any], Dict[str, Any]]:
        """
        Scrapli netmiko send_command_timing

        Map some netmiko send_command args into scrapli; used for allowing folks to test scrapli
        more easily if they are already using netmiko

        Args:
            command_string: string command to send to device
            strip_prompt: True/False strip prompt -- same in scrapli as in netmiko
            kwargs: allows for not blowing up will letting users pass in netmiko args that can
                safely be ignored

        Returns:
            result: text result or structured result if `use_textfsm` is true and parsing successful

        Raises:
            N/A

        """
        if isinstance(command_string, list):
            err = "netmiko does not support sending list of commands, using only the first command!"
            msg = f"***** {err} {'*' * (80 - len(err))}"
            fix = f"To resolve this issue, use native or driver mode with `send_inputs` method."
            warning = "\n" + msg + "\n" + fix + "\n" + msg
            warnings.warn(warning)
            command = command_string[0]
        else:
            command = command_string

        return self.send_command(command, strip_prompt=strip_prompt, **kwargs)

    def send_config_set(
        self, config_commands: Union[str, List[str]], **kwargs: Dict[str, Any]
    ) -> str:
        """
        Scrapli netmiko send_config_set

        Map some netmiko send_config_set args into scrapli; used for allowing folks to test scrapli
        more easily if they are already using netmiko

        Args:
            config_commands: string or list of strings of config commands to send
            kwargs: allows for not blowing up will letting users pass in netmiko args that can
                safely be ignored

        Returns:
            str: text result or structured result if `use_textfsm` is true and parsing successful

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
            if isinstance(config_commands, str):
                configs = [config_commands]
            else:
                configs = config_commands
            results = self.scrapli_driver.send_commands(configs, strip_prompt)
        elif not exit_config_mode:
            self.scrapli_driver.acquire_priv("configuration")
            results = self.scrapli_driver.channel.send_inputs(config_commands, strip_prompt)
        else:
            results = self.scrapli_driver.send_configs(config_commands, strip_prompt)
        # scrapli always strips command, so there isn't typically anything useful coming back
        result = "\n".join([r.result for r in results])
        return result


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
    scrapli_driver = driver_class(auth_strict_key=False, **final_kwargs)

    if auto_open:
        scrapli_driver.driver.open()

    netmiko_driver = NetmikoNetworkDriver(scrapli_driver)

    return netmiko_driver


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
    kwargs["ssh_config_file"] = kwargs.pop("ssh_config_file", False)
    if "global_delay_factor" in kwargs.keys():
        kwargs["timeout_socket"] = kwargs["global_delay_factor"] * 5
        kwargs["timeout_transport"] = kwargs["global_delay_factor"] * 5000
        kwargs["timeout_ops"] = kwargs["global_delay_factor"] * 10
        kwargs.pop("global_delay_factor")
    kwargs["auth_username"] = kwargs.pop("username")
    kwargs["auth_password"] = kwargs.pop("password", None)
    kwargs["auth_public_key"] = kwargs.pop("key_file", "")
    kwargs["auth_secondary"] = kwargs.pop("secret", "")

    transformed_kwargs = {k: v for (k, v) in kwargs.items() if k in VALID_SCRAPLI_KWARGS}

    return transformed_kwargs
