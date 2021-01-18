"""scrapli.decorators"""
import asyncio
import signal
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, wait
from functools import update_wrapper
from logging import LoggerAdapter
from typing import TYPE_CHECKING, Any, Callable

from scrapli.exceptions import ScrapliTimeout

if TYPE_CHECKING:
    from scrapli.channel import Channel  # pragma:  no cover
    from scrapli.driver import AsyncGenericDriver, GenericDriver  # pragma:  no cover
    from scrapli.transport.base.base_transport import BaseTransport  # pragma:  no cover

_IS_WINDOWS = sys.platform.startswith("win")


class TransportTimeout:
    def __init__(self, message: str = "") -> None:
        """
        Transport timeout decorator

        Args:
            message: accepts message from decorated function to add context to any timeout
                (if a timeout happens!)

        Returns:
            None

        Raises:
            N/A

        """
        self.message = message
        self.transport_instance: "BaseTransport"
        self.transport_timeout_transport = 0.0

    def __call__(self, wrapped_func: Callable[..., Any]) -> Callable[..., Any]:
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
                self.transport_instance = args[0]
                self.transport_timeout_transport = self._get_timeout_transport()

                if not self.transport_timeout_transport:
                    return await wrapped_func(*args, **kwargs)

                try:
                    return await asyncio.wait_for(
                        wrapped_func(*args, **kwargs), timeout=self.transport_timeout_transport
                    )
                except asyncio.TimeoutError:
                    self._handle_timeout()

        else:
            # ignoring type error:
            # "All conditional function variants must have identical signatures"
            # one is sync one is async so never going to be identical here!
            def decorate(*args: Any, **kwargs: Any) -> Any:  # type: ignore
                self.transport_instance = args[0]
                self.transport_timeout_transport = self._get_timeout_transport()

                if not self.transport_timeout_transport:
                    return wrapped_func(*args, **kwargs)

                transport_instance_class_name = self.transport_instance.__class__.__name__

                if (
                    transport_instance_class_name in ("SystemTransport", "TelnetTransport")
                    or _IS_WINDOWS
                    or threading.current_thread() is not threading.main_thread()
                ):
                    return self._multiprocessing_timeout(
                        wrapped_func=wrapped_func,
                        args=args,
                        kwargs=kwargs,
                    )

                old = signal.signal(signal.SIGALRM, self._signal_raise_exception)
                signal.setitimer(signal.ITIMER_REAL, self.transport_timeout_transport)
                try:
                    return wrapped_func(*args, **kwargs)
                finally:
                    if self.transport_timeout_transport:
                        signal.setitimer(signal.ITIMER_REAL, 0)
                        signal.signal(signal.SIGALRM, old)

        # ensures that the wrapped function is updated w/ the original functions docs/etc. --
        # necessary for introspection for the auto gen docs to work!
        update_wrapper(wrapper=decorate, wrapped=wrapped_func)
        return decorate

    def _get_timeout_transport(self) -> float:
        """
        Fetch and return timeout transport from the transport object

        Args:
            N/A

        Returns:
            float: transport timeout value

        Raises:
            N/A

        """
        transport_args = self.transport_instance._base_transport_args  # pylint: disable=W0212
        return transport_args.timeout_transport

    def _handle_timeout(self) -> None:
        """
        Timeout handler method to close connections and raise ScrapliTimeout

        Args:
            N/A

        Returns:
            None

        Raises:
            ScrapliTimeout: always, if we hit this method we have already timed out!

        """
        self.transport_instance.logger.critical("transport operation timed out, closing transport")
        self.transport_instance.close()
        raise ScrapliTimeout(self.message)

    def _multiprocessing_timeout(
        self, wrapped_func: Callable[..., Any], args: Any, kwargs: Any
    ) -> Any:
        """
        Multiprocessing method for timeouts; works in threads and on windows

        Args:
            wrapped_func: function being decorated
            args: function being decorated args
            kwargs: function being decorated kwargs

        Returns:
            Any: result of decorated function

        Raises:
            N/A

        """
        pool = ThreadPoolExecutor(max_workers=1)
        future = pool.submit(wrapped_func, *args, **kwargs)
        wait([future], timeout=self.transport_timeout_transport)
        if not future.done():
            self._handle_timeout()
        return future.result()

    def _signal_raise_exception(self, signum: Any, frame: Any) -> None:
        """
        Signal method exception handler

        Args:
            signum: singum from the singal handler, unused here
            frame: frame from the signal handler, unused here

        Returns:
            None

        Raises:
            N/A

        """
        _, _ = signum, frame
        self._handle_timeout()


class ChannelTimeout:
    def __init__(self, message: str = "") -> None:
        """
        Channel timeout decorator

        Args:
            message: accepts message from decorated function to add context to any timeout
                (if a timeout happens!)

        Returns:
            None

        Raises:
            N/A

        """
        self.message = message
        self.channel_timeout_ops = 0.0
        self.channel_logger: LoggerAdapter
        self.transport_instance: "BaseTransport"

    def __call__(self, wrapped_func: Callable[..., Any]) -> Callable[..., Any]:
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
                channel_instance: "Channel" = args[0]
                self.channel_logger = channel_instance.logger
                self.channel_timeout_ops = (
                    channel_instance._base_channel_args.timeout_ops  # pylint: disable=W0212
                )

                if not self.channel_timeout_ops:
                    return await wrapped_func(*args, **kwargs)

                self.transport_instance = channel_instance.transport

                try:
                    return await asyncio.wait_for(
                        wrapped_func(*args, **kwargs), timeout=self.channel_timeout_ops
                    )
                except asyncio.TimeoutError:
                    self._handle_timeout()

        else:
            # ignoring type error:
            # "All conditional function variants must have identical signatures"
            # one is sync one is async so never going to be identical here!
            def decorate(*args: Any, **kwargs: Any) -> Any:  # type: ignore
                channel_instance: "Channel" = args[0]
                self.channel_logger = channel_instance.logger
                self.channel_timeout_ops = (
                    channel_instance._base_channel_args.timeout_ops  # pylint: disable=W0212
                )

                if not self.channel_timeout_ops:
                    return wrapped_func(*args, **kwargs)

                self.transport_instance = channel_instance.transport
                transport_instance_class_name = self.transport_instance.__class__.__name__

                if (
                    transport_instance_class_name in ("SystemTransport", "TelnetTransport")
                    or _IS_WINDOWS
                    or threading.current_thread() is not threading.main_thread()
                ):
                    return self._multiprocessing_timeout(
                        wrapped_func=wrapped_func,
                        args=args,
                        kwargs=kwargs,
                    )

                old = signal.signal(signal.SIGALRM, self._signal_raise_exception)
                signal.setitimer(signal.ITIMER_REAL, self.channel_timeout_ops)
                try:
                    return wrapped_func(*args, **kwargs)
                finally:
                    if self.channel_timeout_ops:
                        signal.setitimer(signal.ITIMER_REAL, 0)
                        signal.signal(signal.SIGALRM, old)

        # ensures that the wrapped function is updated w/ the original functions docs/etc. --
        # necessary for introspection for the auto gen docs to work!
        update_wrapper(wrapper=decorate, wrapped=wrapped_func)
        return decorate

    def _handle_timeout(self) -> None:
        """
        Timeout handler method to close connections and raise ScrapliTimeout

        Args:
            N/A

        Returns:
            None

        Raises:
            ScrapliTimeout: always, if we hit this method we have already timed out!

        """
        self.channel_logger.critical("channel operation timed out, closing transport")
        self.transport_instance.close()
        raise ScrapliTimeout(self.message)

    def _multiprocessing_timeout(
        self, wrapped_func: Callable[..., Any], args: Any, kwargs: Any
    ) -> Any:
        """
        Multiprocessing method for timeouts; works in threads and on windows

        Args:
            wrapped_func: function being decorated
            args: function being decorated args
            kwargs: function being decorated kwargs

        Returns:
            Any: result of decorated function

        Raises:
            N/A

        """
        pool = ThreadPoolExecutor(max_workers=1)
        future = pool.submit(wrapped_func, *args, **kwargs)
        wait([future], timeout=self.channel_timeout_ops)
        if not future.done():
            self._handle_timeout()
        return future.result()

    def _signal_raise_exception(self, signum: Any, frame: Any) -> None:
        """
        Signal method exception handler

        Args:
            signum: singum from the singal handler, unused here
            frame: frame from the signal handler, unused here

        Returns:
            None

        Raises:
            N/A

        """
        _, _ = signum, frame
        self._handle_timeout()


class TimeoutOpsModifier:
    def __call__(self, wrapped_func: Callable[..., Any]) -> Callable[..., Any]:
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
                    result = await wrapped_func(*args, **kwargs)
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
                    result = wrapped_func(*args, **kwargs)
                    driver_instance.timeout_ops = base_timeout_ops
                return result

        # ensures that the wrapped function is updated w/ the original functions docs/etc. --
        # necessary for introspection for the auto gen docs to work!
        update_wrapper(wrapper=decorate, wrapped=wrapped_func)
        return decorate
