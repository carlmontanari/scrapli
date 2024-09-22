"""scrapli.driver.network.base_driver"""

import re
from collections import defaultdict
from datetime import datetime
from enum import Enum
from functools import lru_cache
from logging import Logger, LoggerAdapter
from typing import TYPE_CHECKING, DefaultDict, Dict, List, Optional, Set, Tuple, Union

from scrapli.exceptions import ScrapliPrivilegeError, ScrapliTypeError
from scrapli.helper import user_warning
from scrapli.response import MultiResponse, Response

if TYPE_CHECKING:
    LoggerAdapterT = LoggerAdapter[Logger]  # pragma:  no cover # pylint:disable=E1136
else:
    LoggerAdapterT = LoggerAdapter


class PrivilegeLevel:
    __slots__ = (
        "pattern",
        "name",
        "previous_priv",
        "deescalate",
        "escalate",
        "escalate_auth",
        "escalate_prompt",
        "not_contains",
    )

    def __init__(  # pylint: disable=R0917
        self,
        pattern: str,
        name: str,
        previous_priv: str,
        deescalate: str,
        escalate: str,
        escalate_auth: bool,
        escalate_prompt: str,
        not_contains: Optional[List[str]] = None,
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
            not_contains: list of substrings that should *not* be seen in a prompt for this
                privilege level

        Returns:
            None

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
        self.not_contains: List[str] = not_contains or []


DUMMY_PRIV_LEVEL = PrivilegeLevel("", "DUMMY", "", "", "", False, "")
PRIVS: Dict[str, PrivilegeLevel] = {}


class PrivilegeAction(Enum):
    NO_ACTION = "no action"
    ESCALATE = "escalate"
    DEESCALATE = "deescalate"


class BaseNetworkDriver:
    # BaseNetworkDriver Mixin vars for typing/linting purposes
    logger: LoggerAdapterT
    auth_secondary: str
    failed_when_contains: List[str]
    textfsm_platform: str
    genie_platform: str
    privilege_levels: Dict[str, PrivilegeLevel]
    comms_prompt_pattern: str
    _current_priv_level = DUMMY_PRIV_LEVEL
    _priv_graph: DefaultDict[str, Set[str]]

    def _generate_comms_prompt_pattern(self) -> None:
        """
        Generate the `comms_prompt_pattern` from the currently assigned privilege levels

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        self.logger.debug("generating combined network comms prompt pattern")
        self.comms_prompt_pattern = r"|".join(
            rf"({priv_level_data.pattern})" for priv_level_data in self.privilege_levels.values()
        )

    @lru_cache(maxsize=64)
    def _determine_current_priv(self, current_prompt: str) -> List[str]:
        """
        Determine current privilege level from prompt string

        Args:
            current_prompt: string of current prompt

        Returns:
            list: list of string names of matching privilege levels

        Raises:
            ScrapliPrivilegeError: if privilege level cannot be determined

        """
        matching_priv_levels = []
        for priv_level in self.privilege_levels.values():
            if priv_level.not_contains:
                # starting at 2021.07.30 the `not_contains` field was added to privilege levels
                # (defaulting to an empty tuple) -- this helps us to simplify the priv patterns
                # greatly, as well as have no reliance on look arounds which makes the "normal"
                # scrapli privilege levels more go friendly -- useful for scrapligo!
                if any(not_contains in current_prompt for not_contains in priv_level.not_contains):
                    continue

            search_result = re.search(
                pattern=priv_level.pattern, string=current_prompt, flags=re.M | re.I
            )
            if not search_result:
                continue

            matching_priv_levels.append(priv_level.name)
        if not matching_priv_levels:
            msg = f"could not determine privilege level from provided prompt: '{current_prompt}'"
            self.logger.critical(msg)
            raise ScrapliPrivilegeError(msg)

        self.logger.debug(f"determined current privilege level is one of '{matching_priv_levels}'")

        return matching_priv_levels

    def _build_priv_graph(self) -> None:
        """
        Build a graph of privilege levels

        `_priv_graph` is a "graph" of all privilege levels and how to acquire them from any given
        priv level. This is probably not very efficient but we should never have more than a
        handful of priv levels so this should never be a big issue.

        While at the moment priv levels are always... "linear" in that there is only ever one "up"
        and one "down" privilege from any given priv, we still have "forks" in the road -- for
        example, in IOSXR we can go from privilege exec to configuration or configuration exclusive.
        This method builds a graph that allows us to make intelligent decisions about how to get
        from where we are to where we want to be!

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        self._priv_graph = defaultdict(set)

        privilege_levels = self.privilege_levels.values()
        for privilege_level in privilege_levels:
            if privilege_level.previous_priv:
                self._priv_graph[privilege_level.name].add(privilege_level.previous_priv)
            else:
                self._priv_graph[privilege_level.name] = set()

        for higher_privilege_level, privilege_level_list in self._priv_graph.items():
            for privilege_level_name in privilege_level_list:
                self._priv_graph[privilege_level_name].add(higher_privilege_level)

    def _build_priv_change_map(
        self,
        starting_priv_name: str,
        destination_priv_name: str,
        priv_change_map: Optional[List[str]] = None,
    ) -> List[str]:
        """
        Generate a list of priv levels from starting priv to destination priv

        Args:
            starting_priv_name: name of starting priv
            destination_priv_name: name of destination priv
            priv_change_map: current priv_change_map; should only be passed when this function
                calls itself

        Returns:
            list: list of strings of priv names to get from starting to destination priv level

        Raises:
            N/A

        """
        if priv_change_map is None:
            priv_change_map = []

        priv_change_map = priv_change_map + [starting_priv_name]

        if starting_priv_name == destination_priv_name:
            return priv_change_map

        for privilege_name in self._priv_graph[starting_priv_name]:
            if privilege_name not in priv_change_map:
                updated_priv_change_map = self._build_priv_change_map(
                    starting_priv_name=privilege_name,
                    destination_priv_name=destination_priv_name,
                    priv_change_map=priv_change_map,
                )
                if updated_priv_change_map:
                    return updated_priv_change_map

        # shouldnt ever get to this i dont think... putting here to appease pylint and ignoring cov
        return []  # pragma: nocover

    def update_privilege_levels(self) -> None:
        """
        Re-generate the privilege graph, and update the comms prompt pattern

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        # build/update the priv graph
        self._build_priv_graph()

        # build/update the joined comms prompt pattern
        self._generate_comms_prompt_pattern()

        # ensure the channel has the updated prompt pattern so it knows how to match any newly
        # updated priv levels (such as registered configuration sessions)
        self.channel.comms_prompt_pattern = (  # type: ignore  # pylint: disable=E1101
            self.comms_prompt_pattern
        )

        # finally, clear the lru caches as patterns may have been updated
        self._determine_current_priv.cache_clear()

    def _validate_privilege_level_name(self, privilege_level_name: str) -> None:
        """
        Get privilege level name if provided privilege is valid

        Args:
            privilege_level_name: string name of desired privilege level

        Returns:
            None

        Raises:
            ScrapliPrivilegeError: if attempting to acquire an unknown priv

        """
        desired_privilege_level = self.privilege_levels.get(privilege_level_name)
        if desired_privilege_level is None:
            msg = (
                f"requested privilege level '{privilege_level_name}' not a valid privilege level of"
                f" '{self.__class__.__name__}'"
            )
            self.logger.critical(msg)
            raise ScrapliPrivilegeError(msg)

    def _pre_escalate(self, escalate_priv: PrivilegeLevel) -> None:
        """
        Handle pre "_escalate" tasks for consistency between sync/async versions

        Args:
            escalate_priv: privilege level to escalate to

        Returns:
            None

        Raises:
            N/A

        """
        if escalate_priv.escalate_auth is True and not self.auth_secondary:
            title = "Authentication Warning!"
            message = (
                "scrapli will try to escalate privilege without entering a password but may "
                "fail.\nSet an 'auth_secondary' password if your device requires a password to "
                "increase privilege, otherwise ignore this message."
            )
            user_warning(title=title, message=message)

    def _process_acquire_priv(
        self,
        destination_priv: str,
        current_prompt: str,
    ) -> Tuple[PrivilegeAction, PrivilegeLevel]:
        """
        Handle non channel "acquire_priv" tasks for consistency between sync/async versions

        Args:
            destination_priv: string name of desired privilege level
            current_prompt: string of the current prompt

        Returns:
            Tuple[PrivilegeAction, PrivilegeLevel]: enum set to appropriate value for no action,
                escalate or deescalate and privilege level object to pass to either escalate or
                deescalate method

        Raises:
            N/A

        """
        self.logger.info(f"attempting to acquire '{destination_priv}' privilege level")

        # decide if we are already at the desired priv, then we don't need to do any thing!
        current_priv_patterns = self._determine_current_priv(current_prompt=current_prompt)

        if self._current_priv_level.name in current_priv_patterns:
            current_priv = self.privilege_levels[self._current_priv_level.name]
        elif destination_priv in current_priv_patterns:
            current_priv = self.privilege_levels[destination_priv]
        else:
            # if multiple patterns match pick the zeroith... hopefully this never happens though...
            # and it *shouldn't* because right now the only way to have the same priv patterns is
            # to be *basically* the same privilege level -- i.e. configuration and configuration
            # exclusive for iosxr
            current_priv = self.privilege_levels[current_priv_patterns[0]]

        if current_priv.name == destination_priv:
            self.logger.debug(
                "determined current privilege level is target privilege level, no action needed"
            )
            self._current_priv_level = self.privilege_levels[destination_priv]
            return PrivilegeAction.NO_ACTION, self.privilege_levels[destination_priv]

        map_to_destination_priv = self._build_priv_change_map(
            starting_priv_name=current_priv.name, destination_priv_name=destination_priv
        )

        # at this point we basically dont *know* the privilege leve we are at (or we wont/cant after
        # we do an escalation or deescalation, so we reset to the dummy priv level
        self._current_priv_level = DUMMY_PRIV_LEVEL

        if self.privilege_levels[map_to_destination_priv[1]].previous_priv != current_priv.name:
            self.logger.debug("determined privilege deescalation necessary")
            return PrivilegeAction.DEESCALATE, current_priv

        self.logger.debug("determined privilege escalation necessary")
        return PrivilegeAction.ESCALATE, self.privilege_levels[map_to_destination_priv[1]]

    @property
    def _generic_driver_mode(self) -> bool:
        """
        Getter for `_generic_driver_mode` attribute

        Args:
            N/A

        Returns:
            bool: _generic_driver_mode value

        Raises:
            N/A

        """
        try:
            return self.__generic_driver_mode
        except AttributeError:
            return False

    @_generic_driver_mode.setter
    def _generic_driver_mode(self, value: bool) -> None:
        """
        Setter for `_generic_driver_mode` attribute

        Args:
            value: bool value for _generic_driver_mode

        Returns:
            None

        Raises:
            ScrapliTypeError: if value is not of type bool

        """
        self.logger.debug(f"setting '_generic_driver_mode' value to '{value}'")

        if not isinstance(value, bool):
            raise ScrapliTypeError

        if value is True:
            # if we are setting ingore priv level we reset current priv to the dummy priv so that
            # once (if) a user turns ignore priv back off we know we need to reset/reacquire priv
            # as the user coulda done pretty much anything and we could end up at who knows what
            # priv level
            self._current_priv_level = DUMMY_PRIV_LEVEL

        self.__generic_driver_mode = value

    def _update_response(self, response: Response) -> None:
        """
        Update response with network driver specific data

        This happens here as the underlying channel provides a response object but is unaware of any
        of the network/platform specific attributes that may need to get updated

        Args:
            response: response to update

        Returns:
            None

        Raises:
            N/A

        """
        response.textfsm_platform = self.textfsm_platform
        response.genie_platform = self.genie_platform

    @staticmethod
    def _pre_send_config(config: str) -> List[str]:
        """
        Handle pre "send_config" tasks for consistency between sync/async versions

        Args:
            config: string configuration to send to the device, supports sending multi-line strings

        Returns:
            list: list of config lines from provided "config" input

        Raises:
            ScrapliTypeError: if anything but a string is provided for `file`

        """
        if not isinstance(config, str):
            raise ScrapliTypeError(
                f"'send_config' expects a single string, got {type(config)}, "
                "to send a list of configs use the 'send_configs' method instead."
            )

        # in order to handle multi-line strings, we split lines
        split_config = config.splitlines()

        return split_config

    def _post_send_config(
        self,
        config: str,
        multi_response: MultiResponse,
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
        response.finish_time = datetime.now()
        response.elapsed_time = (response.finish_time - response.start_time).total_seconds()

        # join all the results together into a single final result
        response.result = "\n".join(response.result for response in multi_response)
        response.failed = False

        if any(r.failed for r in multi_response):
            response.failed = True
        self._update_response(response=response)

        return response

    def _pre_send_configs(
        self,
        configs: List[str],
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        privilege_level: str = "",
    ) -> Tuple[str, Union[str, List[str]]]:
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
            Tuple[str, Union[str, List[str]]]: string of resolved privilege level name, and failed
                when contains which may be a string or list of strings

        Raises:
            ScrapliTypeError: if configs is anything but a list
            ScrapliPrivilegeError: if connection is in 'generic_driver_mode' -- this should be a
                non-standard use case so there is no reason to complicate the config(s) methods
                with supporting generic driver mode (plus if there was config modes in generic
                driver mode that wouldn't be very generic driver like, would it!)

        """
        if not isinstance(configs, list):
            raise ScrapliTypeError(
                f"'send_configs' expects a list of strings, got {type(configs)}, "
                "to send a single configuration line/string use the 'send_config' method instead."
            )

        if self._generic_driver_mode is True:
            raise ScrapliPrivilegeError(
                "connection is in 'generic_driver_mode', send config(s|s_from_file) is disabled"
            )

        if failed_when_contains is None:
            final_failed_when_contains = self.failed_when_contains
        elif isinstance(failed_when_contains, str):
            final_failed_when_contains = [failed_when_contains]
        else:
            final_failed_when_contains = failed_when_contains

        if privilege_level:
            self._validate_privilege_level_name(privilege_level_name=privilege_level)
            resolved_privilege_level = privilege_level
        else:
            resolved_privilege_level = "configuration"

        return resolved_privilege_level, final_failed_when_contains

    def _post_send_configs(self, responses: MultiResponse) -> MultiResponse:
        """
        Handle post "send_configs" tasks for consistency between sync/async versions

        Args:
            responses: multi_response object to update

        Returns:
            MultiResponse: Unified response object

        Raises:
            N/A

        """
        for response in responses:
            self._update_response(response=response)

        return responses
