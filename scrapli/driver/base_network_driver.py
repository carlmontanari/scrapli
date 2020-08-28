"""scrapli.driver.base_network_driver"""
import re
import warnings
from collections import UserList
from datetime import datetime
from enum import Enum
from functools import lru_cache
from logging import Logger
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

from scrapli.exceptions import UnknownPrivLevel
from scrapli.helper import resolve_file
from scrapli.response import Response

if TYPE_CHECKING:
    ScrapliMultiResponse = UserList[Response]  # pylint:  disable=E1136; # pragma:  no cover
else:
    ScrapliMultiResponse = UserList


class PrivilegeLevel:
    __slots__ = (
        "pattern",
        "name",
        "previous_priv",
        "deescalate",
        "escalate",
        "escalate_auth",
        "escalate_prompt",
    )

    def __init__(
        self,
        pattern: str,
        name: str,
        previous_priv: str,
        deescalate: str,
        escalate: str,
        escalate_auth: bool,
        escalate_prompt: str,
    ):
        """
        PrivilegeLevel Object

        Args:
            pattern: regex pattern to use to identify this privilege level by the prompt
            name: friendly name of this privilege level
            previous_priv: name of the lower/previous privilege level
            deescalate: how to deescalate *from* this privilege level (to the lower/previous priv)
            escalate: how to escalate *to* this privilege level (from the lower/previous priv)
            escalate_auth: True/False escalation requires authentication
            escalate_prompt: prompt pattern to search for during escalation if escalate auth is True

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.pattern = pattern
        self.name = name
        self.previous_priv = previous_priv
        self.deescalate = deescalate
        self.escalate = escalate
        self.escalate_auth = escalate_auth
        self.escalate_prompt = escalate_prompt


DUMMY_PRIV_LEVEL = PrivilegeLevel("", "DUMMY", "", "", "", False, "")
PRIVS: Dict[str, PrivilegeLevel] = {}


class PrivilegeAction(Enum):
    NO_ACTION = "no action"
    ESCALATE = "escalate"
    DEESCALATE = "deescalate"


class NetworkDriverBase:
    # NetworkDriverBase Mixin vars for typing/linting purposes
    logger: Logger
    comms_prompt_pattern: str
    _current_priv_level = DUMMY_PRIV_LEVEL
    _priv_map: Dict[str, List[str]]
    failed_when_contains: Optional[List[str]]
    privilege_levels: Dict[str, PrivilegeLevel]
    auth_secondary: str
    textfsm_platform: str
    genie_platform: str

    @staticmethod
    def _check_kwargs_comms_prompt_pattern(kwargs: Any) -> None:
        """
        Warn users if passing comms prompt pattern while using NetworkDriver derived classes

        Args:
            kwargs: kwargs being passed into NetworkDriver classes

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        if "comms_prompt_pattern" in kwargs:
            err = "`comms_prompt_pattern` found in kwargs!"
            msg = f"***** {err} {'*' * (80 - len(err))}"
            fix = (
                "`comms_prompt_pattern` is ignored (dropped) when using network drivers. If you "
                "wish to modify the patterns for any network driver sub-classes, please do so by "
                "modifying or providing your own `privilege_levels`."
            )
            warning = "\n" + msg + "\n" + fix + "\n" + msg
            warnings.warn(warning)
            kwargs.pop("comms_prompt_pattern")

    def _generate_comms_prompt_pattern(self) -> None:
        """
        Generate the `comms_prompt_pattern_all` from the currently assigned privilege levels

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.comms_prompt_pattern = r"|".join(
            rf"({priv_level_data.pattern})" for priv_level_data in self.privilege_levels.values()
        )

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

    def update_privilege_levels(self, update_channel: bool = True) -> None:
        """
        Re-generate the privilege map, and update the comms prompt pattern

        Args:
            update_channel: True/False update the channel pattern too -- likely only ever set to
                False for class initialization before channel is opened

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self._build_priv_map()
        self._generate_comms_prompt_pattern()
        # clear the lru cache as patterns may have been updated
        self._determine_current_priv.cache_clear()
        if update_channel is True:
            self.channel.comms_prompt_pattern = (  # type: ignore  # pylint: disable=E1101
                self.comms_prompt_pattern
            )

    @lru_cache()
    def _determine_current_priv(self, current_prompt: str) -> List[str]:
        """
        Determine current privilege level from prompt string

        Args:
            current_prompt: string of current prompt

        Returns:
            matching_priv_levels: list of string names of matching privilege levels

        Raises:
            UnknownPrivLevel: if privilege level cannot be determined

        """
        matching_priv_levels = []
        for priv_level in self.privilege_levels.values():
            search_result = re.search(
                pattern=priv_level.pattern, string=current_prompt, flags=re.M | re.I
            )
            if not search_result:
                continue
            matching_priv_levels.append(priv_level.name)
            self.logger.debug(f"Current privilege level could be `{priv_level.name}`")
        if not matching_priv_levels:
            raise UnknownPrivLevel(
                f"Could not determine privilege level from provided prompt: `{current_prompt}`"
            )
        self.logger.debug(f"Determined current privilege level is one of `{matching_priv_levels}`")
        return matching_priv_levels

    def _get_privilege_level_name(self, requested_priv: str) -> str:
        """
        Get privilege level name if provided privilege is valid

        Args:
            requested_priv: string name of desired privilege level

        Returns:
            str: name of the privilege level requested

        Raises:
            UnknownPrivLevel: if attempting to acquire an unknown priv

        """
        desired_privilege_level = self.privilege_levels.get(requested_priv, None)
        if desired_privilege_level is None:
            raise UnknownPrivLevel(
                f"Requested privilege level `{requested_priv}` not a valid privilege level of "
                f"`{self.__class__.__name__}`"
            )
        resolved_privilege_level = desired_privilege_level.name
        return resolved_privilege_level

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

    def register_configuration_session(self, session_name: str) -> None:
        """
        If applicable, register a configuration session as a valid privilege level

        Args:
            session_name: name of config session to register

        Returns:
            N/A:  # noqa: DAR202

        Raises:
            NotImplementedError: unless overridden by concrete class

        """
        _ = session_name
        raise NotImplementedError(
            f"Configuration sessions not supported for `{self.__class__.__name__}`"
        )

    def _pre_escalate(self, escalate_priv: PrivilegeLevel) -> None:
        """
        Handle pre "_escalate" tasks for consistency between sync/async versions

        Args:
            escalate_priv: privilege level to escalate to

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        if escalate_priv.escalate_auth is True and not self.auth_secondary:
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

    def _pre_acquire_priv(self, desired_priv: str) -> Tuple[str, List[str]]:
        """
        Handle pre "acquire_priv" tasks for consistency between sync/async versions

        Args:
            desired_priv: string name of desired privilege level

        Returns:
            resolved_priv: privilege level class resolved via given privilege name
            map_to_desired_priv: map from current priv to desired priv (list of strings of privs to
                iterate through to get to target priv)

        Raises:
            N/A

        """
        self.logger.info(f"Attempting to acquire `{desired_priv}` privilege level")
        resolved_priv = self._get_privilege_level_name(requested_priv=desired_priv)
        map_to_desired_priv = self._priv_map[resolved_priv]
        return resolved_priv, map_to_desired_priv

    def _process_acquire_priv(
        self,
        resolved_priv: str,
        map_to_desired_priv: List[str],
        current_prompt: str,
    ) -> Tuple[PrivilegeAction, PrivilegeLevel]:
        """
        Handle non channel "acquire_priv" tasks for consistency between sync/async versions

        Args:
            resolved_priv: string name of desired privilege level
            map_to_desired_priv: list of string names of privilege levels to acquire to get to
                desired privilege level
            current_prompt: string of the current prompt

        Returns:
            PrivilegeAction: enum set to appropriate value for no action, escalate or deescalate
            PrivilegeLevel: privilege level object to pass to either escalate or deescalate method

        Raises:
            N/A

        """
        # if we are already at the desired priv, we don't need to do any thing
        current_priv_patterns = self._determine_current_priv(current_prompt=current_prompt)

        # if multiple patterns match pick the zeroith... the only time patterns should be
        # identical is if we have privilege levels like "configuration" or
        # "configuration_exclusive" that have identical prompts (ex: IOSXRDriver)
        current_priv = self.privilege_levels[current_priv_patterns[0]]

        if resolved_priv in current_priv_patterns:
            self.logger.info(f"Acquired requested privilege level `{resolved_priv}`")
            self._current_priv_level = self.privilege_levels[resolved_priv]
            return PrivilegeAction.NO_ACTION, current_priv

        map_to_current_priv = self._priv_map[current_priv.name]
        priv_map = (
            map_to_current_priv
            if map_to_current_priv > map_to_desired_priv
            else map_to_desired_priv
        )

        desired_priv_index = priv_map.index(resolved_priv)
        try:
            current_priv_index = priv_map.index(current_priv.name)
        except ValueError:
            # if the current priv is not in the map for the desired priv; set the current index
            # to the "top" (end) of the priv map and work our way back down
            current_priv_index = len(priv_map)

        if current_priv_index > desired_priv_index:
            deescalate_priv = priv_map[current_priv_index - 1]
            self.logger.info(
                f"Attempting to deescalate from {current_priv.name} to {deescalate_priv}"
            )
            return PrivilegeAction.DEESCALATE, current_priv

        escalate_priv = self.privilege_levels[priv_map[current_priv_index + 1]]
        self.logger.info(f"Attempting to escalate from {current_priv.name} to {escalate_priv.name}")
        return PrivilegeAction.ESCALATE, escalate_priv

    @staticmethod
    def _pre_send_config(config: str) -> List[str]:
        """
        Handle pre "send_config" tasks for consistency between sync/async versions

        Args:
            config: string configuration to send to the device, supports sending multi-line strings

        Returns:
            configs: list of config lines from provided "config" input

        Raises:
            TypeError: if anything but a string is provided for `file`

        """
        if not isinstance(config, str):
            raise TypeError(
                f"`send_config` expects a single string, got {type(config)}, "
                "to send a list of configs use the `send_configs` method instead."
            )

        # in order to handle multi-line strings, we split lines
        split_config = config.splitlines()

        return split_config

    def _post_send_config(
        self,
        config: str,
        multi_response: ScrapliMultiResponse,
    ) -> Response:
        """
        Handle post "send_config" tasks for consistency between sync/async versions

        Args:
            config: string configuration to send to the device, supports sending multi-line strings
            multi_response: multi_response object send_config got from calling self.send_configs;
                we need this to parse out the multi_response back into a single Response object

        Returns:
            Response: Unified response object

        Raises:
            N/A

        """
        # capture failed_when_contains and host from zeroith multi_response element (there should
        #  always be at least a zeroith element here!); getting host just lets us keep the mixin
        #  class a little cleaner without having to deal with sync vs async transport classes from
        #  a typing perspective
        failed_when_contains = multi_response[0].failed_when_contains
        host = multi_response[0].host

        # create a new unified response object
        response = Response(
            host=host,
            channel_input=config,
            failed_when_contains=failed_when_contains,
        )
        response.start_time = multi_response[0].start_time
        response.elapsed_time = (datetime.now() - response.start_time).total_seconds()

        # join all the results together into a single final result
        response.result = "\n".join(response.result for response in multi_response)
        response.failed = False

        if any(response.failed for response in multi_response):
            response.failed = True
        self._update_response(response=response)

        return response

    def _pre_send_configs(
        self,
        configs: List[str],
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        privilege_level: str = "",
    ) -> Tuple[str, Optional[Union[str, List[str]]]]:
        """
        Handle pre "send_configs" tasks for consistency between sync/async versions

        Args:
            configs: list of strings to send to device in config mode
            failed_when_contains: string or list of strings indicating failure if found in response
            privilege_level: name of configuration privilege level/type to acquire; this is platform
                dependent, so check the device driver for specifics. Examples of privilege_name
                would be "configuration_exclusive" for IOSXRDriver, or "configuration_private" for
                JunosDriver. You can also pass in a name of a configuration session such as
                "my-config-session" if you have registered a session using the
                "register_config_session" method of the EOSDriver or NXOSDriver.

        Returns:
            commands: list of commands read from file

        Raises:
            TypeError: if configs is anything but a list

        """
        if not isinstance(configs, list):
            raise TypeError(
                f"`send_configs` expects a list of strings, got {type(configs)}, "
                "to send a single configuration line/string use the `send_config` method instead."
            )

        if failed_when_contains is None:
            failed_when_contains = self.failed_when_contains

        if privilege_level:
            resolved_privilege_level = self._get_privilege_level_name(
                requested_priv=privilege_level
            )
        else:
            resolved_privilege_level = "configuration"

        return resolved_privilege_level, failed_when_contains

    def _post_send_configs(self, responses: ScrapliMultiResponse) -> ScrapliMultiResponse:
        """
        Handle post "send_configs" tasks for consistency between sync/async versions

        Args:
            responses: multi_response object to update

        Returns:
            ScrapliMultiResponse: Unified response object

        Raises:
            N/A

        """
        for response in responses:
            self._update_response(response=response)

        return responses

    @staticmethod
    def _pre_send_configs_from_file(file: str) -> List[str]:
        """
        Handle pre "send_configs_from_file" tasks for consistency between sync/async versions

        Args:
            file: string path to file

        Returns:
            commands: list of commands read from file

        Raises:
            TypeError: if anything but a string is provided for `file`

        """
        if not isinstance(file, str):
            raise TypeError(
                f"`send_configs_from_file` expects a string path to a file, got {type(file)}"
            )
        resolved_file = resolve_file(file)

        with open(resolved_file, "r") as f:
            configs = f.read().splitlines()

        return configs
