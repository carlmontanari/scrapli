"""scrapli.result"""

from typing import Any, TextIO

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
        return not self.results_failed_indicator

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
            return 0

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

    def textfsm_parse(
        self,
        template: str | TextIO | None = None,
        to_dict: bool = True,
        raise_err: bool = False,
    ) -> dict[str, Any] | list[Any]:
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
        raise NotImplementedError("not yet implemented!")

    def genie_parse(
        self,
    ) -> dict[str, Any] | list[Any]:
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
        raise NotImplementedError("not yet implemented!")
