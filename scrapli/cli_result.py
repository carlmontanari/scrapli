"""scrapli.result"""

OPERATION_DELIMITER = "__libscrapli__"


class Result:  # pylint: disable=too-many-instance-attributes
    """
    Result represents a set of results from some Cli operation(s).

    Args:
        N/A

    Returns:
        None

    Raises:
        N/A

    """

    def __init__(  # pylint: disable=too-many-arguments
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
    ) -> None:
        # TODO str/repr
        # TODO textfsm/genie/ttp
        self.host = host
        self.port = port
        self.inputs = inputs.split(OPERATION_DELIMITER)
        self.start_time = start_time
        self.splits = splits
        self.results_raw = results_raw.split(OPERATION_DELIMITER.encode())
        self.results = results.split(OPERATION_DELIMITER)
        self.results_failed_indicator = results_failed_indicator

    def extend(self, result: "Result") -> None:
        """
        Extends this Result object with another Result object.

        Args:
            N/A

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
        # TODO maybe this changes depending on what indicator stuff looks like
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
