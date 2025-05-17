from typing import Optional
from unittest.mock import Mock

import pytest

from scrapli import Cli
from scrapli.cli_decorators import handle_operation_timeout, handle_operation_timeout_async


def test_handle_operation_timeout_unmodified():
    c = Cli(
        definition_file_or_name="nokia_srl",
        host="localhost",
    )

    c.ffi_mapping = Mock()

    @handle_operation_timeout
    def fooer(cls, *, operation_timeout_ns: Optional[int] = None) -> str:
        return "foo'd"

    c.fooer = fooer

    c.fooer(c)

    assert c.ffi_mapping.options_mapping.session.set_operation_timeout_ns.called is False


@pytest.mark.asyncio
async def test_handle_operation_timeout_async_unmodified():
    c = Cli(
        definition_file_or_name="nokia_srl",
        host="localhost",
    )

    c.ffi_mapping = Mock()

    @handle_operation_timeout_async
    async def fooer(cls, *, operation_timeout_ns: Optional[int] = None) -> str:
        return "foo'd"

    c.fooer = fooer

    await c.fooer(c)

    assert c.ffi_mapping.options_mapping.session.set_operation_timeout_ns.called is False


def test_handle_operation_timeout_modified():
    c = Cli(
        definition_file_or_name="nokia_srl",
        host="localhost",
    )

    c.ffi_mapping = Mock()
    c.ffi_mapping.options_mapping.session.set_operation_timeout_ns = Mock(return_value=0)
    c.ptr = 1

    @handle_operation_timeout
    def fooer(cls, *, operation_timeout_ns: Optional[int] = None) -> str:
        return "foo'd"

    c.fooer = fooer

    c.fooer(c, operation_timeout_ns=1)

    assert c.ffi_mapping.options_mapping.session.set_operation_timeout_ns.called is True


@pytest.mark.asyncio
async def test_handle_operation_timeout_async_modified():
    c = Cli(
        definition_file_or_name="nokia_srl",
        host="localhost",
    )

    c.ffi_mapping = Mock()
    c.ffi_mapping.options_mapping.session.set_operation_timeout_ns = Mock(return_value=0)
    c.ptr = 1

    @handle_operation_timeout_async
    async def fooer(cls, *, operation_timeout_ns: Optional[int] = None) -> str:
        return "foo'd"

    c.fooer = fooer

    await c.fooer(c, operation_timeout_ns=1)

    assert c.ffi_mapping.options_mapping.session.set_operation_timeout_ns.called is True
