import asyncio
import contextlib
import socket
import threading
from pathlib import Path

import pytest

from scrapli import (
    AuthOptions,
    Cli,
    LookupKeyValue,
    Netconf,
    TransportTestOptions,
)
from scrapli.exceptions import (
    CancelledException,
    NotOpenedException,
    SessionException,
    TimeoutException,
)
from scrapli.ffi_types import Cancel
from scrapli.session import Options as SessionOptions

# a recorded session holding an open and a get_prompt -- once both have been replayed the test
# transport has nothing more to read, so the connection is open but the "device" is unresponsive
SILENT_AFTER_GET_PROMPT_FIXTURE = Path(__file__).parent / "fixtures" / "cli" / "get-prompt"

DRIVERS = (Cli, Netconf)
DRIVER_IDS = ("cli", "netconf")


@pytest.fixture
def closed_port():
    """A localhost port with nothing listening on it."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))

        return s.getsockname()[1]


@pytest.fixture
def silent_server():
    """A localhost server that accepts connections but never writes anything; yields its port."""
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()

    conns = []

    def accept():
        # accept until the listener is shut down at teardown
        with contextlib.suppress(OSError):
            while True:
                conns.append(listener.accept()[0])

    t = threading.Thread(target=accept, daemon=True)
    t.start()

    yield listener.getsockname()[1]

    listener.shutdown(socket.SHUT_RDWR)
    listener.close()
    t.join()

    for conn in conns:
        conn.close()


@pytest.mark.parametrize(argnames="driver", argvalues=DRIVERS, ids=DRIVER_IDS)
def test_open_connection_refused(driver, closed_port):
    with pytest.raises(SessionException):
        driver(host="127.0.0.1", port=closed_port).open()


@pytest.mark.asyncio
@pytest.mark.parametrize(argnames="driver", argvalues=DRIVERS, ids=DRIVER_IDS)
async def test_open_connection_refused_async(driver, closed_port):
    with pytest.raises(SessionException):
        await driver(host="127.0.0.1", port=closed_port).open_async()


@pytest.mark.parametrize(argnames="driver", argvalues=DRIVERS, ids=DRIVER_IDS)
def test_open_timeout(driver, silent_server):
    d = driver(
        host="127.0.0.1",
        port=silent_server,
        session_options=SessionOptions(operation_timeout_ns=1_000_000_000),
    )

    with pytest.raises(TimeoutException):
        d.open()


@pytest.mark.asyncio
@pytest.mark.parametrize(argnames="driver", argvalues=DRIVERS, ids=DRIVER_IDS)
async def test_open_timeout_async(driver, silent_server):
    d = driver(
        host="127.0.0.1",
        port=silent_server,
        session_options=SessionOptions(operation_timeout_ns=1_000_000_000),
    )

    with pytest.raises(TimeoutException):
        await d.open_async()


@pytest.mark.parametrize(argnames="driver", argvalues=DRIVERS, ids=DRIVER_IDS)
def test_open_timeout_per_call(driver, silent_server):
    with pytest.raises(TimeoutException):
        driver(host="127.0.0.1", port=silent_server).open(operation_timeout_ns=1_000_000_000)


@pytest.mark.asyncio
@pytest.mark.parametrize(argnames="driver", argvalues=DRIVERS, ids=DRIVER_IDS)
async def test_open_timeout_per_call_async(driver, silent_server):
    with pytest.raises(TimeoutException):
        await driver(host="127.0.0.1", port=silent_server).open_async(
            operation_timeout_ns=1_000_000_000
        )


@pytest.mark.parametrize(argnames="driver", argvalues=DRIVERS, ids=DRIVER_IDS)
def test_open_cancelled(driver, silent_server):
    cancel = Cancel()
    timer = threading.Timer(1, cancel.cancel)
    timer.start()

    try:
        with pytest.raises(CancelledException):
            driver(host="127.0.0.1", port=silent_server).open(cancel=cancel)
    finally:
        timer.cancel()


@pytest.mark.asyncio
@pytest.mark.parametrize(argnames="driver", argvalues=DRIVERS, ids=DRIVER_IDS)
async def test_open_cancelled_async(driver, silent_server):
    cancel = Cancel()
    handle = asyncio.get_running_loop().call_later(1, cancel.cancel)

    try:
        with pytest.raises(CancelledException):
            await driver(host="127.0.0.1", port=silent_server).open_async(cancel=cancel)
    finally:
        handle.cancel()


def _recorded_cli() -> Cli:
    return Cli(
        definition_file_or_name="arista_eos",
        host="localhost",
        auth_options=AuthOptions(
            username="admin",
            password="admin",
            lookups=[LookupKeyValue(key="enable", value="libscrapli")],
        ),
        session_options=SessionOptions(read_size=1),
        transport_options=TransportTestOptions(f=str(SILENT_AFTER_GET_PROMPT_FIXTURE)),
    )


@pytest.fixture
def unresponsive_cli():
    """An opened Cli whose device stops responding (nothing left to read) after open."""
    c = _recorded_cli()

    c.open()
    c.get_prompt()

    yield c

    c.close(force=True)


def test_send_input_timeout(unresponsive_cli):
    with pytest.raises(TimeoutException):
        unresponsive_cli.send_input(input_="show version", operation_timeout_ns=1_000_000_000)


@pytest.mark.asyncio
async def test_send_input_timeout_async(unresponsive_cli):
    with pytest.raises(TimeoutException):
        await unresponsive_cli.send_input_async(
            input_="show version", operation_timeout_ns=1_000_000_000
        )


def test_send_input_cancelled(unresponsive_cli):
    cancel = Cancel()
    timer = threading.Timer(1, cancel.cancel)
    timer.start()

    try:
        with pytest.raises(CancelledException):
            unresponsive_cli.send_input(input_="show version", cancel=cancel)
    finally:
        timer.cancel()


@pytest.mark.asyncio
async def test_send_input_cancelled_async(unresponsive_cli):
    cancel = Cancel()
    handle = asyncio.get_running_loop().call_later(1, cancel.cancel)

    try:
        with pytest.raises(CancelledException):
            await unresponsive_cli.send_input_async(input_="show version", cancel=cancel)
    finally:
        handle.cancel()


def _operation(d):
    if isinstance(d, Cli):
        return d.send_input(input_="show version")

    return d.get_config()


async def _operation_async(d):
    if isinstance(d, Cli):
        return await d.send_input_async(input_="show version")

    return await d.get_config_async()


@pytest.mark.parametrize(argnames="driver", argvalues=DRIVERS, ids=DRIVER_IDS)
def test_operation_never_opened(driver):
    with pytest.raises(NotOpenedException):
        _operation(driver(host="127.0.0.1"))


@pytest.mark.asyncio
@pytest.mark.parametrize(argnames="driver", argvalues=DRIVERS, ids=DRIVER_IDS)
async def test_operation_never_opened_async(driver):
    with pytest.raises(NotOpenedException):
        await _operation_async(driver(host="127.0.0.1"))


@pytest.mark.parametrize(argnames="driver", argvalues=DRIVERS, ids=DRIVER_IDS)
def test_operation_after_failed_open(driver, closed_port):
    d = driver(host="127.0.0.1", port=closed_port)

    with pytest.raises(SessionException):
        d.open()

    with pytest.raises(NotOpenedException):
        _operation(d)


@pytest.mark.asyncio
@pytest.mark.parametrize(argnames="driver", argvalues=DRIVERS, ids=DRIVER_IDS)
async def test_operation_after_failed_open_async(driver, closed_port):
    d = driver(host="127.0.0.1", port=closed_port)

    with pytest.raises(SessionException):
        await d.open_async()

    with pytest.raises(NotOpenedException):
        await _operation_async(d)


def test_send_input_after_close():
    c = _recorded_cli()
    c.open()
    c.close(force=True)

    with pytest.raises(NotOpenedException):
        c.send_input(input_="show version")


@pytest.mark.asyncio
async def test_send_input_after_close_async():
    c = _recorded_cli()
    await c.open_async()
    await c.close_async(force=True)

    with pytest.raises(NotOpenedException):
        await c.send_input_async(input_="show version")
