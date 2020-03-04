"""scrapli.decorators"""
import logging
from concurrent.futures import ThreadPoolExecutor, wait
from typing import TYPE_CHECKING, Any, Callable, Dict, Union

if TYPE_CHECKING:
    from scrapli.channel import Channel
    from scrapli.transport import Transport

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
            channel_or_transport: Union["Channel", "Transport"],
            *args: Union[str, int],
            **kwargs: Dict[str, Union[str, int]],
        ) -> Any:
            # import here to avoid circular dependency
            from scrapli.channel import Channel  # pylint: disable=C0415

            timeout_duration = getattr(channel_or_transport, attribute, None)
            if not timeout_duration:
                LOG.error(
                    f"Could not find {attribute} value of {channel_or_transport}, continuing "
                    "without timeout decorator"
                )
                return wrapped_func(channel_or_transport, *args, **kwargs)

            # as this can be called from transport or channel get the appropriate objects
            # to unlock and close the session. we need to unlock as the close will block
            # forever if the session is locked, and the session very likely is locked while
            # waiting for output from the device
            if isinstance(channel_or_transport, Channel):
                timeout_exit = channel_or_transport.transport.timeout_exit
                session_lock = channel_or_transport.transport.session_lock
                close = channel_or_transport.transport.close
            else:
                timeout_exit = channel_or_transport.timeout_exit
                session_lock = channel_or_transport.session_lock
                close = channel_or_transport.close

            pool = ThreadPoolExecutor(max_workers=1)
            future = pool.submit(wrapped_func, channel_or_transport, *args, **kwargs)
            wait([future], timeout=timeout_duration)
            if not future.done():
                LOG.info(message)
                if timeout_exit:
                    LOG.info("timeout_exit is True, closing transport")
                    if session_lock.locked():
                        session_lock.release()
                    close()
                raise TimeoutError(message)
            return future.result()

        return timeout_wrapper

    return decorate
