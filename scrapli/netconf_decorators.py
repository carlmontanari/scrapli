"""scrapli.netconf_decorators"""

from collections.abc import Awaitable, Callable
from ctypes import c_uint64
from functools import update_wrapper
from typing import TYPE_CHECKING, Concatenate, ParamSpec

from scrapli.netconf_result import Result
from scrapli.session import DEFAULT_OPERATION_TIMEOUT_NS

if TYPE_CHECKING:
    from scrapli.netconf import Netconf

P = ParamSpec("P")


def handle_operation_timeout(
    wrapped: Callable[Concatenate["Netconf", P], Result],
) -> Callable[Concatenate["Netconf", P], Result]:
    """
    Wraps a Netconf operation and sets the timeout value for the duration of the operation

    Args:
        wrapped: the operation function

    Returns:
        callable: the wrapper function

    Raises:
        N/A

    """

    def wrapper(inst: "Netconf", /, *args: P.args, **kwargs: P.kwargs) -> Result:
        """
        The operation timeout wrapper

        Args:
            inst: the Netconf instance
            args: the arguments to pass to the wrapped function
            kwargs: the keyword arguments to pass to the wrapped function

        Returns:
            Result: the result of the wrapped function

        Raises:
            OptionsException: if the operation timeout failed to set

        """
        operation_timeout_ns = kwargs.get("operation_timeout_ns")
        if operation_timeout_ns is None:
            return wrapped(inst, *args, **kwargs)

        if operation_timeout_ns == inst.session_options.operation_timeout_ns:
            return wrapped(inst, *args, **kwargs)

        if not isinstance(operation_timeout_ns, int):
            # ignore an invalid type for the timeout
            return wrapped(inst, *args, **kwargs)

        inst.ffi_mapping.session_mapping.set_operation_timeout_ns(
            inst._ptr_or_exception(),
            c_uint64(operation_timeout_ns),
        )

        try:
            res = wrapped(inst, *args, **kwargs)
        except Exception:
            raise
        finally:
            inst.ffi_mapping.session_mapping.set_operation_timeout_ns(
                inst._ptr_or_exception(),
                c_uint64(inst.session_options.operation_timeout_ns or DEFAULT_OPERATION_TIMEOUT_NS),
            )

        return res

    update_wrapper(wrapper=wrapper, wrapped=wrapped)

    return wrapper


def handle_operation_timeout_async(
    wrapped: Callable[Concatenate["Netconf", P], Awaitable[Result]],
) -> Callable[Concatenate["Netconf", P], Awaitable[Result]]:
    """
    Wraps a Netconf operation and sets the timeout value for the duration of the operation

    Args:
        wrapped: the operation function

    Returns:
        callable: the wrapper function

    Raises:
        N/A

    """

    async def wrapper(inst: "Netconf", /, *args: P.args, **kwargs: P.kwargs) -> Result:
        """
        The operation timeout wrapper

        Args:
            inst: the Netconf instance
            args: the arguments to pass to the wrapped function
            kwargs: the keyword arguments to pass to the wrapped function

        Returns:
            Result: the result of the wrapped function

        Raises:
            OptionsException: if the operation timeout failed to set

        """
        operation_timeout_ns = kwargs.get("operation_timeout_ns")
        if operation_timeout_ns is None:
            return await wrapped(inst, *args, **kwargs)

        if operation_timeout_ns == inst.session_options.operation_timeout_ns:
            return await wrapped(inst, *args, **kwargs)

        if not isinstance(operation_timeout_ns, int):
            # ignore an invalid type for the timeout
            return await wrapped(inst, *args, **kwargs)

        inst.ffi_mapping.session_mapping.set_operation_timeout_ns(
            inst._ptr_or_exception(),
            c_uint64(operation_timeout_ns),
        )

        try:
            res = await wrapped(inst, *args, **kwargs)
        except Exception:
            raise
        finally:
            inst.ffi_mapping.session_mapping.set_operation_timeout_ns(
                inst._ptr_or_exception(),
                c_uint64(inst.session_options.operation_timeout_ns or DEFAULT_OPERATION_TIMEOUT_NS),
            )

        return res

    update_wrapper(wrapper=wrapper, wrapped=wrapped)

    return wrapper
