from unittest.mock import Mock

import pytest

from scrapli import Netconf
from scrapli.netconf_decorators import handle_operation_timeout, handle_operation_timeout_async


def test_handle_operation_timeout_unmodified():
    n = Netconf(
        host="localhost",
    )

    n.ffi_mapping = Mock()

    @handle_operation_timeout
    def fooer(cls, *, operation_timeout_ns: int | None = None) -> str:
        return "foo'd"

    n.fooer = fooer

    n.fooer(n)

    assert n.ffi_mapping.options_mapping.session.set_operation_timeout_ns.called is False


@pytest.mark.asyncio
async def test_handle_operation_timeout_async_unmodified():
    n = Netconf(
        host="localhost",
    )

    n.ffi_mapping = Mock()

    @handle_operation_timeout_async
    async def fooer(cls, *, operation_timeout_ns: int | None = None) -> str:
        return "foo'd"

    n.fooer = fooer

    await n.fooer(n)

    assert n.ffi_mapping.options_mapping.session.set_operation_timeout_ns.called is False


def test_handle_operation_timeout_modified():
    n = Netconf(
        host="localhost",
    )

    n.ffi_mapping = Mock()
    n.ffi_mapping.options_mapping.session.set_operation_timeout_ns = Mock(return_value=0)
    n.ptr = 1

    @handle_operation_timeout
    def fooer(cls, *, operation_timeout_ns: int | None = None) -> str:
        return "foo'd"

    n.fooer = fooer

    n.fooer(n, operation_timeout_ns=1)

    assert n.ffi_mapping.options_mapping.session.set_operation_timeout_ns.called is True


@pytest.mark.asyncio
async def test_handle_operation_timeout_async_modified():
    n = Netconf(
        host="localhost",
    )

    n.ffi_mapping = Mock()
    n.ffi_mapping.options_mapping.session.set_operation_timeout_ns = Mock(return_value=0)
    n.ptr = 1

    @handle_operation_timeout_async
    async def fooer(cls, *, operation_timeout_ns: int | None = None) -> str:
        return "foo'd"

    n.fooer = fooer

    await n.fooer(n, operation_timeout_ns=1)

    assert n.ffi_mapping.options_mapping.session.set_operation_timeout_ns.called is True
