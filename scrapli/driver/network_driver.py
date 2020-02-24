"""scrapli.driver.network_driver"""
import logging
import re
from collections import namedtuple
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from scrapli.driver.driver import Scrape
from scrapli.exceptions import CouldNotAcquirePrivLevel, UnknownPrivLevel
from scrapli.helper import get_external_function, get_prompt_pattern, validate_external_function
from scrapli.response import Response
from scrapli.transport import (
    MIKO_TRANSPORT_ARGS,
    SSH2_TRANSPORT_ARGS,
    SYSTEM_SSH_TRANSPORT_ARGS,
    MikoTransport,
    SSH2Transport,
    SystemSSHTransport,
    Transport,
)

TRANSPORT_CLASS: Dict[str, Callable[..., Transport]] = {
    "system": SystemSSHTransport,
    "ssh2": SSH2Transport,
    "paramiko": MikoTransport,
}
TRANSPORT_ARGS: Dict[str, Tuple[str, ...]] = {
    "system": SYSTEM_SSH_TRANSPORT_ARGS,
    "ssh2": SSH2_TRANSPORT_ARGS,
    "paramiko": MIKO_TRANSPORT_ARGS,
}


PrivilegeLevel = namedtuple(
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

LOG = logging.getLogger("scrapli_base")


class NetworkDriver(Scrape):
    def __init__(
        self,
        auth_secondary: str = "",
        session_pre_login_handler: Union[str, Callable[..., Any]] = "",
        session_disable_paging: Union[str, Callable[..., Any]] = "terminal length 0",
        **kwargs: Any,
    ):
        """
        BaseNetworkDriver Object

        Args:
            auth_secondary: password to use for secondary authentication (enable)
            session_pre_login_handler: callable or string that resolves to an importable function to
                handle pre-login (pre disable paging) operations
            session_disable_paging: callable, string that resolves to an importable function, or
                string to send to device to disable paging
            **kwargs: keyword args to pass to inherited class(es)

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        super().__init__(**kwargs)
        self.auth_secondary = auth_secondary
        self.privs = PRIVS
        self.default_desired_priv: Optional[str] = None
        self.textfsm_platform: str = ""
        self.exit_command: str = "exit"

        self.session_pre_login_handler: Optional[Callable[..., Any]] = None
        self.session_disable_paging: Union[str, Callable[..., Any]] = ""
        self._setup_session(session_pre_login_handler, session_disable_paging)

    def _setup_session(
        self,
        session_pre_login_handler: Union[str, Callable[..., Any]],
        session_disable_paging: Union[str, Callable[..., Any]],
    ) -> None:
        """
        Parse and setup session attributes

        Args:
            session_pre_login_handler: pre login handler to parse/set
            session_disable_paging: disable paging to parse/set

        Returns:
            N/A  # noqa: DAR202

        Raises:
            TypeError: if invalid type args provided

        """
        if session_pre_login_handler:
            self.session_pre_login_handler = self._set_session_pre_login_handler(
                session_pre_login_handler
            )
        else:
            self.session_pre_login_handler = None
        if callable(session_disable_paging):
            self.session_disable_paging = session_disable_paging
        if not isinstance(session_disable_paging, str) and not callable(session_disable_paging):
            raise TypeError(
                "session_disable_paging should be str or callable, got "
                f"{type(session_disable_paging)}"
            )
        if session_disable_paging != "terminal length 0":
            try:
                self.session_disable_paging = self._set_session_disable_paging(
                    session_disable_paging
                )
            except TypeError:
                self.session_disable_paging = session_disable_paging
        else:
            self.session_disable_paging = "terminal length 0"

    @staticmethod
    def _set_session_pre_login_handler(
        session_pre_login_handler: Union[str, Callable[..., Any]]
    ) -> Optional[Callable[..., Any]]:
        """
        Return session_pre_login_handler argument

        Args:
            session_pre_login_handler: callable function, or string representing a path to
                a callable

        Returns:
            session_pre_login_handler: callable or default empty string value

        Raises:
            TypeError: if provided string does not result in a callable

        """
        if callable(session_pre_login_handler):
            return session_pre_login_handler
        if not validate_external_function(session_pre_login_handler):
            LOG.critical(f"Invalid comms_pre_login_handler: {session_pre_login_handler}")
            raise TypeError(
                f"{session_pre_login_handler} is an invalid session_pre_login_handler function "
                "or path to a function."
            )
        return get_external_function(session_pre_login_handler)

    @staticmethod
    def _set_session_disable_paging(
        session_disable_paging: Union[Callable[..., Any], str]
    ) -> Union[Callable[..., Any], str]:
        """
        Return session_disable_paging argument

        Args:
            session_disable_paging: callable function, string representing a path to
                a callable, or a string to send to device to disable paging

        Returns:
            session_disable_paging: callable or string to use to disable paging

        Raises:
            TypeError: if provided string does not result in a callable

        """
        if callable(session_disable_paging):
            return session_disable_paging
        if not validate_external_function(session_disable_paging):
            raise TypeError(
                f"{session_disable_paging} is an invalid session_disable_paging function or path "
                "to a function. Assuming this is string to send to disable paging."
            )
        return get_external_function(session_disable_paging)

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
        for priv_level in self.privs.values():
            prompt_pattern = get_prompt_pattern("", priv_level.pattern)
            if re.search(prompt_pattern, current_prompt.encode()):
                return priv_level
        raise UnknownPrivLevel

    def _escalate(self) -> None:
        """
        Escalate to the next privilege level up

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            UnknownPrivLevel: if priv level cant be attained
            TypeError: if invalid next prompt value

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
                self.channel.comms_prompt_pattern = next_priv.pattern
            else:
                self.channel.comms_prompt_pattern = next_priv.pattern
                self.channel.send_inputs(current_priv.escalate)

    def _deescalate(self) -> None:
        """
        Deescalate to the next privilege level down

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            UnknownPrivLevel: if no default priv level set to deescalate to

        """
        current_priv = self._determine_current_priv(self.channel.get_prompt())
        if current_priv.deescalate:
            next_priv = self.privs.get(current_priv.deescalate_priv, None)
            if not next_priv:
                raise UnknownPrivLevel(
                    "NetworkDriver has no default priv levels, set them or use a network driver"
                )
            self.channel.comms_prompt_pattern = next_priv.pattern
            self.channel.send_inputs(current_priv.deescalate)

    def acquire_priv(self, desired_priv: str) -> None:
        """
        Acquire desired priv level

        Args:
            desired_priv: string name of desired privilege level
                (see scrapli.driver.<driver_category.device_type>.driver for levels)

        Returns:
            N/A  # noqa: DAR202

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
        self, commands: Union[str, List[str]], strip_prompt: bool = True
    ) -> List[Response]:
        """
        Send command(s)

        Args:
            commands: string or list of strings to send to device in privilege exec mode
            strip_prompt: True/False strip prompt from returned output

        Returns:
            responses: list of Scrape Response objects

        Raises:
            N/A

        """
        self.acquire_priv(str(self.default_desired_priv))
        responses = self.channel.send_inputs(commands, strip_prompt)

        # update the response objects with textfsm platform; we do this here because the underlying
        #  channel doesn't know or care about platforms
        for response in responses:
            response.textfsm_platform = self.textfsm_platform

        return responses

    def send_interactive(
        self, inputs: Union[List[str], Tuple[str, str, str, str]], hidden_response: bool = False,
    ) -> List[Response]:
        """
        Send inputs in an interactive fashion; used to handle prompts

        accepts inputs and looks for expected prompt;
        sends the appropriate response, then waits for the "finale"
        returns the results of the interaction

        could be "chained" together to respond to more than a "single" staged prompt

        Args:
            inputs: list or tuple containing strings representing
                channel_input - initial input to send
                expected_prompt - prompt to expect after initial input
                response - response to prompt
                final_prompt - final prompt to expect
            hidden_response: True/False response is hidden (i.e. password input)

        Returns:
            responses: List of Scrape Response objects

        Raises:
            N/A

        """
        self.acquire_priv(str(self.default_desired_priv))
        responses = self.channel.send_inputs_interact(inputs, hidden_response)
        return responses

    def send_configs(
        self, configs: Union[str, List[str]], strip_prompt: bool = True
    ) -> List[Response]:
        """
        Send configuration(s)

        Args:
            configs: string or list of strings to send to device in config mode
            strip_prompt: True/False strip prompt from returned output

        Returns:
            responses: List of Scrape Response objects

        Raises:
            N/A

        """
        self.acquire_priv("configuration")
        responses = self.channel.send_inputs(configs, strip_prompt)
        self.acquire_priv(str(self.default_desired_priv))
        return responses

    def get_prompt(self) -> str:
        """
        Convenience method to get device prompt from Channel

        Args:
            N/A

        Returns:
            str: prompt received from channel.get_prompt

        Raises:
            N/A

        """
        prompt: str = self.channel.get_prompt()
        return prompt

    def open(self) -> None:
        super().open()
        if self.session_pre_login_handler:
            self.session_pre_login_handler(self)
        # send disable paging if needed
        if self.session_disable_paging:
            if callable(self.session_disable_paging):
                self.session_disable_paging(self)
            else:
                self.channel.send_inputs(self.session_disable_paging)

    def close(self) -> None:
        self.transport.write(f"{self.exit_command}{self.comms_return_char}")
        super().close()
