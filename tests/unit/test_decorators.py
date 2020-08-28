import asyncio
import time
from threading import Lock

import pytest

from scrapli.decorators import OperationTimeout, TimeoutModifier, requires_open_session
from scrapli.driver import AsyncScrape, Scrape
from scrapli.driver.base_driver import ScrapeBase
from scrapli.exceptions import ConnectionNotOpened, ScrapliTimeout


class SlowClass(ScrapeBase):
    def __init__(self):
        # subclass base scrape to have a logger setup and such
        # set transport to telnet as it works on all platforms and is standard library!
        super().__init__(host="localhost", transport="telnet")
        self.timeout_test = 0.25
        self.timeout_exit = True
        self.session_lock = Lock()
        self.session_lock.acquire()

    @OperationTimeout("timeout_test")
    def slow_function(self):
        time.sleep(1)

    @OperationTimeout("timeout_test")
    def fast_function(self):
        return "fast"

    @OperationTimeout("non_existent_class_attr")
    def confused_function(self):
        return "fast"

    @OperationTimeout("timeout_test")
    async def async_slow_function(self):
        await asyncio.sleep(1)

    @OperationTimeout("timeout_test")
    async def async_fast_function(self):
        return "fast"

    @OperationTimeout("non_existent_class_attr")
    async def async_confused_function(self):
        return "fast"

    def close(self):
        return

    @requires_open_session()
    def raise_attribute_error(self):
        raise AttributeError


def test_operation_timeout_timeout():
    slow = SlowClass()
    with pytest.raises(ScrapliTimeout):
        slow.slow_function()


def test_operation_timeout_success():
    slow = SlowClass()
    result = slow.fast_function()
    assert result == "fast"


def test_operation_timeout_no_class_attr():
    slow = SlowClass()
    result = slow.confused_function()
    assert result == "fast"


@pytest.mark.asyncio
async def test_async_operation_timeout_timeout():
    slow = SlowClass()
    with pytest.raises(ScrapliTimeout):
        await slow.async_slow_function()


@pytest.mark.asyncio
async def test_async_operation_timeout_success():
    slow = SlowClass()
    result = await slow.async_fast_function()
    assert result == "fast"


@pytest.mark.asyncio
async def test_async_operation_timeout_no_class_attr():
    slow = SlowClass()
    result = await slow.async_confused_function()
    assert result == "fast"


def test_requires_open_session():
    slow = SlowClass()
    with pytest.raises(ConnectionNotOpened) as exc:
        slow.raise_attribute_error()
    assert (
        str(exc.value)
        == "Attempting to call method that requires an open connection, but connection is not open. "
        "Call the `.open()` method of your connection object, or use a context manager to ensue "
        "your connection has been opened."
    )


@pytest.mark.parametrize(
    "timeout_ops",
    [
        999,
        30,
        None,
    ],
    ids=["timeout_modified", "timeout_unchanged", "timeout_not_provided"],
)
def test_timeout_modifier(monkeypatch, timeout_ops):
    scrape = Scrape(host="localhost")
    assert scrape.timeout_ops == 30

    @TimeoutModifier()
    def test_timeout_modifier(cls, timeout_ops):
        return cls.timeout_ops

    # stupid patch but does confirm the timeout modifier works as expected!
    monkeypatch.setattr(Scrape, "open", test_timeout_modifier)
    modified_timeout = scrape.open(timeout_ops=timeout_ops)
    assert modified_timeout == timeout_ops if timeout_ops else 30
    assert scrape.timeout_ops == 30


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "timeout_ops",
    [
        999,
        30,
        None,
    ],
    ids=["timeout_modified", "timeout_unchanged", "timeout_not_provided"],
)
async def test_timeout_modifier_async(monkeypatch, timeout_ops):
    scrape = AsyncScrape(host="localhost", transport="asyncssh")
    assert scrape.timeout_ops == 30

    @TimeoutModifier()
    async def test_timeout_modifier(cls, timeout_ops):
        return cls.timeout_ops

    # stupid patch but does confirm the timeout modifier works as expected!
    monkeypatch.setattr(AsyncScrape, "open", test_timeout_modifier)
    modified_timeout = await scrape.open(timeout_ops=timeout_ops)
    assert modified_timeout == timeout_ops if timeout_ops else 30
    assert scrape.timeout_ops == 30
