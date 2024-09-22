"""scrapli.decorators"""

import asyncio
import signal
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, wait
from functools import partial, update_wrapper
from logging import Logger, LoggerAdapter
from typing import TYPE_CHECKING, Any, Callable, Tuple

from scrapli.exceptions import ScrapliTimeout
from scrapli.settings import Settings

if TYPE_CHECKING:
    from scrapli.driver import AsyncGenericDriver, GenericDriver  # pragma:  no cover
    from scrapli.transport.base.base_transport import BaseTransport  # pragma:  no cover

if TYPE_CHECKING:
    LoggerAdapterT = LoggerAdapter[Logger]  # pragma:  no cover  # pylint:disable=E1136
else:
    LoggerAdapterT = LoggerAdapter

_IS_WINDOWS = sys.platform.startswith("win")


FUNC_TIMEOUT_MESSAGE_MAP = {
    "channel_authenticate_ssh": "timed out during in channel ssh authentication",
    "channel_authenticate_telnet": "timed out during in channel telnet authentication",
    "get_prompt": "timed out getting prompt",
    "send_input": "timed out sending input to device",
    "send_input_and_read": "timed out sending input to device",
    "send_inputs_interact": "timed out sending interactive input to device",
    "read": "timed out reading from transport",
}


def _get_timeout_message(func_name: str) -> str:
    """
    Return appropriate timeout message for the given function name

    Args:
        func_name: name of function to fetch timeout message for

    Returns:
        str: timeout message

    Raises:
        N/A

    """
    return FUNC_TIMEOUT_MESSAGE_MAP.get(func_name, "unspecified timeout occurred")


def _signal_raise_exception(
    signum: Any, frame: Any, transport: "BaseTransport", logger: LoggerAdapterT, message: str
) -> None:
    """
    Signal method exception handler

    Args:
        signum: singum from the singal handler, unused here
        frame: frame from the signal handler, unused here
        transport: transport to close
        logger: logger to write closing messages to
        message: exception message

    Returns:
        None

    Raises:
        N/A

    """
    _, _ = signum, frame

    return _handle_timeout(transport=transport, logger=logger, message=message)


def _multiprocessing_timeout(  # pylint: disable=R0917
    transport: "BaseTransport",
    logger: LoggerAdapterT,
    timeout: float,
    wrapped_func: Callable[..., Any],
    args: Any,
    kwargs: Any,
) -> Any:
    """
    Return appropriate timeout message for the given function name

    Args:
        transport: transport to close (if timeout occurs)
        logger: logger to write closing message to
        timeout: timeout in seconds
        wrapped_func: function being decorated
        args: function args
        kwargs: function kwargs

    Returns:
        Any: result of the wrapped function

    Raises:
        N/A

    """
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(wrapped_func, *args, **kwargs)
        wait([future], timeout=timeout)
        if not future.done():
            return _handle_timeout(
                transport=transport,
                logger=logger,
                message=_get_timeout_message(func_name=wrapped_func.__name__),
            )
        return future.result()


def _handle_timeout(transport: "BaseTransport", logger: LoggerAdapterT, message: str) -> None:
    """
    Timeout handler method to close connections and raise ScrapliTimeout

    Args:
        transport: transport to close
        logger: logger to write closing message to
        message: message to pass to ScrapliTimeout exception

    Returns:
        None

    Raises:
        ScrapliTimeout: always, if we hit this method we have already timed out!

    """
    if Settings.NO_TERMINATE_ON_TIMEOUT:
        logger.critical(
            "operation timed out, NO_TERMINATE_ON_TIMEOUT is true, not closing connection"
        )
    else:
        logger.critical("operation timed out, closing connection")
        transport.close()

    raise ScrapliTimeout(message)


def _get_transport_logger_timeout(
    cls: Any,
) -> Tuple["BaseTransport", LoggerAdapterT, float]:
    """
    Fetch the transport, logger and timeout from the channel or transport object

    Args:
        cls: Channel or Transport object (self from wrapped function) to grab transport/logger and
            timeout values from

    Returns:
        Tuple: transport, logger, and timeout value

    Raises:
        N/A

    """
    if hasattr(cls, "transport"):
        return (
            cls.transport,
            cls.logger,
            cls._base_channel_args.timeout_ops,  # pylint: disable=W0212
        )

    return (
        cls,
        cls.logger,
        cls._base_transport_args.timeout_transport,  # pylint: disable=W0212
    )


def timeout_wrapper(wrapped_func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Timeout wrapper for transports

    Args:
        wrapped_func: function being wrapped -- must be a method of Channel or Transport

    Returns:
        Any: result of wrapped function

    Raises:
        N/A

    """
    if asyncio.iscoroutinefunction(wrapped_func):

        async def decorate(*args: Any, **kwargs: Any) -> Any:
            transport, logger, timeout = _get_transport_logger_timeout(cls=args[0])

            if not timeout:
                return await wrapped_func(*args, **kwargs)

            try:
                return await asyncio.wait_for(wrapped_func(*args, **kwargs), timeout=timeout)
            except asyncio.TimeoutError:
                _handle_timeout(
                    transport=transport,
                    logger=logger,
                    message=_get_timeout_message(func_name=wrapped_func.__name__),
                )

    else:
        # ignoring type error:
        # "All conditional function variants must have identical signatures"
        # one is sync one is async so never going to be identical here!
        def decorate(*args: Any, **kwargs: Any) -> Any:  # type: ignore
            transport, logger, timeout = _get_transport_logger_timeout(cls=args[0])

            if not timeout:
                return wrapped_func(*args, **kwargs)

            cls_name = transport.__class__.__name__

            if (
                cls_name in ("SystemTransport", "TelnetTransport")
                or _IS_WINDOWS
                or threading.current_thread() is not threading.main_thread()
            ):
                return _multiprocessing_timeout(
                    transport=transport,
                    logger=logger,
                    timeout=timeout,
                    wrapped_func=wrapped_func,
                    args=args,
                    kwargs=kwargs,
                )

            callback = partial(
                _signal_raise_exception,
                transport=transport,
                logger=logger,
                message=_get_timeout_message(wrapped_func.__name__),
            )

            old = signal.signal(signal.SIGALRM, callback)
            signal.setitimer(signal.ITIMER_REAL, timeout)
            try:
                return wrapped_func(*args, **kwargs)
            finally:
                if timeout:
                    signal.setitimer(signal.ITIMER_REAL, 0)
                    signal.signal(signal.SIGALRM, old)

    # ensures that the wrapped function is updated w/ the original functions docs/etc. --
    # necessary for introspection for the auto gen docs to work!
    update_wrapper(wrapper=decorate, wrapped=wrapped_func)
    return decorate


def timeout_modifier(wrapped_func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorate an "operation" to modify the timeout_ops value for duration of that operation

    This decorator wraps send command/config ops and is used to allow users to set a
    `timeout_ops` value for the duration of a single method call -- this makes it so users don't
    need to manually set/reset the value

    Args:
        wrapped_func: function being decorated

    Returns:
        decorate: decorated func

    Raises:
        N/A

    """
    if asyncio.iscoroutinefunction(wrapped_func):

        async def decorate(*args: Any, **kwargs: Any) -> Any:
            driver_instance: "AsyncGenericDriver" = args[0]
            driver_logger = driver_instance.logger

            timeout_ops_kwarg = kwargs.get("timeout_ops", None)

            if timeout_ops_kwarg is None or timeout_ops_kwarg == driver_instance.timeout_ops:
                result = await wrapped_func(*args, **kwargs)
            else:
                driver_logger.info(
                    "modifying driver timeout for current operation, temporary timeout_ops "
                    f"value: '{timeout_ops_kwarg}'"
                )
                base_timeout_ops = driver_instance.timeout_ops
                driver_instance.timeout_ops = kwargs["timeout_ops"]
                try:
                    result = await wrapped_func(*args, **kwargs)
                finally:
                    driver_instance.timeout_ops = base_timeout_ops
            return result

    else:
        # ignoring type error:
        # "All conditional function variants must have identical signatures"
        # one is sync one is async so never going to be identical here!
        def decorate(*args: Any, **kwargs: Any) -> Any:  # type: ignore
            driver_instance: "GenericDriver" = args[0]
            driver_logger = driver_instance.logger

            timeout_ops_kwarg = kwargs.get("timeout_ops", None)

            if timeout_ops_kwarg is None or timeout_ops_kwarg == driver_instance.timeout_ops:
                result = wrapped_func(*args, **kwargs)
            else:
                driver_logger.info(
                    "modifying driver timeout for current operation, temporary timeout_ops "
                    f"value: '{timeout_ops_kwarg}'"
                )
                base_timeout_ops = driver_instance.timeout_ops
                driver_instance.timeout_ops = kwargs["timeout_ops"]
                try:
                    result = wrapped_func(*args, **kwargs)
                finally:
                    driver_instance.timeout_ops = base_timeout_ops
            return result

    # ensures that the wrapped function is updated w/ the original functions docs/etc. --
    # necessary for introspection for the auto gen docs to work!
    update_wrapper(wrapper=decorate, wrapped=wrapped_func)
    return decorate
