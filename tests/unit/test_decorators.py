import asyncio
import time

import pytest

from scrapli.decorators import ChannelTimeout, TimeoutOpsModifier, TransportTimeout
from scrapli.exceptions import ScrapliTimeout


@pytest.mark.parametrize(
    "test_data",
    (
        1,
        0,
    ),
    ids=("timeout_operation", "timeout_disabled"),
)
def test_transport_timeout_sync_signals(monkeypatch, sync_transport_no_abc, test_data):
    timeout_transport = test_data
    sync_transport_no_abc._base_transport_args.timeout_transport = timeout_transport

    @TransportTimeout()
    def _open(cls):
        return cls._base_transport_args.timeout_transport

    # stupid patch but does confirm the timeout modifier works as expected!
    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.open", _open)

    # simply running this to make sure it runs and allows the wrapped function to return nicely
    assert sync_transport_no_abc.open() == timeout_transport


@pytest.mark.parametrize(
    "test_data",
    (
        1,
        0,
    ),
    ids=("timeout_operation", "timeout_disabled"),
)
def test_transport_timeout_sync_multiprocessing(monkeypatch, sync_transport_no_abc, test_data):
    timeout_transport = test_data
    sync_transport_no_abc._base_transport_args.timeout_transport = timeout_transport

    @TransportTimeout()
    def _open(cls):
        return cls._base_transport_args.timeout_transport

    # stupid patch but does confirm the timeout modifier works as expected!
    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.open", _open)
    # just patch _IS_WINDOWS to force using multiprocessing timeout
    monkeypatch.setattr("scrapli.decorators._IS_WINDOWS", True)

    # simply running this to make sure it runs and allows the wrapped function to return nicely
    assert sync_transport_no_abc.open() == timeout_transport


def test_transport_timeout_sync_timed_out_signals(monkeypatch, sync_transport_no_abc):
    sync_transport_no_abc._base_transport_args.timeout_transport = 0.1

    @TransportTimeout()
    def _open(cls):
        time.sleep(0.5)

    # stupid patch but does confirm the timeout modifier works as expected!
    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.open", _open)

    with pytest.raises(ScrapliTimeout):
        sync_transport_no_abc.open()


def test_transport_timeout_sync_timed_out_multiprocessing(monkeypatch, sync_transport_no_abc):
    sync_transport_no_abc._base_transport_args.timeout_transport = 0.1

    @TransportTimeout()
    def _open(cls):
        time.sleep(0.5)

    # stupid patch but does confirm the timeout modifier works as expected!
    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.open", _open)
    # just patch _IS_WINDOWS to force using multiprocessing timeout
    monkeypatch.setattr("scrapli.decorators._IS_WINDOWS", True)

    with pytest.raises(ScrapliTimeout):
        sync_transport_no_abc.open()


@pytest.mark.asyncio
async def test_transport_timeout_async_timed_out(monkeypatch, async_transport_no_abc):
    async_transport_no_abc._base_transport_args.timeout_transport = 0.1

    @TransportTimeout()
    async def _open(cls):
        await asyncio.sleep(0.5)

    # stupid patch but does confirm the timeout modifier works as expected!
    monkeypatch.setattr("scrapli.transport.base.async_transport.AsyncTransport.open", _open)

    with pytest.raises(ScrapliTimeout):
        await async_transport_no_abc.open()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_data",
    (
        1,
        0,
    ),
    ids=("timeout_operation", "timeout_disabled"),
)
async def test_transport_timeout_async(monkeypatch, async_transport_no_abc, test_data):
    timeout_transport = test_data
    async_transport_no_abc._base_transport_args.timeout_transport = timeout_transport

    @TransportTimeout()
    async def _open(cls):
        return cls._base_transport_args.timeout_transport

    # stupid patch but does confirm the timeout modifier works as expected!
    monkeypatch.setattr("scrapli.transport.base.async_transport.AsyncTransport.open", _open)

    # simply running this to make sure it runs and allows the wrapped function to return nicely
    assert await async_transport_no_abc.open() == timeout_transport


@pytest.mark.parametrize(
    "test_data",
    (
        1,
        0,
    ),
    ids=("timeout_operation", "timeout_disabled"),
)
def test_channel_timeout_sync_signals(monkeypatch, sync_channel, test_data):
    timeout_ops = test_data
    sync_channel._base_channel_args.timeout_ops = timeout_ops

    @ChannelTimeout()
    def _send_input(cls):
        return cls._base_channel_args.timeout_ops

    # stupid patch but does confirm the timeout modifier works as expected!
    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.send_input", _send_input)

    # simply running this to make sure it runs and allows the wrapped function to return nicely
    assert sync_channel.send_input() == timeout_ops


@pytest.mark.parametrize(
    "test_data",
    (
        1,
        0,
    ),
    ids=("timeout_operation", "timeout_disabled"),
)
def test_channel_timeout_sync_multiprocessing(monkeypatch, sync_channel, test_data):
    timeout_ops = test_data
    sync_channel._base_channel_args.timeout_ops = timeout_ops

    @ChannelTimeout()
    def _send_input(cls):
        return cls._base_channel_args.timeout_ops

    # stupid patch but does confirm the timeout modifier works as expected!
    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.send_input", _send_input)
    # just patch _IS_WINDOWS to force using multiprocessing timeout
    monkeypatch.setattr("scrapli.decorators._IS_WINDOWS", True)

    # simply running this to make sure it runs and allows the wrapped function to return nicely
    assert sync_channel.send_input() == timeout_ops


def test_channel_timeout_sync_timed_out_signals(monkeypatch, sync_channel):
    sync_channel._base_channel_args.timeout_ops = 0.1

    @ChannelTimeout()
    def _send_input(cls):
        time.sleep(0.5)

    # stupid patch but does confirm the timeout modifier works as expected!
    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.send_input", _send_input)

    with pytest.raises(ScrapliTimeout):
        sync_channel.send_input()


def test_channel_timeout_sync_timed_out_multiprocessing(monkeypatch, sync_channel):
    sync_channel._base_channel_args.timeout_ops = 0.1

    @ChannelTimeout()
    def _send_input(cls):
        time.sleep(0.5)

    # stupid patch but does confirm the timeout modifier works as expected!
    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.send_input", _send_input)

    # just patch _IS_WINDOWS to force using multiprocessing timeout
    monkeypatch.setattr("scrapli.decorators._IS_WINDOWS", True)

    with pytest.raises(ScrapliTimeout):
        sync_channel.send_input()


@pytest.mark.asyncio
async def test_channel_timeout_async_timed_out(monkeypatch, async_channel):
    async_channel._base_channel_args.timeout_ops = 0.1

    @ChannelTimeout()
    async def _send_input(cls):
        await asyncio.sleep(0.5)

    # stupid patch but does confirm the timeout modifier works as expected!
    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.send_input", _send_input)

    with pytest.raises(ScrapliTimeout):
        await async_channel.send_input()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_data",
    (
        1,
        0,
    ),
    ids=("timeout_operation", "timeout_disabled"),
)
async def test_channel_timeout_async(monkeypatch, async_channel, test_data):
    timeout_ops = test_data
    async_channel._base_channel_args.timeout_ops = timeout_ops

    @ChannelTimeout()
    async def _send_input(cls):
        return cls._base_channel_args.timeout_ops

    # stupid patch but does confirm the timeout modifier works as expected!
    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.send_input", _send_input)

    # simply running this to make sure it runs and allows the wrapped function to return nicely
    assert await async_channel.send_input() == timeout_ops


@pytest.mark.parametrize(
    "test_data",
    (
        999,
        30,
        None,
    ),
    ids=("timeout_modified", "timeout_unchanged", "timeout_not_provided"),
)
def test_timeout_modifier(monkeypatch, sync_driver, test_data):
    timeout_ops = test_data
    assert sync_driver.timeout_ops == 30

    @TimeoutOpsModifier()
    def _test_timeout_modifier(cls, timeout_ops):
        return cls.timeout_ops

    # stupid patch but does confirm the timeout modifier works as expected!
    monkeypatch.setattr("scrapli.driver.base.sync_driver.Driver.open", _test_timeout_modifier)

    modified_timeout = sync_driver.open(timeout_ops=timeout_ops)
    assert modified_timeout == timeout_ops if timeout_ops else 30
    assert sync_driver.timeout_ops == 30


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "test_data",
    (
        999,
        30,
        None,
    ),
    ids=("timeout_modified", "timeout_unchanged", "timeout_not_provided"),
)
async def test_timeout_modifier_async(monkeypatch, async_driver, test_data):
    timeout_ops = test_data
    assert async_driver.timeout_ops == 30

    @TimeoutOpsModifier()
    async def _test_timeout_modifier(cls, timeout_ops):
        return cls.timeout_ops

    # stupid patch but does confirm the timeout modifier works as expected!
    monkeypatch.setattr("scrapli.driver.base.async_driver.AsyncDriver.open", _test_timeout_modifier)
    modified_timeout = await async_driver.open(timeout_ops=timeout_ops)
    assert modified_timeout == timeout_ops if timeout_ops else 30
    assert async_driver.timeout_ops == 30
