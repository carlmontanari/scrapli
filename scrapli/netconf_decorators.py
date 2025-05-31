"""scrapli.netconf_decorators"""

from collections.abc import Awaitable, Callable
from ctypes import c_uint64
from functools import update_wrapper
from typing import TYPE_CHECKING, Concatenate, ParamSpec

from scrapli.exceptions import OptionsException
from scrapli.netconf_result import Result

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

        status = inst.ffi_mapping.options_mapping.session.set_operation_timeout_ns(
            inst._ptr_or_exception(),
            c_uint64(operation_timeout_ns),
        )
        if status != 0:
            raise OptionsException("failed to set session operation timeout")

        res = wrapped(inst, *args, **kwargs)

        status = inst.ffi_mapping.options_mapping.session.set_operation_timeout_ns(
            inst._ptr_or_exception(),
            c_uint64(operation_timeout_ns),
        )
        if status != 0:
            raise OptionsException("failed to set session operation timeout")

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

        status = inst.ffi_mapping.options_mapping.session.set_operation_timeout_ns(
            inst._ptr_or_exception(),
            c_uint64(operation_timeout_ns),
        )
        if status != 0:
            raise OptionsException("failed to set session operation timeout")

        res = await wrapped(inst, *args, **kwargs)

        status = inst.ffi_mapping.options_mapping.session.set_operation_timeout_ns(
            inst._ptr_or_exception(),
            c_uint64(operation_timeout_ns),
        )
        if status != 0:
            raise OptionsException("failed to set session operation timeout")

        return res

    update_wrapper(wrapper=wrapper, wrapped=wrapped)

    return wrapper
