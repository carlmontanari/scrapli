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
        return bool(self.rpc_errors)

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
