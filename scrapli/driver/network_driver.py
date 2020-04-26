"""scrapli.driver.network_driver"""
import logging
import re
import warnings
from abc import ABC, abstractmethod
from collections import namedtuple
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple, Union

from scrapli.driver.generic_driver import GenericDriver
from scrapli.exceptions import UnknownPrivLevel
from scrapli.helper import get_prompt_pattern, resolve_file
from scrapli.response import Response

PrivilegeLevel = namedtuple(
    "PrivilegeLevel",
    "pattern "  # regex pattern for this priv level
    "name "  # friendly name of the priv level
    "previous_priv "  # name of the "lower"/"previous" priv level
    "deescalate "  # how to deescalate *from* this priv level (to the lower/previous priv)
    "escalate "  # how to escalate *to* this priv level (from the lower/previous priv)
    "escalate_auth "  # is there auth to get *to* this priv level
    "escalate_prompt ",  # what is the prompt to get *to* this priv level
)

NoPrivLevel = PrivilegeLevel("", "", "", "", "", "", "")


PRIVS: Dict[str, PrivilegeLevel] = {}

LOG = logging.getLogger("driver")


class NetworkDriver(GenericDriver, ABC):
    @abstractmethod
    def __init__(
        self,
        privilege_levels: Dict[str, PrivilegeLevel],
        default_desired_privilege_level: str,
        auth_secondary: str = "",
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
            **kwargs: keyword args to pass to inherited class(es)

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.privilege_levels = privilege_levels
        self.default_desired_privilege_level = default_desired_privilege_level

        self.comms_prompt_pattern_all = r"|".join(
            rf"(?P<{priv_level}>{priv_level_data.pattern})"
            for priv_level, priv_level_data in self.privilege_levels.items()
        )
        self._current_priv_level = NoPrivLevel
        self._priv_map: Dict[str, List[str]] = {}
        self._build_priv_map()

        self.auth_secondary = auth_secondary

        self.textfsm_platform: str = ""
        self.genie_platform: str = ""
        self.failed_when_contains: List[str] = []

        super().__init__(comms_prompt_pattern=self.comms_prompt_pattern_all, **kwargs)

    def _build_priv_map(self) -> None:
        """
        Build a "map" of privilege levels

        `_priv_map` is a "map" of all privilege levels mapped out to the lowest available priv. This
        map is used for determining how to escalate/deescalate.

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        for priv_level in self.privilege_levels:
            self._priv_map[priv_level] = [priv_level]
            while True:
                previous_priv = self.privilege_levels[self._priv_map[priv_level][0]].previous_priv
                if not previous_priv:
                    break
                self._priv_map[priv_level].insert(0, previous_priv)

    @lru_cache()
    def _determine_current_priv(self, current_prompt: str) -> PrivilegeLevel:
        """
        Determine current privilege level from prompt string

        Args:
            current_prompt: string of current prompt

        Returns:
            PrivilegeLevel: NamedTuple of current privilege level

        Raises:
            UnknownPrivLevel: if privilege level cannot be determined

        """
        prompt_pattern = get_prompt_pattern(prompt="", class_prompt=self.comms_prompt_pattern_all)
        search_result = re.search(pattern=prompt_pattern, string=current_prompt.encode())
        if search_result:
            possible_priv_levels = [
                priv_name
                for priv_name, matched_prompt in search_result.groupdict().items()
                if matched_prompt
            ]
            priv_level = self.privilege_levels[possible_priv_levels[0]]
            LOG.debug(f"Determined current privilege level is `{priv_level.name}`")
            return priv_level
        raise UnknownPrivLevel(
            f"Could not determine privilege level from provided prompt: `{current_prompt}`"
        )

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
        next_prompt_pattern = escalate_priv.pattern
        if escalate_priv.escalate_auth is True:
            if not self.auth_secondary:
                err = (
                    "Privilege escalation generally requires an `auth_secondary` password, "
                    "but none is set!"
                )
                msg = f"***** {err} {'*' * (80 - len(err))}"
                fix = (
                    "scrapli will try to escalate privilege without entering a password but may "
                    "fail.\nSet an `auth_secondary` password if your device requires a password to "
                    "increase privilege, otherwise ignore this message."
                )
                warning = "\n" + msg + "\n" + fix + "\n" + msg
                warnings.warn(warning)
            else:
                escalate_cmd: str = escalate_priv.escalate
                escalate_prompt: str = escalate_priv.escalate_prompt
                escalate_auth = self.auth_secondary
                super().send_interactive(
                    interact_events=[
                        (escalate_cmd, escalate_prompt, False),
                        (escalate_auth, next_prompt_pattern, True),
                    ],
                )
                self.channel.comms_prompt_pattern = next_prompt_pattern
                return
        self.channel.comms_prompt_pattern = next_prompt_pattern
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
        self.channel.comms_prompt_pattern = self.privilege_levels[
            current_priv.previous_priv
        ].pattern
        self.channel.send_input(channel_input=current_priv.deescalate)

    def acquire_priv(self, desired_priv: str) -> None:
        """
        Acquire desired priv level

        Args:
            desired_priv: string name of desired privilege level
                (see scrapli.driver.<driver_category.device_type>.driver for levels)

        Returns:
            N/A  # noqa: DAR202

        Raises:
           UnknownPrivLevel: if attempting to acquire an unknown priv

        """
        LOG.info(f"Attempting to acquire `{desired_priv}` privilege level")
        if desired_priv not in self.privilege_levels.keys():
            raise UnknownPrivLevel(
                f"Requested privilege level `{desired_priv}` not a valid privilege level of "
                f"`{self.__class__.__name__}`"
            )

        map_to_desired_priv = self._priv_map[desired_priv]

        while True:
            # if we are already at the desired priv, we don't need to do any thing
            current_priv = self._determine_current_priv(current_prompt=self.channel.get_prompt())
            if current_priv.name == desired_priv:
                self._current_priv_level = current_priv
                return

            map_to_current_priv = self._priv_map[current_priv.name]
            priv_map = (
                map_to_current_priv
                if map_to_current_priv > map_to_desired_priv
                else map_to_desired_priv
            )

            desired_priv_index = priv_map.index(desired_priv)
            current_priv_index = priv_map.index(current_priv.name)
            if current_priv_index > desired_priv_index:
                deescalate_priv = priv_map[current_priv_index - 1]
                LOG.info(f"Attempting to deescalate from {current_priv.name} to {deescalate_priv}")
                self._deescalate(current_priv=current_priv)
            else:
                escalate_priv = self.privilege_levels[priv_map[current_priv_index + 1]]
                LOG.info(f"Attempting to escalate from {current_priv.name} to {escalate_priv.name}")
                self._escalate(escalate_priv=escalate_priv)

    def _update_response(self, response: Response) -> None:
        """
        Update response with network driver specific data

        This happens here as the underlying channel provides a response object but is unaware of any
        of the network/platform specific attributes that may need to get updated

        Args:
            response: response to update

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        response.textfsm_platform = self.textfsm_platform
        response.genie_platform = self.genie_platform

    def send_command(
        self,
        command: str,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
    ) -> Response:
        """
        Send a command

        Super method will raise TypeError if anything but a string is passed here!

        Args:
            command: string to send to device in privilege exec mode
            strip_prompt: True/False strip prompt from returned output
            failed_when_contains: string or list of strings indicating failure if found in response

        Returns:
            Response: Scrapli Response object

        Raises:
            N/A

        """
        if self._current_priv_level.name != self.default_desired_privilege_level:
            self.acquire_priv(desired_priv=self.default_desired_privilege_level)

        if failed_when_contains is None:
            failed_when_contains = self.failed_when_contains

        response = super().send_command(
            command=command, strip_prompt=strip_prompt, failed_when_contains=failed_when_contains
        )

        self._update_response(response)

        return response

    def send_commands(
        self,
        commands: List[str],
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        stop_on_failed: bool = False,
    ) -> List[Response]:
        """
        Send multiple commands

        Super method will raise TypeError if anything but a list of strings is passed here!

        Args:
            commands: list of strings to send to device in privilege exec mode
            strip_prompt: True/False strip prompt from returned output
            failed_when_contains: string or list of strings indicating failure if found in response
            stop_on_failed: True/False stop executing commands if a command fails, returns results
                as of current execution

        Returns:
            responses: list of Scrapli Response objects

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
    ) -> List[Response]:
        """
        Send command(s) from file

        Args:
            file: string path to file
            strip_prompt: True/False strip prompt from returned output
            failed_when_contains: string or list of strings indicating failure if found in response
            stop_on_failed: True/False stop executing commands if a command fails, returns results
                as of current execution

        Returns:
            responses: list of Scrapli Response objects

        Raises:
            TypeError: if anything but a string is provided for `file`

        """
        if not isinstance(file, str):
            raise TypeError(
                f"`send_commands_from_file` expects a string path to file, got {type(file)}"
            )
        resolved_file = resolve_file(file)

        with open(resolved_file, "r") as f:
            commands = f.read().splitlines()

        return self.send_commands(
            commands=commands,
            strip_prompt=strip_prompt,
            failed_when_contains=failed_when_contains,
            stop_on_failed=stop_on_failed,
        )

    def send_interactive(
        self,
        interact_events: List[Tuple[str, str, Optional[bool]]],
        failed_when_contains: Optional[Union[str, List[str]]] = None,
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

        Returns:
            Response: scrapli Response object

        Raises:
            N/A

        """
        if self._current_priv_level.name != self.default_desired_privilege_level:
            self.acquire_priv(desired_priv=self.default_desired_privilege_level)
        response = super().send_interactive(
            interact_events=interact_events, failed_when_contains=failed_when_contains
        )
        self._update_response(response=response)

        return response

    def _abort_config(self) -> None:
        """
        Abort a configuration session for platforms with commit type functionality; i.e iosxr/junos

        Args:
            N/A

        Returns:
            N/A:  # noqa: DAR202

        Raises:
            N/A

        """

    def send_configs(
        self,
        configs: Union[str, List[str]],
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        stop_on_failed: bool = False,
    ) -> List[Response]:
        """
        Send configuration(s)

        Args:
            configs: string or list of strings to send to device in config mode
            strip_prompt: True/False strip prompt from returned output
            failed_when_contains: string or list of strings indicating failure if found in response
            stop_on_failed: True/False stop executing commands if a command fails, returns results
                as of current execution

        Returns:
            responses: List of Scrape Response objects

        Raises:
            N/A

        """
        if isinstance(configs, str):
            configs = [configs]

        if not self._current_priv_level.name.startswith("configuration"):
            self.acquire_priv(desired_priv="configuration")

        if failed_when_contains is None:
            failed_when_contains = self.failed_when_contains

        responses = []
        _failed_during_execution = False
        for config in configs:
            response = super().send_command(
                command=config,
                strip_prompt=strip_prompt,
                failed_when_contains=failed_when_contains,
            )
            responses.append(response)
            if stop_on_failed is True and response.failed is True:
                _failed_during_execution = True
                break

        for response in responses:
            self._update_response(response=response)

        if _failed_during_execution is True:
            self._abort_config()

        self.acquire_priv(desired_priv=self.default_desired_privilege_level)
        return responses

    def send_configs_from_file(
        self,
        file: str,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        stop_on_failed: bool = False,
    ) -> List[Response]:
        """
        Send configuration(s) from a file

        Args:
            file: string path to file
            strip_prompt: True/False strip prompt from returned output
            failed_when_contains: string or list of strings indicating failure if found in response
            stop_on_failed: True/False stop executing commands if a command fails, returns results
                as of current execution

        Returns:
            responses: List of Scrape Response objects

        Raises:
            TypeError: if anything but a string is provided for `file`

        """
        if not isinstance(file, str):
            raise TypeError(
                f"`send_configs_from_file` expects a string path to file, got {type(file)}"
            )
        resolved_file = resolve_file(file)

        with open(resolved_file, "r") as f:
            configs = f.read().splitlines()

        return self.send_configs(
            configs=configs,
            strip_prompt=strip_prompt,
            failed_when_contains=failed_when_contains,
            stop_on_failed=stop_on_failed,
        )
