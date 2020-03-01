"""scrapli.decorators"""
import logging
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Any, Callable, Dict, Union

LOG = logging.getLogger("scrapli")


def operation_timeout(attribute: str, message: str = "") -> Callable[..., Any]:
    """
    Decorate an "operation" -- raises exception if the operation timeout is exceeded

    Wrap an operation, check class for given attribute and use that for the timeout duration.

    Historically this operation timeout decorator used signals instead of the concurrent_futures
    seen here. The signals method was probably a bit more elegant, however there were issues with
    supporting the system transport as system transport subprocess/ptyprocess components spawn
    threads of their own, and signals must operate in the main thread.

    Args:
        attribute: attribute to inspect in class (to set timeout duration)
        message: optional message to pass when decorating a non-standard operation such as telnet
            login (as opposed to "normal" channel operations)

    Returns:
        decorate: wrapped function

    Raises:
        TimeoutError: if timeout exceeded

    """

    def decorate(wrapped_func: Callable[..., Any]) -> Callable[..., Any]:
        def timeout_wrapper(
            self: object, *args: Union[str, int], **kwargs: Dict[str, Union[str, int]]
        ) -> Any:
            timeout_duration = getattr(self, attribute, None)
            if not timeout_duration:
                return wrapped_func(self, *args, **kwargs)

            pool = ThreadPoolExecutor(max_workers=1)
            future = pool.submit(wrapped_func, self, *args, **kwargs)
            wait([future], timeout=timeout_duration)
            if not future.done():
                raise TimeoutError(message)
            return future.result()

        return timeout_wrapper

    return decorate
