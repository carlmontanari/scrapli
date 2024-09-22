"""scrapli.response"""

from collections import UserList
from datetime import datetime
from io import TextIOWrapper
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, TextIO, Union, cast

from scrapli.exceptions import ScrapliCommandFailure
from scrapli.helper import _textfsm_get_template, genie_parse, textfsm_parse, ttp_parse


class Response:
    def __init__(  # pylint: disable=R0917
        self,
        host: str,
        channel_input: str,
        textfsm_platform: str = "",
        genie_platform: str = "",
        failed_when_contains: Optional[Union[str, List[str]]] = None,
    ):
        """
        Scrapli Response

        Store channel_input, resulting output, and start/end/elapsed time information. Attempt to
        determine if command was successful or not and reflect that in a failed attribute.

        Args:
            host: host that was operated on
            channel_input: input that got sent down the channel
            textfsm_platform: ntc-templates friendly platform type
            genie_platform: cisco pyats/genie friendly platform type
            failed_when_contains: list of strings that, if present in final output, represent a
                failed command/interaction

        Returns:
            None

        Raises:
            N/A

        """
        self.host = host
        self.start_time = datetime.now()
        self.finish_time: Optional[datetime] = None
        self.elapsed_time: Optional[float] = None

        self.channel_input = channel_input
        self.textfsm_platform = textfsm_platform
        self.genie_platform = genie_platform
        self.raw_result: bytes = b""
        self.result: str = ""

        if isinstance(failed_when_contains, str):
            failed_when_contains = [failed_when_contains]
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
        Magic repr method for Response class

        Args:
            N/A

        Returns:
            str: repr for class object

        Raises:
            N/A

        """
        return (
            f"{self.__class__.__name__}("
            f"host={self.host!r},"
            f"channel_input={self.channel_input!r},"
            f"textfsm_platform={self.textfsm_platform!r},"
            f"genie_platform={self.genie_platform!r},"
            f"failed_when_contains={self.failed_when_contains!r})"
        )

    def __str__(self) -> str:
        """
        Magic str method for Response class

        Args:
            N/A

        Returns:
            str: str for class object

        Raises:
            N/A

        """
        return f"{self.__class__.__name__} <Success: {not self.failed}>"

    def record_response(self, result: bytes) -> None:
        """
        Record channel_input results and elapsed time of channel input/reading output

        Args:
            result: string result of channel_input

        Returns:
            None

        Raises:
            N/A

        """
        self.finish_time = datetime.now()
        self.elapsed_time = (self.finish_time - self.start_time).total_seconds()
        self.raw_result = result

        try:
            self.result = result.decode()
        except UnicodeDecodeError:
            # sometimes we get some "garbage" characters, the iso encoding seems to handle these
            # better but unclear what the other impact is so we'll just catch exceptions and try
            # this encoding
            self.result = result.decode(encoding="ISO-8859-1")

        if not self.failed_when_contains:
            self.failed = False
        elif all(err not in self.result for err in self.failed_when_contains):
            self.failed = False

    def textfsm_parse_output(
        self,
        template: Union[str, TextIO, None] = None,
        to_dict: bool = True,
        raise_err: bool = False,
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Parse results with textfsm, always return structured data

        Returns an empty list if parsing fails!

        Args:
            template: string path to textfsm template or opened textfsm template file
            to_dict: convert textfsm output from list of lists to list of dicts -- basically create
                dict from header and row data so it is easier to read/parse the output
            raise_err: exceptions in the textfsm parser will raised for the caller to handle

        Returns:
            structured_result: empty list or parsed data from textfsm

        Raises:
            N/A

        """
        if template is None:
            template = _textfsm_get_template(
                platform=self.textfsm_platform, command=self.channel_input
            )

        if template is None:
            return []

        template = cast(Union[str, TextIOWrapper], template)
        return (
            textfsm_parse(
                template=template, output=self.result, to_dict=to_dict, raise_err=raise_err
            )
            or []
        )

    def genie_parse_output(self) -> Union[Dict[str, Any], List[Any]]:
        """
        Parse results with genie, always return structured data

        Returns an empty list if parsing fails!

        Args:
            N/A

        Returns:
            structured_result: empty list or parsed data from genie

        Raises:
            N/A

        """
        return genie_parse(
            platform=self.genie_platform,
            command=self.channel_input,
            output=self.result,
        )

    def ttp_parse_output(
        self, template: Union[str, TextIOWrapper]
    ) -> Union[Dict[str, Any], List[Any]]:
        """
        Parse results with ttp, always return structured data

        Returns an empty list if parsing fails!

        Args:
            template: string path to ttp template or opened ttp template file

        Returns:
            structured_result: empty list or parsed data from ttp

        Raises:
            N/A

        """
        return ttp_parse(template=template, output=self.result) or []

    def raise_for_status(self) -> None:
        """
        Raise a `ScrapliCommandFailure` if command/config failed

        Args:
            N/A

        Returns:
            None

        Raises:
            ScrapliCommandFailure: if command/config failed

        """
        if self.failed:
            raise ScrapliCommandFailure()


if TYPE_CHECKING:
    ScrapliMultiResponse = UserList[Response]  # pylint:  disable=E1136; # pragma:  no cover
else:
    ScrapliMultiResponse = UserList


class MultiResponse(ScrapliMultiResponse):
    def __init__(self, initlist: Optional[Iterable[Any]] = None) -> None:
        """
        Initialize list of responses

        Args:
            initlist: initial list seed data, if any

        Returns:
            None

        Raises:
            N/A

        """
        super().__init__(initlist=initlist)

        self.data: List[Response]

    def __str__(self) -> str:
        """
        Magic str method for MultiResponse class

        Args:
            N/A

        Returns:
            str: str for class object

        Raises:
            N/A

        """
        return (
            f"{self.__class__.__name__} <Success: {not self.failed}; "
            f"Response Elements: {len(self.data)}>"
        )

    @property
    def host(self) -> str:
        """
        Return the host of the multiresponse

        Args:
            N/A

        Returns:
            str: The host of the associated responses

        Raises:
            N/A

        """
        try:
            response = self.data[0]
        except IndexError:
            return ""
        return response.host

    @property
    def failed(self) -> bool:
        """
        Determine if any elements of MultiResponse are failed

        Args:
            N/A

        Returns:
            bool: True for failed

        Raises:
            N/A

        """
        return any(response.failed for response in self.data)

    @property
    def result(self) -> str:
        """
        Build a unified result from all elements of MultiResponse

        Args:
            N/A

        Returns:
            str: Unified result by combining results of all elements of MultiResponse

        Raises:
            N/A

        """
        return "".join(
            "\n".join([response.channel_input, response.result]) for response in self.data
        )

    def raise_for_status(self) -> None:
        """
        Raise a `ScrapliCommandFailure` if any elements are failed

        Args:
            N/A

        Returns:
            None

        Raises:
            ScrapliCommandFailure: if any elements are failed

        """
        if self.failed:
            raise ScrapliCommandFailure()
