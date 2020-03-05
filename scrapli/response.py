"""scrapli.response"""
from datetime import datetime
from io import TextIOWrapper
from typing import Any, Dict, List, Optional, Union

from scrapli.helper import _textfsm_get_template, textfsm_parse


class Response:
    def __init__(
        self,
        host: str,
        channel_input: str,
        textfsm_platform: str = "",
        expectation: Optional[str] = None,
        channel_response: Optional[str] = None,
        finale: Optional[str] = None,
        failed_when_contains: Optional[List[str]] = None,
    ):
        """
        Scrapli Response

        Store channel_input, resulting output, and start/end/elapsed time information. Attempt to
        determine if command was successful or not and reflect that in a failed attribute.

        Args:
            host: host that was operated on
            channel_input: input that got sent down the channel
            textfsm_platform: ntc-templates friendly platform type
            expectation: used for send_inputs_interact -- string to expect back from the channel
                after initial input
            channel_response: used for send_inputs_interact -- string to use to respond to expected
                prompt
            finale: string of prompt to look for to know when "done" with interaction
            failed_when_contains: list of strings that, if present in final output, represent a
                failed command/interaction

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A  # noqa

        """
        self.host = host
        self.start_time = datetime.now()
        self.finish_time: Optional[datetime] = None
        self.elapsed_time: Optional[float] = None

        self.channel_input = channel_input
        self.textfsm_platform = textfsm_platform
        self.expectation = expectation
        self.channel_response = channel_response
        self.finale = finale
        self.raw_result: str = ""
        self.result: str = ""

        # for future use -- could add failed when terms in each driver, then check for those strings
        # in results to determine if the command failed, could also set this at send_inputs level
        self.failed_when_contains = failed_when_contains
        self.failed = True

    def __bool__(self) -> bool:
        """
        Magic bool method based on channel_input being failed or not

        Args:
            N/A

        Returns:
            bool: True/False if channel_input failed

        Raises:
            N/A

        """
        return self.failed

    def __repr__(self) -> str:
        """
        Magic repr method for SSH2NetResponse class

        Args:
            N/A

        Returns:
            str: repr for class object

        Raises:
            N/A

        """
        return f"Scrape <Success: {str(not self.failed)}>"

    def __str__(self) -> str:
        """
        Magic str method for SSH2NetResponse class

        Args:
            N/A

        Returns:
            str: str for class object

        Raises:
            N/A

        """
        return f"Scrape <Success: {str(not self.failed)}>"

    def record_response(self, result: str) -> None:
        """
        Record channel_input results and elapsed time of channel input/reading output

        Args:
            result: string result of channel_input

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.finish_time = datetime.now()
        self.elapsed_time = (self.finish_time - self.start_time).total_seconds()
        self.result = result
        # update failed to false after recording results
        self.failed = False

    def textfsm_parse_output(self) -> Union[Dict[str, Any], List[Any]]:
        """
        Parse results with textfsm, assign result to `structured_result`

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        template = _textfsm_get_template(self.textfsm_platform, self.channel_input)
        if isinstance(template, TextIOWrapper):
            structured_result = textfsm_parse(template, self.result) or []
        else:
            structured_result = []
        return structured_result
