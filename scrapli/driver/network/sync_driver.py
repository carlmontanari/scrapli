"""scrapli.driver.network.sync_driver"""
from collections import defaultdict
from io import BytesIO
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from scrapli.driver.generic import GenericDriver
from scrapli.driver.network.base_driver import BaseNetworkDriver, PrivilegeAction, PrivilegeLevel
from scrapli.exceptions import ScrapliPrivilegeError
from scrapli.response import MultiResponse, Response


class NetworkDriver(GenericDriver, BaseNetworkDriver):
    def __init__(
        self,
        host: str,
        privilege_levels: Dict[str, PrivilegeLevel],
        default_desired_privilege_level: str,
        port: int = 22,
        auth_username: str = "",
        auth_password: str = "",
        auth_private_key: str = "",
        auth_private_key_passphrase: str = "",
        auth_strict_key: bool = True,
        auth_bypass: bool = False,
        timeout_socket: float = 15.0,
        timeout_transport: float = 30.0,
        timeout_ops: float = 30.0,
        comms_return_char: str = "\n",
        comms_ansi: bool = False,
        ssh_config_file: Union[str, bool] = False,
        ssh_known_hosts_file: Union[str, bool] = False,
        on_init: Optional[Callable[..., Any]] = None,
        on_open: Optional[Callable[..., Any]] = None,
        on_close: Optional[Callable[..., Any]] = None,
        transport: str = "system",
        transport_options: Optional[Dict[str, Any]] = None,
        channel_log: Union[str, bool, BytesIO] = False,
        channel_lock: bool = False,
        logging_uid: str = "",
        auth_secondary: str = "",
        failed_when_contains: Optional[List[str]] = None,
        textfsm_platform: str = "",
        genie_platform: str = "",
    ):
        # ensure type for comms_prompt_pattern exists before setting it in the mixin
        self.comms_prompt_pattern: str

        super().__init__(
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
            logging_uid=logging_uid,
        )

        self.auth_secondary = auth_secondary
        self.failed_when_contains = failed_when_contains or []
        self.textfsm_platform = textfsm_platform
        self.genie_platform = genie_platform

        self.privilege_levels = privilege_levels
        self.default_desired_privilege_level = default_desired_privilege_level
        self._priv_graph = defaultdict(set)
        self.update_privilege_levels()

    def _escalate(self, escalate_priv: PrivilegeLevel) -> None:
        """
        Escalate to the next privilege level up

        Args:
            escalate_priv: privilege level to escalate to

        Returns:
            None

        Raises:
            N/A

        """
        self._pre_escalate(escalate_priv=escalate_priv)

        if escalate_priv.escalate_auth is True and self.auth_secondary:
            super().send_interactive(
                interact_events=[
                    (escalate_priv.escalate, escalate_priv.escalate_prompt, False),
                    (self.auth_secondary, escalate_priv.pattern, True),
                ],
            )
        else:
            self.channel.send_input(channel_input=escalate_priv.escalate)

    def _deescalate(self, current_priv: PrivilegeLevel) -> None:
        """
        Deescalate to the next privilege level down

        Args:
            current_priv: current privilege level

        Returns:
            None

        Raises:
            N/A

        """
        self.channel.send_input(channel_input=current_priv.deescalate)

    def acquire_priv(self, desired_priv: str) -> None:
        """
        Acquire desired priv level

        Args:
            desired_priv: string name of desired privilege level see
                `scrapli.driver.<driver_category.device_type>.driver` for levels

        Returns:
            None

        Raises:
            ScrapliPrivilegeError: if desired_priv cannot be attained

        """
        self._validate_privilege_level_name(privilege_level_name=desired_priv)

        privilege_change_count = 0

        while True:
            current_prompt = self.channel.get_prompt()
            privilege_action, target_priv = self._process_acquire_priv(
                destination_priv=desired_priv,
                current_prompt=current_prompt,
            )

            if privilege_action == PrivilegeAction.NO_ACTION:
                self._current_priv_level = target_priv
                return
            if privilege_action == PrivilegeAction.DEESCALATE:
                self._deescalate(current_priv=target_priv)
            if privilege_action == PrivilegeAction.ESCALATE:
                self._escalate(escalate_priv=target_priv)

            privilege_change_count += 1
            if privilege_change_count > len(self.privilege_levels) * 2:
                msg = f"Failed to acquire requested privilege level {desired_priv}"
                raise ScrapliPrivilegeError(msg)

    def send_command(
        self,
        command: str,
        *,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        timeout_ops: Optional[float] = None,
    ) -> Response:
        """
        Send a command

        Super method will raise TypeError if anything but a string is passed here!

        Args:
            command: string to send to device in privilege exec mode
            strip_prompt: True/False strip prompt from returned output
            failed_when_contains: string or list of strings indicating failure if found in response
            timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
                the duration of the operation, value is reset to initial value after operation is
                completed

        Returns:
            Response: Scrapli Response object

        Raises:
            N/A

        """
        if self._current_priv_level.name != self.default_desired_privilege_level:
            self.acquire_priv(desired_priv=self.default_desired_privilege_level)

        if failed_when_contains is None:
            failed_when_contains = self.failed_when_contains

        response: Response = super().send_command(
            command=command,
            strip_prompt=strip_prompt,
            failed_when_contains=failed_when_contains,
            timeout_ops=timeout_ops,
        )
        self._update_response(response)

        return response

    def send_commands(
        self,
        commands: List[str],
        *,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        stop_on_failed: bool = False,
        eager: bool = False,
        timeout_ops: Optional[float] = None,
    ) -> MultiResponse:
        """
        Send multiple commands

        Super method will raise TypeError if anything but a list of strings is passed here!

        Args:
            commands: list of strings to send to device in privilege exec mode
            strip_prompt: True/False strip prompt from returned output
            failed_when_contains: string or list of strings indicating failure if found in response
            stop_on_failed: True/False stop executing commands if a command fails, returns results
                as of current execution
            eager: if eager is True we do not read until prompt is seen at each command sent to the
                channel. Do *not* use this unless you know what you are doing as it is possible that
                it can make scrapli less reliable!
            timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
                the duration of the operation, value is reset to initial value after operation is
                completed. Note that this is the timeout value PER COMMAND sent, not for the total
                of the commands being sent!

        Returns:
            MultiResponse: Scrapli MultiResponse object

        Raises:
            N/A

        """
        if self._current_priv_level.name != self.default_desired_privilege_level:
            self.acquire_priv(desired_priv=self.default_desired_privilege_level)

        if failed_when_contains is None:
            failed_when_contains = self.failed_when_contains

        responses = super().send_commands(
            commands=commands,
            strip_prompt=strip_prompt,
            failed_when_contains=failed_when_contains,
            stop_on_failed=stop_on_failed,
            eager=eager,
            timeout_ops=timeout_ops,
        )

        for response in responses:
            self._update_response(response=response)

        return responses

    def send_commands_from_file(
        self,
        file: str,
        *,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        stop_on_failed: bool = False,
        eager: bool = False,
        timeout_ops: Optional[float] = None,
    ) -> MultiResponse:
        """
        Send command(s) from file

        Args:
            file: string path to file
            strip_prompt: True/False strip prompt from returned output
            failed_when_contains: string or list of strings indicating failure if found in response
            stop_on_failed: True/False stop executing commands if a command fails, returns results
                as of current execution
            eager: if eager is True we do not read until prompt is seen at each command sent to the
                channel. Do *not* use this unless you know what you are doing as it is possible that
                it can make scrapli less reliable!
            timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
                the duration of the operation, value is reset to initial value after operation is
                completed. Note that this is the timeout value PER COMMAND sent, not for the total
                of the commands being sent!

        Returns:
            MultiResponse: Scrapli MultiResponse object

        Raises:
            N/A

        """
        if self._current_priv_level.name != self.default_desired_privilege_level:
            self.acquire_priv(desired_priv=self.default_desired_privilege_level)

        if failed_when_contains is None:
            failed_when_contains = self.failed_when_contains

        return super().send_commands_from_file(
            file=file,
            strip_prompt=strip_prompt,
            failed_when_contains=failed_when_contains,
            stop_on_failed=stop_on_failed,
            eager=eager,
            timeout_ops=timeout_ops,
        )

    def send_interactive(
        self,
        interact_events: List[Tuple[str, str, Optional[bool]]],
        *,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        privilege_level: str = "",
        timeout_ops: Optional[float] = None,
    ) -> Response:
        """
        Interact with a device with changing prompts per input.

        Used to interact with devices where prompts change per input, and where inputs may be hidden
        such as in the case of a password input. This can be used to respond to challenges from
        devices such as the confirmation for the command "clear logging" on IOSXE devices for
        example. You may have as many elements in the "interact_events" list as needed, and each
        element of that list should be a tuple of two or three elements. The first element is always
        the input to send as a string, the second should be the expected response as a string, and
        the optional third a bool for whether or not the input is "hidden" (i.e. password input)

        An example where we need this sort of capability:

        '''
        3560CX#copy flash: scp:
        Source filename []? test1.txt
        Address or name of remote host []? 172.31.254.100
        Destination username [carl]?
        Writing test1.txt
        Password:

        Password:
         Sink: C0644 639 test1.txt
        !
        639 bytes copied in 12.066 secs (53 bytes/sec)
        3560CX#
        '''

        To accomplish this we can use the following:

        '''
        interact = conn.channel.send_inputs_interact(
            [
                ("copy flash: scp:", "Source filename []?", False),
                ("test1.txt", "Address or name of remote host []?", False),
                ("172.31.254.100", "Destination username [carl]?", False),
                ("carl", "Password:", False),
                ("super_secure_password", prompt, True),
            ]
        )
        '''

        If we needed to deal with more prompts we could simply continue adding tuples to the list of
        interact "events".

        Args:
            interact_events: list of tuples containing the "interactions" with the device
                each list element must have an input and an expected response, and may have an
                optional bool for the third and final element -- the optional bool specifies if the
                input that is sent to the device is "hidden" (ex: password), if the hidden param is
                not provided it is assumed the input is "normal" (not hidden)
            failed_when_contains: list of strings that, if present in final output, represent a
                failed command/interaction
            privilege_level: name of the privilege level to operate in
            timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
                the duration of the operation, value is reset to initial value after operation is
                completed. Note that this is the timeout value PER COMMAND sent, not for the total
                of the commands being sent!

        Returns:
            Response: scrapli Response object

        Raises:
            N/A

        """
        if privilege_level:
            self._validate_privilege_level_name(privilege_level_name=privilege_level)
            resolved_privilege_level = privilege_level
        else:
            resolved_privilege_level = self.default_desired_privilege_level

        if self._current_priv_level.name != resolved_privilege_level:
            self.acquire_priv(desired_priv=resolved_privilege_level)

        if failed_when_contains is None:
            failed_when_contains = self.failed_when_contains

        # type hint is due to the TimeoutModifier wrapper returning `Any` so that we dont anger the
        # asyncio parts (which will get an awaitable not a Response returned)
        response: Response = super().send_interactive(
            interact_events=interact_events,
            failed_when_contains=failed_when_contains,
            timeout_ops=timeout_ops,
        )
        self._update_response(response=response)

        return response

    def _abort_config(self) -> None:
        """
        Abort a configuration operation/session if applicable (for config sessions like junos/iosxr)

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """

    def send_configs(
        self,
        configs: List[str],
        *,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        stop_on_failed: bool = False,
        privilege_level: str = "",
        eager: bool = False,
        timeout_ops: Optional[float] = None,
    ) -> MultiResponse:
        """
        Send configuration(s)

        Args:
            configs: list of strings to send to device in config mode
            strip_prompt: True/False strip prompt from returned output
            failed_when_contains: string or list of strings indicating failure if found in response
            stop_on_failed: True/False stop executing commands if a command fails, returns results
                as of current execution; aborts configuration session if applicable (iosxr/junos or
                eos/nxos if using a configuration session)
            privilege_level: name of configuration privilege level/type to acquire; this is platform
                dependent, so check the device driver for specifics. Examples of privilege_name
                would be "configuration_exclusive" for IOSXRDriver, or "configuration_private" for
                JunosDriver. You can also pass in a name of a configuration session such as
                "my-config-session" if you have registered a session using the
                "register_config_session" method of the EOSDriver or NXOSDriver.
            eager: if eager is True we do not read until prompt is seen at each command sent to the
                channel. Do *not* use this unless you know what you are doing as it is possible that
                it can make scrapli less reliable!
            timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
                the duration of the operation, value is reset to initial value after operation is
                completed. Note that this is the timeout value PER CONFIG sent, not for the total
                of the configs being sent!

        Returns:
            MultiResponse: Scrapli MultiResponse object

        Raises:
            N/A

        """
        resolved_privilege_level, failed_when_contains = self._pre_send_configs(
            configs=configs,
            failed_when_contains=failed_when_contains,
            privilege_level=privilege_level,
        )

        if self._current_priv_level.name != resolved_privilege_level:
            self.acquire_priv(desired_priv=resolved_privilege_level)

        responses = super().send_commands(
            commands=configs,
            strip_prompt=strip_prompt,
            failed_when_contains=failed_when_contains,
            stop_on_failed=stop_on_failed,
            eager=eager,
            timeout_ops=timeout_ops,
        )

        if responses.failed:
            self._abort_config()

        return self._post_send_configs(responses=responses)

    def send_config(
        self,
        config: str,
        *,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        stop_on_failed: bool = False,
        privilege_level: str = "",
        eager: bool = False,
        timeout_ops: Optional[float] = None,
    ) -> Response:
        """
        Send configuration string

        Args:
            config: string configuration to send to the device, supports sending multi-line strings
            strip_prompt: True/False strip prompt from returned output
            failed_when_contains: string or list of strings indicating failure if found in response
            stop_on_failed: True/False stop executing commands if a command fails, returns results
                as of current execution; aborts configuration session if applicable (iosxr/junos or
                eos/nxos if using a configuration session)
            privilege_level: name of configuration privilege level/type to acquire; this is platform
                dependent, so check the device driver for specifics. Examples of privilege_name
                would be "configuration_exclusive" for IOSXRDriver, or "configuration_private" for
                JunosDriver. You can also pass in a name of a configuration session such as
                "my-config-session" if you have registered a session using the
                "register_config_session" method of the EOSDriver or NXOSDriver.
            eager: if eager is True we do not read until prompt is seen at each command sent to the
                channel. Do *not* use this unless you know what you are doing as it is possible that
                it can make scrapli less reliable!
            timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
                the duration of the operation, value is reset to initial value after operation is
                completed. Note that this is the timeout value PER CONFIG sent, not for the total
                of the configs being sent!

        Returns:
            Response: Scrapli Response object

        Raises:
            N/A

        """
        split_config = self._pre_send_config(config=config)

        # now that we have a list of configs, just use send_configs to actually execute them
        multi_response = self.send_configs(
            configs=split_config,
            strip_prompt=strip_prompt,
            failed_when_contains=failed_when_contains,
            stop_on_failed=stop_on_failed,
            privilege_level=privilege_level,
            eager=eager,
            timeout_ops=timeout_ops,
        )
        return self._post_send_config(config=config, multi_response=multi_response)

    def send_configs_from_file(
        self,
        file: str,
        *,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        stop_on_failed: bool = False,
        privilege_level: str = "",
        eager: bool = False,
        timeout_ops: Optional[float] = None,
    ) -> MultiResponse:
        """
        Send configuration(s) from a file

        Args:
            file: string path to file
            strip_prompt: True/False strip prompt from returned output
            failed_when_contains: string or list of strings indicating failure if found in response
            stop_on_failed: True/False stop executing commands if a command fails, returns results
                as of current execution; aborts configuration session if applicable (iosxr/junos or
                eos/nxos if using a configuration session)
            privilege_level: name of configuration privilege level/type to acquire; this is platform
                dependent, so check the device driver for specifics. Examples of privilege_name
                would be "exclusive" for IOSXRDriver, "private" for JunosDriver. You can also pass
                in a name of a configuration session such as "session_mysession" if you have
                registered a session using the "register_config_session" method of the EOSDriver or
                NXOSDriver.
            eager: if eager is True we do not read until prompt is seen at each command sent to the
                channel. Do *not* use this unless you know what you are doing as it is possible that
                it can make scrapli less reliable!
            timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
                the duration of the operation, value is reset to initial value after operation is
                completed. Note that this is the timeout value PER CONFIG sent, not for the total
                of the configs being sent!

        Returns:
            MultiResponse: Scrapli MultiResponse object

        Raises:
            N/A

        """
        configs = self._pre_send_from_file(file=file, caller="send_configs_from_file")

        return self.send_configs(
            configs=configs,
            strip_prompt=strip_prompt,
            failed_when_contains=failed_when_contains,
            stop_on_failed=stop_on_failed,
            privilege_level=privilege_level,
            eager=eager,
            timeout_ops=timeout_ops,
        )
