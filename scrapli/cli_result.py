"""scrapli.result"""

from typing import Any, TextIO

from scrapli.cli_parse import genie_parse, textfsm_get_template, textfsm_parse
from scrapli.exceptions import ParsingException
from scrapli.helper import bulid_result_preview, unix_nano_timestmap_to_iso

OPERATION_DELIMITER = "__libscrapli__"


class Result:
    """
    Result represents a set of results from some Cli operation(s).

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(  # noqa: PLR0913
        self,
        *,
        host: str,
        port: int,
        inputs: str,
        start_time: int,
        splits: list[int],
        results_raw: bytes,
        results: str,
        results_failed_indicator: str,
        textfsm_platform: str,
        genie_platform: str,
    ) -> None:
        self.host = host
        self.port = port
        self.inputs = inputs.split(OPERATION_DELIMITER)
        self.start_time = start_time
        self.splits = splits
        self.results_raw = results_raw.split(OPERATION_DELIMITER.encode())
        self.results = results.split(OPERATION_DELIMITER)
        self.results_failed_indicator = results_failed_indicator
        self.textfsm_platform = textfsm_platform
        self.genie_platform = genie_platform

    def __str__(self) -> str:
        """
        Magic str method for Result class

        Args:
            N/A

        Returns:
            str: str for class object

        Raises:
            N/A

        """
        return (
            "<-----\n"
            f"\tInput(s)         : {self.inputs}\n"
            f"\tStart Time       : {unix_nano_timestmap_to_iso(timestamp=self.start_time)}\n"
            f"\tEnd Time         : {unix_nano_timestmap_to_iso(timestamp=self.end_time)}\n"
            f"\tElapsed Time (s) : {self.elapsed_time_seconds:.2f}s\n"
            f"\tResult           : {bulid_result_preview(result=self.result)}\n"
            "----->"
        )

    def extend(self, result: "Result") -> None:
        """
        Extends this Result object with another Result object.

        Args:
            result: the result object with which to extend this result object

        Returns:
            N/A

        Raises:
            N/A

        """
        self.inputs.extend(result.inputs)
        self.results_raw.extend(result.results_raw)
        self.results.extend(result.results)
        self.splits.extend(result.splits)

    @property
    def failed(self) -> bool:
        """
        Returns True if any failed indicators were seen, otherwise False.

        Args:
            N/A

        Returns:
            bool: True for failed, otherwise False

        Raises:
            N/A

        """
        return bool(self.results_failed_indicator)

    @property
    def end_time(self) -> int:
        """
        Returns the end time of the operations in unix nano.

        Args:
            N/A

        Returns:
            int: end time in unix nano

        Raises:
            N/A

        """
        if not self.splits:
            # if we had no splits it was a "noop" type op (like enter mode when
            # you are already in the requested mode), so we'll lie and say it
            # was a 1ns op time
            return self.start_time + 1

        return self.splits[-1]

    @property
    def elapsed_time_seconds(self) -> float:
        """
        Returns the number of seconds the operation took.

        Args:
            N/A

        Returns:
            float: duration in seconds

        Raises:
            N/A

        """
        return (self.end_time - self.start_time) / 1_000_000_000

    @property
    def result(self) -> str:
        """
        Returns the results joined on newline chars. Note this does *not* include inputs sent.

        Args:
            N/A

        Returns:
            str: joined results

        Raises:
            N/A

        """
        return "\n".join(self.results)

    @property
    def result_raw(self) -> bytes:
        """
        Returns the results (raw) joined on newline chars. Note this does *not* include inputs sent.

        Args:
            N/A

        Returns:
            bytes: joined results

        Raises:
            N/A

        """
        return b"\n".join(self.results_raw)

    def textfsm_parse(
        self,
        index: int = 0,
        template: str | TextIO | None = None,
        to_dict: bool = True,
    ) -> list[Any] | dict[str, Any]:
        """
        Parse results with textfsm, always return structured data

        Returns an empty list if parsing fails!

        Args:
            index: the index of the result to parse, assumes first/zeroith if not provided
            template: string path to textfsm template or opened textfsm template file
            to_dict: convert textfsm output from list of lists to list of dicts -- basically create
                dict from header and row data so it is easier to read/parse the output

        Returns:
            structured_result: empty list or parsed data from textfsm

        Raises:
            N/A

        """
        if template is None:
            template = textfsm_get_template(
                platform=self.textfsm_platform, command=self.inputs[index]
            )

        if template is None:
            raise ParsingException("no template provided or available for input")

        return textfsm_parse(template=template, output=self.result, to_dict=to_dict)

    def genie_parse(
        self,
        index: int = 0,
    ) -> dict[str, Any] | list[Any]:
        """
        Parse results with genie, always return structured data

        Returns an empty list if parsing fails!

        Args:
            index: the index of the result to parse, assumes first/zeroith if not provided

        Returns:
            structured_result: empty list or parsed data from genie

        Raises:
            N/A

        """
        return genie_parse(self.genie_platform, self.inputs[index], self.results[index])
