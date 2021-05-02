<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/sanitize.min.css" integrity="sha256-PK9q560IAAa6WVRRh76LtCaI8pjTJ2z11v0miyNNjrs=" crossorigin>
<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/typography.min.css" integrity="sha256-7l/o7C8jubJiy74VsKTidCy1yBkRtiUGbVkYBylBqUg=" crossorigin>
<link rel="stylesheet preload" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/styles/github.min.css" crossorigin>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/highlight.min.js" integrity="sha256-Uv3H6lx7dJmRfRvH8TH6kJD1TSK1aFcwgx+mdg3epi8=" crossorigin></script>
<script>window.addEventListener('DOMContentLoaded', () => hljs.initHighlighting())</script>















#Module scrapli.driver.generic.base_driver

scrapli.driver.generic.base_driver

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
"""scrapli.driver.generic.base_driver"""
from typing import List, Optional, Tuple, Union

from scrapli.exceptions import ScrapliTypeError
from scrapli.helper import resolve_file
from scrapli.response import MultiResponse, Response


class BaseGenericDriver:
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
            ScrapliTypeError: if command is anything but a string

        """
        if not isinstance(command, str):
            raise ScrapliTypeError(
                f"`send_command` expects a single string, got {type(command)}, "
                "to send a list of commands use the `send_commands` method instead."
            )

        response = Response(
            host=host,
            channel_input=command,
            failed_when_contains=failed_when_contains,
        )

        return response

    @staticmethod
    def _post_send_command(
        raw_response: bytes, processed_response: bytes, response: Response
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
        response.record_response(result=processed_response)
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
            ScrapliTypeError: if command is anything but a string

        """
        if not isinstance(commands, list):
            raise ScrapliTypeError(
                f"`send_commands` expects a list of strings, got {type(commands)}, "
                "to send a single command use the `send_command` method instead."
            )

        responses = MultiResponse()

        return responses

    @staticmethod
    def _pre_send_from_file(file: str, caller: str) -> List[str]:
        """
        Handle pre "send_*_from_file" tasks for consistency between sync/async versions

        Args:
            file: string path to file
            caller: name of the calling method for more helpful error message

        Returns:
            list: list of commands/configs read from file

        Raises:
            ScrapliTypeError: if anything but a string is provided for `file`

        """
        if not isinstance(file, str):
            raise ScrapliTypeError(f"`{caller}` expects a string path to a file, got {type(file)}")
        resolved_file = resolve_file(file)

        with open(resolved_file, "r") as f:
            commands = f.read().splitlines()

        return commands

    @classmethod
    def _pre_send_interactive(
        cls,
        host: str,
        interact_events: Union[List[Tuple[str, str]], List[Tuple[str, str, bool]]],
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
        </code>
    </pre>
</details>




## Classes

### BaseGenericDriver



<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
class BaseGenericDriver:
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
            ScrapliTypeError: if command is anything but a string

        """
        if not isinstance(command, str):
            raise ScrapliTypeError(
                f"`send_command` expects a single string, got {type(command)}, "
                "to send a list of commands use the `send_commands` method instead."
            )

        response = Response(
            host=host,
            channel_input=command,
            failed_when_contains=failed_when_contains,
        )

        return response

    @staticmethod
    def _post_send_command(
        raw_response: bytes, processed_response: bytes, response: Response
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
        response.record_response(result=processed_response)
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
            ScrapliTypeError: if command is anything but a string

        """
        if not isinstance(commands, list):
            raise ScrapliTypeError(
                f"`send_commands` expects a list of strings, got {type(commands)}, "
                "to send a single command use the `send_command` method instead."
            )

        responses = MultiResponse()

        return responses

    @staticmethod
    def _pre_send_from_file(file: str, caller: str) -> List[str]:
        """
        Handle pre "send_*_from_file" tasks for consistency between sync/async versions

        Args:
            file: string path to file
            caller: name of the calling method for more helpful error message

        Returns:
            list: list of commands/configs read from file

        Raises:
            ScrapliTypeError: if anything but a string is provided for `file`

        """
        if not isinstance(file, str):
            raise ScrapliTypeError(f"`{caller}` expects a string path to a file, got {type(file)}")
        resolved_file = resolve_file(file)

        with open(resolved_file, "r") as f:
            commands = f.read().splitlines()

        return commands

    @classmethod
    def _pre_send_interactive(
        cls,
        host: str,
        interact_events: Union[List[Tuple[str, str]], List[Tuple[str, str, bool]]],
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
        </code>
    </pre>
</details>


#### Descendants
- scrapli.driver.generic.async_driver.AsyncGenericDriver
- scrapli.driver.generic.sync_driver.GenericDriver