from collections.abc import Callable

import pytest

from scrapli import (
    AuthOptions,
    Cli,
    LookupKeyValue,
    Netconf,
    NetconfOptions,
    SessionOptions,
    TransportOptions,
    TransportTestOptions,
)
from scrapli.cli_result import Result

HOST = "localhost"
SSH_PORT_RECORD = 22022
SSH_PORT = 22
NETCONF_PORT_RECORD = 23830
NETCONF_PORT = 830


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
        transport_options = TransportOptions()
    else:
        port = SSH_PORT
        session_options = SessionOptions(read_size=1)
        transport_options = TransportOptions(test=TransportTestOptions(f=f))

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
        transport_options = TransportOptions()
    else:
        port = NETCONF_PORT
        session_options = SessionOptions(read_size=1, operation_max_search_depth=32)
        transport_options = TransportOptions(test=TransportTestOptions(f=f))

    return Netconf(
        host=HOST,
        port=port,
        options=NetconfOptions(
            close_force=True,
        ),
        auth_options=AuthOptions(
            username="root",
            password="password",
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

        assert clean_netconf_output(actual.result) == golden

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
