"""scrapli.decorators"""
import asyncio
import multiprocessing.pool
import signal
import sys
import threading
from typing import TYPE_CHECKING, Any, Callable, Dict, Union

from scrapli.exceptions import ConnectionNotOpened, ScrapliTimeout

if TYPE_CHECKING:
    from scrapli.channel import AsyncChannel  # pragma: no cover
    from scrapli.channel import Channel  # pragma:  no cover
    from scrapli.transport import Transport  # pragma:  no cover

WIN = sys.platform.startswith("win")


class OperationTimeout:
    def __init__(self, attribute: str, message: str = "") -> None:
        """
        Operation timeout decorator

        Wrap an operation, check class for given attribute and use that for the timeout duration.

        Historically this was not a class and has gone through several iterations... the first
        iteration was using only signal... this was fast and efficient but did not work on windows
        and due to system transport spawning a pty/forking things it would not work for that either.
        Timeouts were then moved to use the multiprocessing method, which works in all cases, and is
        thread safe (unlike signal), however it is very cpu intensive and slightly slower than the
        signal method. This current iteration moved the decorator into a class so it is more orderly
        and easier to break things up into smaller chunks, and importantly now supports both timeout
        methods -- signal and multiprocessing. This will always try to use the signal method, but if
        that is not available (due to windows, system transport, or being in not the main thread),
        it will fallback to the multiprocessing method.

        Args:
            attribute: name of attribute to use to get timeout value (set in the decorator)
            message: optional message to use in timeout exception (set in the decorator)

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.attribute = attribute
        self.message = message

        self.scrapli_obj: Union["Channel", "Transport"]
        self.session_lock: threading.Lock
        self.close: Callable[..., Any]
        self.transport: "Transport"
        self.timeout_duration: int
        self.timeout_exit: bool = True
        self.system_transport: bool = True
        self._use_signals: bool = False

    def __call__(self, wrapped_func: Callable[..., Any]) -> Callable[..., Any]:
        """
        Operation timeout decorator

        This is what is called when the decorator is triggered

        Args:
            wrapped_func: function being decorated

        Returns:
            decorate: decorated func

        Raises:
            N/A

        """
        if asyncio.iscoroutinefunction(wrapped_func):

            async def decorate(*args: Any, **kwargs: Any) -> Any:
                self.scrapli_obj = args[0]
                self.timeout_duration = getattr(self.scrapli_obj, self.attribute, None)

                if not self.timeout_duration:
                    self.scrapli_obj.logger.info(
                        f"Could not find {self.attribute} value of {self.scrapli_obj}, continuing "
                        "without timeout decorator"
                    )
                    return await wrapped_func(*args, **kwargs)

                self.set_scrapli_obj_attrs()
                return await self.asyncio_timeout(
                    wrapped_func=wrapped_func, args=args, kwargs=kwargs
                )

        else:

            def decorate(*args: Any, **kwargs: Any) -> Any:  # type: ignore
                self.scrapli_obj = args[0]
                self.timeout_duration = getattr(self.scrapli_obj, self.attribute, None)

                if not self.timeout_duration:
                    self.scrapli_obj.logger.info(
                        f"Could not find {self.attribute} value of {self.scrapli_obj}, continuing "
                        "without timeout decorator"
                    )
                    return wrapped_func(*args, **kwargs)

                self.set_scrapli_obj_attrs()

                if self._use_signals:
                    return self.signal_timeout(wrapped_func=wrapped_func, args=args, kwargs=kwargs)
                return self.multiprocessing_timeout(
                    wrapped_func=wrapped_func, args=args, kwargs=kwargs
                )

        return decorate

    def set_scrapli_obj_attrs(self) -> None:
        """
        Parent method to set attributes of wrapped functions class object

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        from scrapli.channel import AsyncChannel, Channel  # pylint: disable=C0415
        from scrapli.transport.systemssh import SystemSSHTransport  # pylint: disable=C0415

        if isinstance(self.scrapli_obj, (AsyncChannel, Channel)):
            self.timeout_exit = self.scrapli_obj.transport.timeout_exit
            self.session_lock = self.scrapli_obj.transport.session_lock
            self.close = self.scrapli_obj.transport.close
            self.transport = self.scrapli_obj.transport
        else:
            self.timeout_exit = self.scrapli_obj.timeout_exit
            self.session_lock = self.scrapli_obj.session_lock
            self.close = self.scrapli_obj.close
            self.transport = self.scrapli_obj

        if not isinstance(self.transport, SystemSSHTransport):
            self.system_transport = False

        if (
            self.system_transport
            or WIN
            or threading.current_thread() is not threading.main_thread()
        ):
            self._use_signals = False
        else:
            self._use_signals = True

    def _handle_timeout(self) -> None:
        """
        Timeout handler method to release locks/raise exception consistently between timeout methods

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            ScrapliTimeout: always, if we hit this method we have already timed out!

        """
        if self.timeout_exit:
            self.scrapli_obj.logger.info("timeout_exit is True, closing transport")
            if self.session_lock.locked():
                self.session_lock.release()
            self.close()
        raise ScrapliTimeout(self.message)

    def _signal_raise_exception(self, signum: Any, frame: Any) -> None:
        """
        Signal method exception handler

        Args:
            signum: singum from the singal handler, unused here
            frame: frame from the signal handler, unused here

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        _, _ = signum, frame
        self._handle_timeout()

    async def asyncio_timeout(
        self, wrapped_func: Callable[..., Any], args: Any, kwargs: Any
    ) -> Any:
        """
        Asyncio method for timeouts

        Args:
            wrapped_func: function being decorated
            args: function being decorated args
            kwargs: function being decorated kwargs

        Returns:
            Any: result of decorated function

        Raises:
            N/A

        """
        try:
            return await asyncio.wait_for(
                wrapped_func(*args, **kwargs), timeout=self.timeout_duration
            )
        except asyncio.TimeoutError:
            self._handle_timeout()

    def signal_timeout(self, wrapped_func: Callable[..., Any], args: Any, kwargs: Any) -> Any:
        """
        Signal method for timeouts; does not work with system transport, on windows, or in threads

        Perhaps wondering why, if this doesnt work in so many places, do we have it? Great question!
        Because it is way way way way faster/less cpu intensive than the multiprocessing method!

        Args:
            wrapped_func: function being decorated
            args: function being decorated args
            kwargs: function being decorated kwargs

        Returns:
            Any: result of decorated function

        Raises:
            N/A

        """
        old = signal.signal(signal.SIGALRM, self._signal_raise_exception)
        signal.setitimer(signal.ITIMER_REAL, self.timeout_duration)
        try:
            return wrapped_func(*args, **kwargs)
        finally:
            if self.timeout_duration:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, old)

    def multiprocessing_timeout(
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
        pool = multiprocessing.pool.ThreadPool(processes=1)
        future = pool.apply_async(wrapped_func, args, kwargs)
        try:
            result = future.get(timeout=self.timeout_duration)
            pool.terminate()
            return result
        except multiprocessing.context.TimeoutError:
            pool.terminate()
            self._handle_timeout()


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
