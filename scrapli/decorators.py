"""scrapli.decorators"""
import asyncio
import multiprocessing.pool
from typing import TYPE_CHECKING, Any, Callable, Dict, Union

from scrapli.exceptions import ConnectionNotOpened, ScrapliTimeout

if TYPE_CHECKING:
    from scrapli.channel import AsyncChannel  # pragma: no cover
    from scrapli.channel import Channel  # pragma:  no cover
    from scrapli.transport import Transport  # pragma:  no cover


def operation_timeout(attribute: str, message: str = "") -> Callable[..., Any]:
    """
    Decorate an "operation" -- raises exception if the operation timeout is exceeded

    Wrap an operation, check class for given attribute and use that for the timeout duration.

    Historically this operation timeout decorator used signals instead of the multiprocessing
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
        ScrapliTimeout: if timeout exceeded

    """

    def decorate(wrapped_func: Callable[..., Any]) -> Callable[..., Any]:
        def timeout_wrapper(
            channel_or_transport: Union["Channel", "Transport"],
            *args: Any,
            **kwargs: Dict[str, Union[str, int]],
        ) -> Any:
            # import here to avoid circular dependency
            from scrapli.channel import AsyncChannel, Channel  # pylint: disable=C0415

            timeout_duration = getattr(channel_or_transport, attribute, None)
            if not timeout_duration:
                channel_or_transport.logger.info(
                    f"Could not find {attribute} value of {channel_or_transport}, continuing "
                    "without timeout decorator"
                )
                return wrapped_func(channel_or_transport, *args, **kwargs)

            # as this can be called from transport or channel get the appropriate objects
            # to unlock and close the session. we need to unlock as the close will block
            # forever if the session is locked, and the session very likely is locked while
            # waiting for output from the device
            if isinstance(channel_or_transport, (AsyncChannel, Channel)):
                timeout_exit = channel_or_transport.transport.timeout_exit
                session_lock = channel_or_transport.transport.session_lock
                close = channel_or_transport.transport.close
            else:
                timeout_exit = channel_or_transport.timeout_exit
                session_lock = channel_or_transport.session_lock
                close = channel_or_transport.close

            pool = multiprocessing.pool.ThreadPool(processes=1)
            func_args = [channel_or_transport, *args]
            future = pool.apply_async(wrapped_func, func_args, kwargs)
            try:
                result = future.get(timeout=timeout_duration)
                pool.terminate()
                return result
            except multiprocessing.context.TimeoutError:
                pool.terminate()
                channel_or_transport.logger.info(message)
                if timeout_exit:
                    channel_or_transport.logger.info("timeout_exit is True, closing transport")
                    if session_lock.locked():
                        session_lock.release()
                    close()
                raise ScrapliTimeout(message)

        return timeout_wrapper

    return decorate


def async_operation_timeout(attribute: str, message: str = "") -> Callable[..., Any]:
    """
    Decorate an async "operation" -- raises exception if the operation timeout is exceeded

    Wrap an operation, check class for given attribute and use that for the timeout duration. This
    perhaps could/should just be simply asyncio wait_for, however for consistency purposes and to
    be sure that the right (timeout) attribute is fetched, and importantly for ensuring that the
    connection is closed, this is just an async duplication of `operation_timeout`!

    Args:
        attribute: attribute to inspect in class (to set timeout duration)
        message: optional message to pass when decorating a non-standard operation such as telnet
            login (as opposed to "normal" channel operations)

    Returns:
        decorate: wrapped function

    Raises:
        ScrapliTimeout: if timeout exceeded

    """

    def decorate(wrapped_func: Callable[..., Any]) -> Callable[..., Any]:
        async def timeout_wrapper(
            channel_or_transport: Union["AsyncChannel", "Transport"],
            *args: Any,
            **kwargs: Dict[str, Union[str, int]],
        ) -> Any:
            # import here to avoid circular dependency
            from scrapli.channel import AsyncChannel  # pylint: disable=C0415

            timeout_duration = getattr(channel_or_transport, attribute, None)
            if not timeout_duration:
                channel_or_transport.logger.info(
                    f"Could not find {attribute} value of {channel_or_transport}, continuing "
                    "without timeout decorator"
                )
                return await wrapped_func(channel_or_transport, *args, **kwargs)

            # as this can be called from transport or channel get the appropriate objects
            # to unlock and close the session. we need to unlock as the close will block
            # forever if the session is locked, and the session very likely is locked while
            # waiting for output from the device
            if isinstance(channel_or_transport, AsyncChannel):
                timeout_exit = channel_or_transport.transport.timeout_exit
                session_lock = channel_or_transport.transport.session_lock
                close = channel_or_transport.transport.close
            else:
                timeout_exit = channel_or_transport.timeout_exit
                session_lock = channel_or_transport.session_lock
                close = channel_or_transport.close

            try:
                return await asyncio.wait_for(
                    wrapped_func(channel_or_transport, *args, **kwargs), timeout=timeout_duration
                )
            except asyncio.TimeoutError:
                channel_or_transport.logger.info(message)
                if timeout_exit:
                    channel_or_transport.logger.info("timeout_exit is True, closing transport")
                    if session_lock.locked():
                        session_lock.release()
                        close()
                raise ScrapliTimeout(message)

        return timeout_wrapper

    return decorate


def requires_open_session() -> Callable[..., Any]:
    """
    Decorate an "operation" to require that the underlying scrapli session has been opened

    Args:
        N/A

    Returns:
        decorate: wrapped function

    Raises:
        ConnectionNotOpened: if scrapli connection has not been opened yet

    """

    def decorate(wrapped_func: Callable[..., Any]) -> Callable[..., Any]:
        def requires_open_session_wrapper(
            *args: Union[str, int], **kwargs: Dict[str, Union[str, int]],
        ) -> Any:
            try:
                return wrapped_func(*args, **kwargs)
            except AttributeError:
                raise ConnectionNotOpened(
                    "Attempting to call method that requires an open connection, but connection is "
                    "not open. Call the `.open()` method of your connection object, or use a "
                    "context manager to ensue your connection has been opened."
                )

        return requires_open_session_wrapper

    return decorate
