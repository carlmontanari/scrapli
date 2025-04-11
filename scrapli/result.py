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
