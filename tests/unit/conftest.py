import contextlib
import os
import shutil
import signal
import socket
import subprocess
import tempfile
import time
from collections.abc import Callable, Generator
from pathlib import Path
from typing import IO

import pytest

from scrapli import (
    AuthOptions,
    Cli,
    LookupKeyValue,
    Netconf,
    SessionOptions,
    TransportBinOptions,
    TransportSsh2Options,
    TransportTestOptions,
)
from scrapli.cli_result import Result

HOST = "localhost"
SSH_PORT_RECORD = 22022
SSH_PORT = 22
NETCONF_PORT_RECORD = 23830
NETCONF_PORT = 830
DUMMY_SSH_SERVER_HOST = "localhost"
DUMMY_SSH_SERVER_PORT = 2222


def _original_name_to_filename(originalname: str) -> str:
    return originalname.removeprefix("test_").replace("_", "-")


@pytest.fixture(scope="function")
def cli(request: pytest.FixtureRequest) -> Cli:
    """Fixture to provide a Cli instance for unit testing"""
    filename = _original_name_to_filename(originalname=request.node.originalname)
    fixture_dir = f"{request.node.path.parent}/fixtures/cli"
    f = f"{fixture_dir}/{filename}"

    if id_ := getattr(getattr(request.node, "callspec", False), "id", False):
        f = f"{f}-{id_}"

    if request.config.getoption("--record"):
        port = SSH_PORT_RECORD
        session_options = SessionOptions(
            recorder_path=f,
        )
        transport_options = TransportBinOptions()
    else:
        port = SSH_PORT
        session_options = SessionOptions(read_size=1)
        transport_options = TransportTestOptions(f=f)

    return Cli(
        definition_file_or_name="arista_eos",
        host=HOST,
        port=port,
        auth_options=AuthOptions(
            username="admin",
            password="admin",
            lookups=[LookupKeyValue(key="enable", value="libscrapli")],
        ),
        session_options=session_options,
        transport_options=transport_options,
    )


@pytest.fixture(scope="function")
def cli_assert_result(
    request: pytest.FixtureRequest, clean_cli_output: Callable[[str], str]
) -> Callable[[Result], None]:
    """Fixture to update or assert golden files for unit tests"""
    filename = _original_name_to_filename(originalname=request.node.originalname)
    golden_dir = f"{request.node.path.parent}/golden/cli"
    f = f"{golden_dir}/{filename}"

    if id_ := getattr(getattr(request.node, "callspec", False), "id", False):
        f = f"{f}-{id_}"

    def _cli_assert_result(actual: Result) -> None:
        if request.config.getoption("--update"):
            with open(file=f, mode="w") as _f:
                _f.write(clean_cli_output(actual.result))

            return

        with open(file=f, mode="r", newline="") as _f:
            golden = _f.read()

        assert clean_cli_output(actual.result) == golden

        assert actual.port == SSH_PORT
        assert actual.host == HOST
        assert actual.start_time != 0
        assert actual.end_time != 0
        assert actual.elapsed_time_seconds != 0
        assert len(actual.results) != 0
        assert len(actual.results_raw) != 0
        assert actual.failed is False

    return _cli_assert_result


@pytest.fixture(scope="function")
def netconf(request: pytest.FixtureRequest) -> Netconf:
    """Fixture to provide a Netconf instance for unit testing"""
    filename = _original_name_to_filename(originalname=request.node.originalname)
    fixture_dir = f"{request.node.path.parent}/fixtures/netconf"
    f = f"{fixture_dir}/{filename}"

    if id_ := getattr(getattr(request.node, "callspec", False), "id", False):
        f = f"{f}-{id_}"

    if request.config.getoption("--record"):
        port = NETCONF_PORT_RECORD
        session_options = SessionOptions(
            recorder_path=f,
        )
        transport_options = TransportBinOptions()
    else:
        port = NETCONF_PORT
        session_options = SessionOptions(
            read_size=1,
            operation_max_search_depth=32,
            # because gh runners are horrendously slow and we read 1 byte at a time
            operation_timeout_s=30,
        )
        transport_options = TransportTestOptions(f=f)

    return Netconf(
        host=HOST,
        port=port,
        auth_options=AuthOptions(
            username="root",
            password="password",
        ),
        session_options=session_options,
        transport_options=transport_options,
    )


@pytest.fixture(scope="function")
def netconf_srl(request: pytest.FixtureRequest) -> Netconf:
    """Fixture to provide a Netconf instance (srl not netopeer) for unit testing"""
    filename = _original_name_to_filename(originalname=request.node.originalname)
    fixture_dir = f"{request.node.path.parent}/fixtures/netconf"
    f = f"{fixture_dir}/{filename}"

    if id_ := getattr(getattr(request.node, "callspec", False), "id", False):
        f = f"{f}-{id_}"

    if request.config.getoption("--record"):
        port = 21830
        session_options = SessionOptions(
            recorder_path=f,
        )
        transport_options = TransportBinOptions()
    else:
        port = NETCONF_PORT
        session_options = SessionOptions(read_size=1, operation_max_search_depth=32)
        transport_options = TransportTestOptions(f=f)

    return Netconf(
        host=HOST,
        port=port,
        auth_options=AuthOptions(
            username="admin",
            password="NokiaSrl1!",
        ),
        session_options=session_options,
        transport_options=transport_options,
    )


@pytest.fixture(scope="function")
def netconf_assert_result(
    request: pytest.FixtureRequest, clean_netconf_output: Callable[[str], str]
) -> Callable[[Result], None]:
    """Fixture to update or assert golden files for unit tests"""
    filename = _original_name_to_filename(originalname=request.node.originalname)
    golden_dir = f"{request.node.path.parent}/golden/netconf"
    f = f"{golden_dir}/{filename}"

    if id_ := getattr(getattr(request.node, "callspec", False), "id", False):
        f = f"{f}-{id_}"

    def _netconf_assert_result(actual: Result) -> None:
        if request.config.getoption("--update"):
            with open(file=f, mode="w") as _f:
                _f.write(clean_netconf_output(actual.result))

            return

        with open(file=f, mode="r", newline="") as _f:
            golden = _f.read()

        assert clean_netconf_output(actual.result) == clean_netconf_output(golden)

        assert actual.port == NETCONF_PORT
        assert actual.host == HOST
        assert actual.start_time != 0
        assert actual.end_time != 0
        assert actual.elapsed_time_seconds != 0
        assert len(actual.result) != 0
        assert len(actual.result_raw) != 0
        # would be nice to check failed, but for now we dont as we are just making sure
        # we send valid rpcs for things like cancel commit which will always (for now)
        # reply w/ an error saying no commit to cancel.

    return _netconf_assert_result


@pytest.fixture(scope="function")
def options_assert_result(request: pytest.FixtureRequest) -> Callable[[Result], None]:
    def _options_assert_result(actual: str, f: str):
        if request.config.getoption("--update"):
            with open(file=f, mode="w") as _f:
                _f.write(actual)

            return

        with open(file=f, mode="r", newline="") as _f:
            golden = _f.read()

        assert actual == golden.strip()

    return _options_assert_result


def _wait_for_dummy_ssh_server(proc: subprocess.Popen[bytes], output_f: IO[bytes]) -> None:
    # lil time to fetch deps etc.
    deadline = time.monotonic() + 120

    while time.monotonic() < deadline:
        if proc.poll() is not None:
            output_f.seek(0)
            output = output_f.read().decode(errors="replace")

            raise RuntimeError(
                f"dummy ssh server exited early w/ return code {proc.returncode}, "
                f"output:\n{output}"
            )

        try:
            with socket.create_connection(
                (DUMMY_SSH_SERVER_HOST, DUMMY_SSH_SERVER_PORT), timeout=1
            ):
                return
        except OSError:
            time.sleep(0.25)

    raise TimeoutError("timed out waiting for dummy ssh server to accept connections")


@pytest.fixture(scope="module")
def dummy_ssh_server() -> Generator[None, None, None]:
    command = ["go", "run", "."]

    if command[0] == "go" and shutil.which("go") is None:
        pytest.skip("go toolchain not available, skipping...")

    output_f = tempfile.TemporaryFile()

    proc = subprocess.Popen(
        command,
        cwd=Path(__file__).parent / "dummy_ssh_server",
        stdout=output_f,
        stderr=subprocess.STDOUT,
        # new session/process group so we can reliably kill the server `go run` spawns, not
        # just `go run` itself
        start_new_session=True,
    )

    try:
        _wait_for_dummy_ssh_server(proc=proc, output_f=output_f)

        yield
    finally:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)

        proc.wait()
        output_f.close()


@pytest.fixture(scope="function")
def concurrency_cli(transport) -> Callable[[], Cli]:
    """Fixture providing a factory building Cli instances pointed at the dummy ssh server"""

    def _concurrency_cli() -> Cli:
        # note that every call builds fresh transport options -- options objects hold
        # per-connection c-string state once applied, so they must not be shared across
        # concurrent connections
        if transport == "bin":
            transport_options: TransportBinOptions | TransportSsh2Options = TransportBinOptions(
                extra_open_args=["-F", "/dev/null"],
            )
        else:
            transport_options = TransportSsh2Options()

        return Cli(
            DUMMY_SSH_SERVER_HOST,
            port=DUMMY_SSH_SERVER_PORT,
            auth_options=AuthOptions(
                username="admin",
                password="password",
            ),
            transport_options=transport_options,
        )

    return _concurrency_cli
