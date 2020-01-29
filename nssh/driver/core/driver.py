"""nssh.driver.core.driver"""
import collections
import re
from io import TextIOWrapper
from typing import Any, Dict, List, Optional, Union

from nssh import NSSH
from nssh.exceptions import CouldNotAcquirePrivLevel, UnknownPrivLevel
from nssh.helper import _textfsm_get_template, get_prompt_pattern, textfsm_parse
from nssh.result import Result

PrivilegeLevel = collections.namedtuple(
    "PrivilegeLevel",
    "pattern "
    "name "
    "deescalate_priv "
    "deescalate "
    "escalate_priv "
    "escalate "
    "escalate_auth "
    "escalate_prompt "
    "requestable "
    "level",
)

PRIVS: Dict[str, PrivilegeLevel] = {}


class NetworkDriver(NSSH):
    def __init__(self, auth_secondary: str = "", **kwargs: Any):
        """
        BaseNetworkDriver Object

        Args:
            auth_secondary: password to use for secondary authentication (enable)
            **kwargs: keyword args to pass to inherited class(es)

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa
        """
        super().__init__(**kwargs)
        self.auth_secondary = auth_secondary
        self.privs = PRIVS
        self.default_desired_priv: Optional[str] = None
        self.textfsm_platform: str = ""

    def _determine_current_priv(self, current_prompt: str) -> PrivilegeLevel:
        """
        Determine current privilege level from prompt string

        Args:
            current_prompt: string of current prompt

        Returns:
            priv_level: NamedTuple of current privilege level

        Raises:
            UnknownPrivLevel: if privilege level cannot be determined  # noqa
            # NOTE: darglint raises DAR401 for some reason hence the noqa...

        """
        # TODO -- fix above note...
        for priv_level in self.privs.values():
            prompt_pattern = get_prompt_pattern("", priv_level.pattern)
            if re.search(prompt_pattern, current_prompt.encode()):
                return priv_level
        raise UnknownPrivLevel

    def _escalate(self) -> None:
        """
        Escalate to the next privilege level up

        Args:
            N/A  # noqa

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa

        """
        current_priv = self._determine_current_priv(self.channel.get_prompt())
        if current_priv.escalate:
            next_priv = self.privs.get(current_priv.escalate_priv, None)
            if next_priv is None:
                raise UnknownPrivLevel(
                    f"Could not get next priv level, current priv is {current_priv.name}"
                )
            next_prompt = next_priv.pattern
            if current_priv.escalate_auth:
                escalate_cmd: str = current_priv.escalate
                escalate_prompt: str = current_priv.escalate_prompt
                escalate_auth = self.auth_secondary
                if not isinstance(next_prompt, str):
                    raise TypeError(
                        f"got {type(next_prompt)} for {current_priv.name} escalate priv, "
                        "expected str"
                    )
                self.channel.send_inputs_interact(
                    (escalate_cmd, escalate_prompt, escalate_auth, next_prompt),
                    hidden_response=True,
                )

            else:
                self.channel.comms_prompt_pattern = next_priv.pattern
                self.channel.send_inputs(current_priv.escalate)

    def _deescalate(self) -> None:
        """
        Deescalate to the next privilege level down

        Args:
            N/A  # noqa

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa

        """
        current_priv = self._determine_current_priv(self.channel.get_prompt())
        if current_priv.deescalate:
            self.channel.send_inputs(current_priv.deescalate)

    def acquire_priv(self, desired_priv: str) -> None:
        """
        Acquire desired priv level

        Args:
            desired_priv: string name of desired privilege level
                (see nssh.driver.<driver_category.device_type>.driver for levels)

        Returns:
            N/A  # noqa

        Raises:
            CouldNotAcquirePrivLevel: if requested priv level not attained

        """
        priv_attempt_counter = 0
        while True:
            current_priv = self._determine_current_priv(self.channel.get_prompt())
            if current_priv == self.privs[desired_priv]:
                return
            if priv_attempt_counter > len(self.privs):
                raise CouldNotAcquirePrivLevel(
                    f"Could not get to '{desired_priv}' privilege level."
                )

            if current_priv.level > self.privs[desired_priv].level:
                self._deescalate()
            else:
                self._escalate()
            priv_attempt_counter += 1

    def send_commands(
        self, commands: Union[str, List[str]], strip_prompt: bool = True, textfsm: bool = False,
    ) -> List[Result]:
        """
        Send command(s)

        Args:
            commands: string or list of strings to send to device in privilege exec mode
            strip_prompt: True/False strip prompt from returned output
            textfsm: True/False try to parse each command with textfsm

        Returns:
            results: list of SSH2NetResult objects

        Raises:
            N/A  # noqa
        """
        self.acquire_priv(str(self.default_desired_priv))
        results = self.channel.send_inputs(commands, strip_prompt)
        if not textfsm:
            return results
        for result in results:
            result.structured_result = self.textfsm_parse_output(
                result.channel_input, result.result
            )
        return results

    def send_configs(
        self, configs: Union[str, List[str]], strip_prompt: bool = True
    ) -> List[Result]:
        """
        Send configuration(s)

        Args:
            configs: string or list of strings to send to device in config mode
            strip_prompt: True/False strip prompt from returned output

        Returns:
            N/A  # noqa

        Raises:
            N/A  # noqa
        """
        self.acquire_priv("configuration")
        result = self.channel.send_inputs(configs, strip_prompt)
        self.acquire_priv(str(self.default_desired_priv))
        return result

    def textfsm_parse_output(
        self, command: str, output: str
    ) -> Union[List[Union[List[Any], Dict[str, Any]]], Dict[str, Any]]:
        """
        Parse output with TextFSM and ntc-templates

        Always return a non-string value -- if parsing fails to produce list/dict, return empty dict

        Args:
            command: command used to get output
            output: output from command

        Returns:
            output: parsed output

        Raises:
            N/A  # noqa
        """
        template = _textfsm_get_template(self.textfsm_platform, command)
        if isinstance(template, TextIOWrapper):
            structured_output = textfsm_parse(template, output)
            if isinstance(structured_output, (dict, list)):
                return structured_output
        return {}
