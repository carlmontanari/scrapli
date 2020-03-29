"""scrapli.driver.generic_driver"""
from typing import Any, List, Optional, Union

from scrapli.driver.driver import Scrape
from scrapli.response import Response


class GenericDriver(Scrape):
    def __init__(
        self,
        comms_prompt_pattern: str = r"^\S{0,32}[#>$~@:\]]\s*$",
        comms_ansi: bool = True,
        **kwargs: Any,
    ):
        """
        GenericDriver Object

        A generic network driver that will *hopefully* work for a broad variety of devices with
        minimal to no modifications and provide a normal NetworkDriver type experience with
        `send_command(s)`, `get_prompt` and `send_interactive` methods instead of forcing users to
        call Channel methods directly.

        This driver doesn't know anything about privilege levels (or any type of "config modes",
        disabling paging, gracefully exiting, or anything like that, and as such should be treated
        similar to the base `Scrape` object from that perspective.

        Args:
            comms_prompt_pattern: raw string regex pattern -- preferably use `^` and `$` anchors!
                this is the single most important attribute here! if this does not match a prompt,
                scrapli will not work!
                For this GenericDriver the prompt pattern matches a really wide range of things...
                the general pattern is start of line, match any character 0-32 times, then match a
                prompt termination character from the following character set: `#`, `>`, `$`, `~`,
                `@`, `:`, `]`, finally match any or no whitespace till the end of the line. This
                pattern works on all of the "core" platforms and should work on a wide range of
                other devices, however because it is so broad it may also accidentally match too
                many things and cause issues, so be careful!
            comms_ansi: True/False strip comms_ansi characters from output; in the case of the
                GenericDriver, always strip ansi; this may slow things down but will hopefully help
                prevent issues! Obviously can be overridden if desired.
            **kwargs: keyword args to pass to inherited class(es)

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A
        """
        super().__init__(comms_prompt_pattern=comms_prompt_pattern, comms_ansi=comms_ansi, **kwargs)

    def send_command(
        self,
        command: str,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
    ) -> Response:
        """
        Send a command

        Args:
            command: string to send to device in privilege exec mode
            strip_prompt: True/False strip prompt from returned output
            failed_when_contains: string or list of strings indicating failure if found in response

        Returns:
            Response: Scrapli Response object

        Raises:
            TypeError: if command is anything but a string

        """
        if not isinstance(command, str):
            raise TypeError(
                f"`send_command` expects a single string, got {type(command)}. "
                "to send a list of commands use the `send_commands` method instead."
            )

        response = Response(
            self.transport.host, channel_input=command, failed_when_contains=failed_when_contains
        )
        raw_response, processed_response = self.channel.send_input(command, strip_prompt)
        response.record_response(processed_response)
        response.raw_result = raw_response

        return response

    def send_commands(
        self,
        commands: List[str],
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
    ) -> List[Response]:
        """
        Send multiple commands

        Args:
            commands: list of strings to send to device in privilege exec mode
            strip_prompt: True/False strip prompt from returned output
            failed_when_contains: string or list of strings indicating failure if found in response

        Returns:
            responses: list of Scrapli Response objects

        Raises:
            TypeError: if commands is anything but a list

        """
        if not isinstance(commands, list):
            raise TypeError(
                f"`send_commands` expects a list of strings, got {type(commands)}. "
                "to send a single command use the `send_command` method instead."
            )

        responses = []
        for command in commands:
            responses.append(
                self.send_command(
                    command, strip_prompt=strip_prompt, failed_when_contains=failed_when_contains
                )
            )

        return responses

    def send_interactive(self, interact: List[str], hidden_response: bool = False) -> Response:
        """
        Send inputs in an interactive fashion; used to handle prompts

        accepts inputs and looks for expected prompt;
        sends the appropriate response, then waits for the "finale"
        returns the results of the interaction

        could be "chained" together to respond to more than a "single" staged prompt

        Args:
            interact: list of four string elements representing...
                channel_input - initial input to send
                expected_prompt - prompt to expect after initial input
                response - response to prompt
                final_prompt - final prompt to expect
            hidden_response: True/False response is hidden (i.e. password input)

        Returns:
            Response: scrapli Response object

        Raises:
            N/A

        """
        response = self.channel.send_inputs_interact(interact, hidden_response)
        return response

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
