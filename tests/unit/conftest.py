from collections.abc import Callable

import pytest

from scrapli import (
    AuthOptions,
    Cli,
    LookupKeyValue,
    SessionOptions,
    TransportOptions,
    TransportTestOptions,
)
from scrapli.cli_result import Result

HOST = "localhost"


def _original_name_to_filename(originalname: str) -> str:
    return originalname.removeprefix("test_").replace("_", "-")


@pytest.fixture(scope="function")
def cli_sync(request: pytest.FixtureRequest) -> Cli:
    """Fixture to provide a sync Cli instance for unit testing"""

    f = f"{request.node.path.parent}/fixtures/{_original_name_to_filename(originalname=request.node.originalname)}"

    if id_ := request.node.callspec.id:
        f = f"{f}-{id_}"

    if request.config.getoption("--record"):
        port = 22022
        session_options = SessionOptions(
            recorder_path=f,
        )
        transport_options = TransportOptions()
    else:
        port = 22
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
def cli_assert_result(request: pytest.FixtureRequest) -> Callable[[Result], None]:
    """Fixture to update or assert golden files for unit tests"""
    f = f"{request.node.path.parent}/golden/{_original_name_to_filename(originalname=request.node.originalname)}"

    if id_ := request.node.callspec.id:
        f = f"{f}-{id_}"

    def _cli_assert_result(actual: Result) -> None:
        if request.config.getoption("--update"):
            with open(f, "w") as _f:
                _f.write(actual.result)

            return

        with open(f, "r") as _f:
            golden = _f.read()

        assert actual.result == golden

        assert actual.port == 22
        assert actual.host == HOST
        assert actual.start_time != 0
        assert actual.end_time != 0
        # TODO elapsed time, failed indicator, maybe more?
        assert actual.result_raw != b""

    return _cli_assert_result
