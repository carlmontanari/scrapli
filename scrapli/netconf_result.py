"""scrapli.result"""

from dataclasses import dataclass


@dataclass
class Result:
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
        rpc_warnings:
        rpc_errors:

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
    rpc_warnings: str
    rpc_errors: str
