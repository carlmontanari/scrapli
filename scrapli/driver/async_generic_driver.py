"""scrapli.driver.async_generic_driver"""
from collections import UserList
from typing import TYPE_CHECKING, Any, List, Optional, Tuple, Union

from scrapli.channel import AsyncChannel
from scrapli.driver.async_driver import AsyncScrape
from scrapli.driver.base_generic_driver import GenericDriverBase
from scrapli.response import Response

if TYPE_CHECKING:
    ScrapliMultiResponse = UserList[Response]  # pylint:  disable=E1136; # pragma:  no cover
else:
    ScrapliMultiResponse = UserList


class AsyncGenericDriver(AsyncScrape, GenericDriverBase):
    def __init__(
        self,
        comms_prompt_pattern: str = r"^\S{0,48}[#>$~@:\]]\s*$",
        comms_ansi: bool = True,
        **kwargs: Any,
    ):
        """
        AsyncGenericDriver Object

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
        self.channel: AsyncChannel

    async def send_command(
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
            N/A

        """
        response = self._pre_send_command(
            host=self.transport.host, command=command, failed_when_contains=failed_when_contains
        )
        raw_response, processed_response = await self.channel.send_input(
            channel_input=command, strip_prompt=strip_prompt
        )
        return self._post_send_command(
            raw_response=raw_response, processed_response=processed_response, response=response
        )

    async def send_commands(
        self,
        commands: List[str],
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        stop_on_failed: bool = False,
    ) -> ScrapliMultiResponse:
        """
        Send multiple commands

        Args:
            commands: list of strings to send to device in privilege exec mode
            strip_prompt: True/False strip prompt from returned output
            failed_when_contains: string or list of strings indicating failure if found in response
            stop_on_failed: True/False stop executing commands if a command fails, returns results
                as of current execution

        Returns:
            ScrapliMultiResponse: Scrapli MultiResponse object

        Raises:
            N/A

        """
        responses = self._pre_send_commands(commands=commands)
        for command in commands:
            response = await self.send_command(
                command=command,
                strip_prompt=strip_prompt,
                failed_when_contains=failed_when_contains,
            )
            responses.append(response)
            if stop_on_failed is True and response.failed is True:
                return responses

        return responses

    async def send_commands_from_file(
        self,
        file: str,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        stop_on_failed: bool = False,
    ) -> ScrapliMultiResponse:
        """
        Send command(s) from file

        Args:
            file: string path to file
            strip_prompt: True/False strip prompt from returned output
            failed_when_contains: string or list of strings indicating failure if found in response
            stop_on_failed: True/False stop executing commands if a command fails, returns results
                as of current execution

        Returns:
            ScrapliMultiResponse: Scrapli MultiResponse object

        Raises:
            N/A

        """
        commands = self._pre_send_commands_from_file(file=file)

        return await self.send_commands(
            commands=commands,
            strip_prompt=strip_prompt,
            failed_when_contains=failed_when_contains,
            stop_on_failed=stop_on_failed,
        )

    async def send_interactive(
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
            privilege_level: ignored in this base class; for LSP reasons for subclasses

        Returns:
            Response: scrapli Response object

        Raises:
            N/A

        """
        _ = privilege_level

        response = self._pre_send_interactive(
            host=self.transport.host,
            interact_events=interact_events,
            failed_when_contains=failed_when_contains,
        )
        raw_response, processed_response = await self.channel.send_inputs_interact(
            interact_events=interact_events
        )
        return self._post_send_command(
            raw_response=raw_response, processed_response=processed_response, response=response
        )

    async def get_prompt(self) -> str:
        """
        Convenience method to get device prompt from Channel

        Args:
            N/A

        Returns:
            str: prompt received from channel.get_prompt

        Raises:
            N/A

        """
        prompt: str = await self.channel.get_prompt()
        return prompt
