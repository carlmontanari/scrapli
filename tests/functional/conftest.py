import sys
from collections.abc import Callable

import pytest

from scrapli import (
    AuthOptions,
    Cli,
    LookupKeyValue,
    SessionOptions,
    TransportBinOptions,
    TransportOptions,
    TransportSsh2Options,
)
from scrapli.cli_result import Result

IS_DARWIN = sys.platform == "darwin"


def _original_name_to_filename(originalname: str) -> str:
    return originalname.removeprefix("test_").replace("_", "-")


@pytest.fixture(scope="function")
def cli(platform, transport) -> Cli:
    """Fixture to provide a Cli instance for unit testing"""
    if platform == "arista_eos":
        host = "localhost" if IS_DARWIN else "172.20.20.17"
        port = 22022 if IS_DARWIN else 22
        auth_options = AuthOptions(
            username="admin",
            password="admin",
            lookups=[LookupKeyValue(key="enable", value="libscrapli")],
        )
    else:
        host = "localhost" if sys.platform == "darwin" else "172.20.20.16"
        port = 21022 if IS_DARWIN else 22
        auth_options = AuthOptions(
            username="admin",
            password="NokiaSrl1!",
        )

    if transport == "bin":
        transport_options = TransportOptions(TransportBinOptions())
    else:
        transport_options = TransportOptions(TransportSsh2Options())

    return Cli(
        definition_file_or_name=platform,
        host=host,
        port=port,
        auth_options=auth_options,
        session_options=SessionOptions(
            # because we do the info from state on srl :)
            operation_timeout_s=300,
        ),
        transport_options=transport_options,
    )


@pytest.fixture(scope="function")
def cli_assert_result(request: pytest.FixtureRequest) -> Callable[[Result], None]:
    """Fixture to update or assert golden files for unit tests"""
    filename = _original_name_to_filename(originalname=request.node.originalname)
    golden_dir = f"{request.node.path.parent}/golden/cli"
    f = f"{golden_dir}/{filename}"

    if id_ := getattr(getattr(request.node, "callspec", False), "id", False):
        f = f"{f}-{id_}"

    def _cli_assert_result(actual: Result) -> None:
        if request.config.getoption("--update"):
            with open(file=f, mode="w") as _f:
                _f.write(actual.result)

            return

        with open(file=f, mode="r", newline="") as _f:
            golden = _f.read()

        assert actual.result == golden

        assert actual.start_time != 0
        assert actual.end_time != 0
        assert actual.elapsed_time_seconds != 0
        assert len(actual.results) != 0
        assert len(actual.results_raw) != 0
        assert actual.failed is False

    return _cli_assert_result
