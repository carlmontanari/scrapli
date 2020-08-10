"""scrapli.driver.network_driver"""
from collections import UserList
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from scrapli.driver.base_network_driver import NetworkDriverBase, PrivilegeAction, PrivilegeLevel
from scrapli.driver.generic_driver import GenericDriver
from scrapli.exceptions import CouldNotAcquirePrivLevel
from scrapli.response import MultiResponse, Response

if TYPE_CHECKING:
    ScrapliMultiResponse = UserList[Response]  # pylint:  disable=E1136; # pragma:  no cover
else:
    ScrapliMultiResponse = UserList


class NetworkDriver(GenericDriver, NetworkDriverBase):
    def __init__(
        self,
        privilege_levels: Dict[str, PrivilegeLevel],
        default_desired_privilege_level: str,
        auth_secondary: str = "",
        failed_when_contains: Optional[List[str]] = None,
        textfsm_platform: str = "",
        genie_platform: str = "",
        **kwargs: Any,
    ):
        """
        BaseNetworkDriver Object

        Args:
            privilege_levels: Dict of privilege levels for a given platform
            default_desired_privilege_level: string of name of default desired priv, this is the
                priv level that is generally used to disable paging/set terminal width and things
                like that upon first login, and is also the priv level scrapli will try to acquire
                for normal "command" operations (`send_command`, `send_commands`)
            auth_secondary: password to use for secondary authentication (enable)
            failed_when_contains: list of strings that indicate a command/configuration has failed
            textfsm_platform: string name of platform to use for textfsm parsing
            genie_platform: string name of platform to use for genie parsing
            **kwargs: keyword args to pass to inherited class(es)

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self._check_kwargs_comms_prompt_pattern(kwargs=kwargs)

        self.auth_secondary = auth_secondary
        self.privilege_levels = privilege_levels
        self._priv_map = {}
        self.default_desired_privilege_level = default_desired_privilege_level
        self.update_privilege_levels(update_channel=False)

        self.textfsm_platform = textfsm_platform
        self.genie_platform = genie_platform
        self.failed_when_contains = failed_when_contains or []

        super().__init__(comms_prompt_pattern=self.comms_prompt_pattern, **kwargs)

    def _escalate(self, escalate_priv: PrivilegeLevel) -> None:
        """
        Escalate to the next privilege level up

        Args:
            escalate_priv: privilege level to escalate to

        Returns:
            N/A  # noqa: DAR202

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
            N/A  # noqa: DAR202

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
            N/A  # noqa: DAR202

        Raises:
            CouldNotAcquirePrivLevel: if desired_priv cannot be attained

        """
        resolved_priv, map_to_desired_priv = self._pre_acquire_priv(desired_priv=desired_priv)

        privilege_change_count = 0
        while True:
            current_prompt = self.channel.get_prompt()
            privilege_action, target_priv = self._process_acquire_priv(
                resolved_priv=resolved_priv,
                map_to_desired_priv=map_to_desired_priv,
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
                msg = f"Failed to acquire requested privilege level {resolved_priv}"
                raise CouldNotAcquirePrivLevel(msg)

    def send_command(
        self,
        command: str,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        *,
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
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        stop_on_failed: bool = False,
        *,
        timeout_ops: Optional[float] = None,
    ) -> ScrapliMultiResponse:
        """
        Send multiple commands

        Super method will raise TypeError if anything but a list of strings is passed here!

        Args:
            commands: list of strings to send to device in privilege exec mode
            strip_prompt: True/False strip prompt from returned output
            failed_when_contains: string or list of strings indicating failure if found in response
            stop_on_failed: True/False stop executing commands if a command fails, returns results
                as of current execution
            timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
                the duration of the operation, value is reset to initial value after operation is
                completed. Note that this is the timeout value PER COMMAND sent, not for the total
                of the commands being sent!

        Returns:
            ScrapliMultiResponse: Scrapli MultiResponse object

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
            timeout_ops=timeout_ops,
        )

        for response in responses:
            self._update_response(response=response)

        return responses

    def send_commands_from_file(
        self,
        file: str,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        stop_on_failed: bool = False,
        *,
        timeout_ops: Optional[float] = None,
    ) -> ScrapliMultiResponse:
        """
        Send command(s) from file

        Args:
            file: string path to file
            strip_prompt: True/False strip prompt from returned output
            failed_when_contains: string or list of strings indicating failure if found in response
            stop_on_failed: True/False stop executing commands if a command fails, returns results
                as of current execution
            timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
                the duration of the operation, value is reset to initial value after operation is
                completed. Note that this is the timeout value PER COMMAND sent, not for the total
                of the commands being sent!

        Returns:
            ScrapliMultiResponse: Scrapli MultiResponse object

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
            timeout_ops=timeout_ops,
        )

    def send_interactive(
        self,
        interact_events: List[Tuple[str, str, Optional[bool]]],
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        privilege_level: str = "",
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

        ```
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
        ```

        To accomplish this we can use the following:

        ```
        interact = conn.channel.send_inputs_interact(
            [
                ("copy flash: scp:", "Source filename []?", False),
                ("test1.txt", "Address or name of remote host []?", False),
                ("172.31.254.100", "Destination username [carl]?", False),
                ("carl", "Password:", False),
                ("super_secure_password", prompt, True),
            ]
        )
        ```

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

        Returns:
            Response: scrapli Response object

        Raises:
            N/A

        """
        if privilege_level:
            resolved_privilege_level = self._get_privilege_level_name(
                requested_priv=privilege_level
            )
        else:
            resolved_privilege_level = self.default_desired_privilege_level

        if self._current_priv_level.name != resolved_privilege_level:
            self.acquire_priv(desired_priv=resolved_privilege_level)
        response = super().send_interactive(
            interact_events=interact_events, failed_when_contains=failed_when_contains
        )
        self._update_response(response=response)

        return response

    def _abort_config(self) -> None:
        """
        Abort a configuration operation/session if applicable (for config sessions like junos/iosxr)

        Args:
            N/A

        Returns:
            N/A:  # noqa: DAR202

        Raises:
            N/A

        """

    def send_config(
        self,
        config: str,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        stop_on_failed: bool = False,
        privilege_level: str = "",
        *,
        timeout_ops: Optional[float] = None,
    ) -> Response:
        """
        Send configuration(s)

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
            timeout_ops=timeout_ops,
        )
        return self._post_send_config(config=config, multi_response=multi_response)

    def send_configs(
        self,
        configs: List[str],
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        stop_on_failed: bool = False,
        privilege_level: str = "",
        *,
        timeout_ops: Optional[float] = None,
    ) -> ScrapliMultiResponse:
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
            timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
                the duration of the operation, value is reset to initial value after operation is
                completed. Note that this is the timeout value PER CONFIG sent, not for the total
                of the configs being sent!

        Returns:
            ScrapliMultiResponse: Scrapli MultiResponse object

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

        responses = MultiResponse()
        _failed_during_execution = False
        for config in configs:
            response = super().send_command(
                command=config,
                strip_prompt=strip_prompt,
                failed_when_contains=failed_when_contains,
                timeout_ops=timeout_ops,
            )
            responses.append(response)
            if response.failed is True:
                _failed_during_execution = True
                if stop_on_failed is True:
                    break

        if _failed_during_execution is True:
            self._abort_config()

        return self._post_send_configs(responses=responses)

    def send_configs_from_file(
        self,
        file: str,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        stop_on_failed: bool = False,
        privilege_level: str = "",
        *,
        timeout_ops: Optional[float] = None,
    ) -> ScrapliMultiResponse:
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
            timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
                the duration of the operation, value is reset to initial value after operation is
                completed. Note that this is the timeout value PER CONFIG sent, not for the total
                of the configs being sent!

        Returns:
            ScrapliMultiResponse: Scrapli MultiResponse object

        Raises:
            N/A

        """
        configs = self._pre_send_configs_from_file(file=file)

        return self.send_configs(
            configs=configs,
            strip_prompt=strip_prompt,
            failed_when_contains=failed_when_contains,
            stop_on_failed=stop_on_failed,
            privilege_level=privilege_level,
            timeout_ops=timeout_ops,
        )
