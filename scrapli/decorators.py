"""scrapli.decorators"""
import logging
from typing import Any, Callable, Dict, Union

LOG = logging.getLogger("scrapli")


def operation_timeout(attribute: str, message: str = "") -> Callable[..., Any]:
    """
    Decorate an "operation" -- raises exception if the operation timeout is exceeded

    Wrap an operation, check class for given attribute and use that for the timeout duration.

    Args:
        attribute: attribute to inspect in class (to set timeout duration)
        message: optional message to pass when decorating a non-standard operation such as telnet
            login (as opposed to "normal" channel operations)

    Returns:
        decorate: wrapped function

    Raises:
        TimeoutError: if timeout exceeded

    """
    import signal  # noqa

    def _raise_exception(signum: Any, frame: Any) -> None:
        if message:
            raise TimeoutError(message)
        raise TimeoutError

    def decorate(wrapped_func: Callable[..., Any]) -> Callable[..., Any]:
        def timeout_wrapper(
            self: object, *args: Union[str, int], **kwargs: Dict[str, Union[str, int]]
        ) -> Any:
            timeout_duration = getattr(self, attribute, None)
            if not timeout_duration:
                return wrapped_func(self, *args, **kwargs)
            old = signal.signal(signal.SIGALRM, _raise_exception)
            signal.setitimer(signal.ITIMER_REAL, timeout_duration)
            try:
                return wrapped_func(self, *args, **kwargs)
            finally:
                if timeout_duration:
                    signal.setitimer(signal.ITIMER_REAL, 0)
                    signal.signal(signal.SIGALRM, old)

        return timeout_wrapper

    return decorate
