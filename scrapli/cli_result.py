"""scrapli.result"""

from dataclasses import dataclass


@dataclass
class Result:  # pylint: disable=too-many-instance-attributes
    """
    Result holds the result of an operation.

    Args:
        input_:
        host:
        port:
        start_time:
        end_time:
        result_raw:
        result:
        result_failed_indicator:

    Returns:
        None

    Raises:
        N/A

    """

    input_: str
    host: str
    port: int
    start_time: int
    end_time: int
    result_raw: bytes
    result: str
    result_failed_indicator: str

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


@dataclass
class MultiResult:  # pylint: disable=too-many-instance-attributes
    """
    MultiResult holds the result of a multi operation (send_inputs).

    Args:
        host:
        port:
        start_time:
        end_time:
        results:

    Returns:
        None

    Raises:
        N/A

    """

    host: str
    port: int
    start_time: int
    end_time: int
    results: list[Result]
