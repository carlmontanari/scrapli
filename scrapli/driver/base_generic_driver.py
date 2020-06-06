"""scrapli.driver.base_generic_driver"""
from typing import List, Optional, Tuple, Union

from scrapli.helper import resolve_file
from scrapli.response import MultiResponse, Response


class GenericDriverBase:
    """
    GenericDriverBase Object

    A generic network driver that will *hopefully* work for a broad variety of devices with
    minimal to no modifications and provide a normal NetworkDriver type experience with
    `send_command(s)`, `get_prompt` and `send_interactive` methods instead of forcing users to
    call Channel methods directly.

    This driver doesn't know anything about privilege levels (or any type of "config modes",
    disabling paging, gracefully exiting, or anything like that, and as such should be treated
    similar to the base `Scrape` object from that perspective.

    """

    @staticmethod
    def _pre_send_command(
        host: str, command: str, failed_when_contains: Optional[Union[str, List[str]]] = None
    ) -> Response:
        """
        Handle pre "send_command" tasks for consistency between sync/async versions

        Args:
            host: string name of the host
            command: string to send to device in privilege exec mode
            failed_when_contains: string or list of strings indicating failure if found in response

        Returns:
            Response: Scrapli Response object

        Raises:
            TypeError: if command is anything but a string

        """
        if not isinstance(command, str):
            raise TypeError(
                f"`send_command` expects a single string, got {type(command)}, "
                "to send a list of commands use the `send_commands` method instead."
            )

        response = Response(
            host=host, channel_input=command, failed_when_contains=failed_when_contains,
        )

        return response

    @staticmethod
    def _post_send_command(
        raw_response: str, processed_response: str, response: Response
    ) -> Response:
        """
        Handle post "send_command" tasks for consistency between sync/async versions

        Args:
            raw_response: raw response returned from the channel
            processed_response: processed response returned from the channel
            response: response object to update with channel results

        Returns:
            Response: Scrapli Response object

        Raises:
            N/A

        """
        response._record_response(result=processed_response)  # pylint: disable=W0212
        response.raw_result = raw_response
        return response

    @staticmethod
    def _pre_send_commands(commands: List[str]) -> MultiResponse:
        """
        Handle pre "send_command" tasks for consistency between sync/async versions

        Args:
            commands: list of strings to send to device in privilege exec mode

        Returns:
            MultiResponse: Scrapli MultiResponse object

        Raises:
            TypeError: if command is anything but a string

        """
        if not isinstance(commands, list):
            raise TypeError(
                f"`send_commands` expects a list of strings, got {type(commands)}, "
                "to send a single command use the `send_command` method instead."
            )

        responses = MultiResponse()

        return responses

    @staticmethod
    def _pre_send_commands_from_file(file: str) -> List[str]:
        """
        Handle pre "send_commands_from_file" tasks for consistency between sync/async versions

        Args:
            file: string path to file

        Returns:
            commands: list of commands read from file

        Raises:
            TypeError: if anything but a string is provided for `file`

        """
        if not isinstance(file, str):
            raise TypeError(
                f"`send_commands_from_file` expects a string path to a file, got {type(file)}"
            )
        resolved_file = resolve_file(file)

        with open(resolved_file, "r") as f:
            commands = f.read().splitlines()

        return commands

    @classmethod
    def _pre_send_interactive(
        cls,
        host: str,
        interact_events: List[Tuple[str, str, Optional[bool]]],
        failed_when_contains: Optional[Union[str, List[str]]] = None,
    ) -> Response:
        """
        Handle pre "send_interactive" tasks for consistency between sync/async versions

        Args:
            host: string name of the host
            interact_events: list of tuples containing the "interactions" with the device
                each list element must have an input and an expected response, and may have an
                optional bool for the third and final element -- the optional bool specifies if the
                input that is sent to the device is "hidden" (ex: password), if the hidden param is
                not provided it is assumed the input is "normal" (not hidden)
            failed_when_contains: string or list of strings indicating failure if found in response

        Returns:
            Response: Scrapli Response object

        Raises:
            N/A

        """
        joined_input = ", ".join([event[0] for event in interact_events])
        return cls._pre_send_command(
            host=host, command=joined_input, failed_when_contains=failed_when_contains
        )
