<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/sanitize.min.css" integrity="sha256-PK9q560IAAa6WVRRh76LtCaI8pjTJ2z11v0miyNNjrs=" crossorigin>
<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/typography.min.css" integrity="sha256-7l/o7C8jubJiy74VsKTidCy1yBkRtiUGbVkYBylBqUg=" crossorigin>
<link rel="stylesheet preload" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/styles/github.min.css" crossorigin>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/highlight.min.js" integrity="sha256-Uv3H6lx7dJmRfRvH8TH6kJD1TSK1aFcwgx+mdg3epi8=" crossorigin></script>
<script>window.addEventListener('DOMContentLoaded', () => hljs.initHighlighting())</script>















#Module scrapli.response

scrapli.response

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
"""scrapli.response"""
from collections import UserList
from datetime import datetime
from io import TextIOWrapper
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from scrapli.exceptions import ScrapliCommandFailure
from scrapli.helper import _textfsm_get_template, genie_parse, textfsm_parse, ttp_parse


class Response:
    def __init__(
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
        return f"Response <Success: {str(not self.failed)}>"

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
        return f"Response <Success: {str(not self.failed)}>"

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
        self.result = result.decode()
        if not self.failed_when_contains:
            self.failed = False
        elif not any(err in self.result for err in self.failed_when_contains):
            self.failed = False

    def textfsm_parse_output(self, to_dict: bool = True) -> Union[Dict[str, Any], List[Any]]:
        """
        Parse results with textfsm, always return structured data

        Returns an empty list if parsing fails!

        Args:
            to_dict: convert textfsm output from list of lists to list of dicts -- basically create
                dict from header and row data so it is easier to read/parse the output

        Returns:
            structured_result: empty list or parsed data from textfsm

        Raises:
            N/A

        """
        template = _textfsm_get_template(platform=self.textfsm_platform, command=self.channel_input)
        if isinstance(template, TextIOWrapper):
            structured_result = (
                textfsm_parse(template=template, output=self.result, to_dict=to_dict) or []
            )
        else:
            structured_result = []
        return structured_result

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
        structured_result = genie_parse(
            platform=self.genie_platform, command=self.channel_input, output=self.result
        )
        return structured_result

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
        structured_result = ttp_parse(template=template, output=self.result) or []
        return structured_result

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
    def __repr__(self) -> str:
        """
        Magic repr method for MultiResponse class

        Args:
            N/A

        Returns:
            str: repr for class object

        Raises:
            N/A

        """
        return (
            f"MultiResponse <Success: {str(not self.failed)}; "
            f"Response Elements: {len(self.data)}>"
        )

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
            f"MultiResponse <Success: {str(not self.failed)}; "
            f"Response Elements: {len(self.data)}>"
        )

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
        if any(response.failed for response in self.data):
            return True
        return False

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
        result = ""
        for response in self.data:
            result += "\n".join([response.channel_input, response.result])
        return result

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
        </code>
    </pre>
</details>




## Classes

### MultiResponse


```text
A more or less complete user-defined wrapper around list objects.
```

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
class MultiResponse(ScrapliMultiResponse):
    def __repr__(self) -> str:
        """
        Magic repr method for MultiResponse class

        Args:
            N/A

        Returns:
            str: repr for class object

        Raises:
            N/A

        """
        return (
            f"MultiResponse <Success: {str(not self.failed)}; "
            f"Response Elements: {len(self.data)}>"
        )

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
            f"MultiResponse <Success: {str(not self.failed)}; "
            f"Response Elements: {len(self.data)}>"
        )

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
        if any(response.failed for response in self.data):
            return True
        return False

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
        result = ""
        for response in self.data:
            result += "\n".join([response.channel_input, response.result])
        return result

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
        </code>
    </pre>
</details>


#### Ancestors (in MRO)
- collections.UserList
- collections.abc.MutableSequence
- collections.abc.Sequence
- collections.abc.Reversible
- collections.abc.Collection
- collections.abc.Sized
- collections.abc.Iterable
- collections.abc.Container
#### Instance variables

    
`failed: bool`

```text
Determine if any elements of MultiResponse are failed

Args:
    N/A

Returns:
    bool: True for failed

Raises:
    N/A
```



    
`result: str`

```text
Build a unified result from all elements of MultiResponse

Args:
    N/A

Returns:
    str: Unified result by combining results of all elements of MultiResponse

Raises:
    N/A
```


#### Methods

    

##### raise_for_status
`raise_for_status(self) ‑> NoneType`

```text
Raise a `ScrapliCommandFailure` if any elements are failed

Args:
    N/A

Returns:
    None

Raises:
    ScrapliCommandFailure: if any elements are failed
```





### Response


```text
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
```

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
class Response:
    def __init__(
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
        return f"Response <Success: {str(not self.failed)}>"

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
        return f"Response <Success: {str(not self.failed)}>"

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
        self.result = result.decode()
        if not self.failed_when_contains:
            self.failed = False
        elif not any(err in self.result for err in self.failed_when_contains):
            self.failed = False

    def textfsm_parse_output(self, to_dict: bool = True) -> Union[Dict[str, Any], List[Any]]:
        """
        Parse results with textfsm, always return structured data

        Returns an empty list if parsing fails!

        Args:
            to_dict: convert textfsm output from list of lists to list of dicts -- basically create
                dict from header and row data so it is easier to read/parse the output

        Returns:
            structured_result: empty list or parsed data from textfsm

        Raises:
            N/A

        """
        template = _textfsm_get_template(platform=self.textfsm_platform, command=self.channel_input)
        if isinstance(template, TextIOWrapper):
            structured_result = (
                textfsm_parse(template=template, output=self.result, to_dict=to_dict) or []
            )
        else:
            structured_result = []
        return structured_result

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
        structured_result = genie_parse(
            platform=self.genie_platform, command=self.channel_input, output=self.result
        )
        return structured_result

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
        structured_result = ttp_parse(template=template, output=self.result) or []
        return structured_result

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
        </code>
    </pre>
</details>


#### Methods

    

##### genie_parse_output
`genie_parse_output(self) ‑> Union[Dict[str, Any], List[Any]]`

```text
Parse results with genie, always return structured data

Returns an empty list if parsing fails!

Args:
    N/A

Returns:
    structured_result: empty list or parsed data from genie

Raises:
    N/A
```



    

##### raise_for_status
`raise_for_status(self) ‑> NoneType`

```text
Raise a `ScrapliCommandFailure` if command/config failed

Args:
    N/A

Returns:
    None

Raises:
    ScrapliCommandFailure: if command/config failed
```



    

##### record_response
`record_response(self, result: bytes) ‑> NoneType`

```text
Record channel_input results and elapsed time of channel input/reading output

Args:
    result: string result of channel_input

Returns:
    None

Raises:
    N/A
```



    

##### textfsm_parse_output
`textfsm_parse_output(self, to_dict: bool = True) ‑> Union[Dict[str, Any], List[Any]]`

```text
Parse results with textfsm, always return structured data

Returns an empty list if parsing fails!

Args:
    to_dict: convert textfsm output from list of lists to list of dicts -- basically create
        dict from header and row data so it is easier to read/parse the output

Returns:
    structured_result: empty list or parsed data from textfsm

Raises:
    N/A
```



    

##### ttp_parse_output
`ttp_parse_output(self, template: Union[str, _io.TextIOWrapper]) ‑> Union[Dict[str, Any], List[Any]]`

```text
Parse results with ttp, always return structured data

Returns an empty list if parsing fails!

Args:
    template: string path to ttp template or opened ttp template file

Returns:
    structured_result: empty list or parsed data from ttp

Raises:
    N/A
```