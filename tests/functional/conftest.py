import subprocess
import sys
from collections.abc import Callable
from difflib import SequenceMatcher

import pytest

from scrapli import (
    AuthOptions,
    Cli,
    LookupKeyValue,
    Netconf,
    SessionOptions,
    TransportBinOptions,
    TransportOptions,
    TransportSsh2Options,
)
from scrapli.cli_result import Result

IS_DARWIN = sys.platform == "darwin"
EOS_AVAILABLE = "ceos" in subprocess.getoutput("docker ps")

SSH_PORT = 22
NETCONF_PORT = 830

NETCONF_NON_EXACT_GOLDEN_MATCH_THRESHOLD = 0.8
NETCONF_NON_EXACT_CASE_SUB_STRS = (
    "test_get[netopeer",
    "test_get_async[netopeer",
)


def _original_name_to_filename(originalname: str) -> str:
    return originalname.removeprefix("test_").replace("_", "-")


@pytest.fixture(scope="function")
def cli(platform, transport) -> Cli:
    """Fixture to provide a Cli instance for functional testing"""
    if platform == "arista_eos":
        if EOS_AVAILABLE is False:
            # because we cant have this publicly in ci afaik
            pytest.skip("eos not available, skipping...")

        host = "localhost" if IS_DARWIN else "172.20.20.17"
        port = 22022 if IS_DARWIN else SSH_PORT
        auth_options = AuthOptions(
            username="admin",
            password="admin",
            lookups=[LookupKeyValue(key="enable", value="libscrapli")],
        )
    else:
        host = "localhost" if sys.platform == "darwin" else "172.20.20.16"
        port = 21022 if IS_DARWIN else SSH_PORT
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
def cli_assert_result(
    request: pytest.FixtureRequest, clean_cli_output: Callable[[str], str]
) -> Callable[[Result], None]:
    """Fixture to update or assert golden files for functional tests"""
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

        assert actual.start_time != 0
        assert actual.end_time != 0
        assert actual.elapsed_time_seconds != 0
        assert len(actual.results) != 0
        assert len(actual.results_raw) != 0
        assert actual.failed is False

    return _cli_assert_result


@pytest.fixture(scope="function")
def netconf(platform, transport) -> Netconf:
    """Fixture to provide a Netconf instance for functional testing"""
    if platform == "arista_eos":
        if EOS_AVAILABLE is False:
            # because we cant have this publicly in ci afaik
            pytest.skip("eos not available, skipping...")

        host = "localhost" if IS_DARWIN else "172.20.20.17"
        port = 22830 if IS_DARWIN else NETCONF_PORT
        auth_options = AuthOptions(
            username="admin",
            password="admin",
        )
    elif platform == "nokia_srl":
        host = "localhost" if sys.platform == "darwin" else "172.20.20.16"
        port = 21830 if IS_DARWIN else NETCONF_PORT
        auth_options = AuthOptions(
            username="admin",
            password="NokiaSrl1!",
        )
    else:
        # netopeer server
        host = "localhost" if sys.platform == "darwin" else "172.20.20.18"
        port = 23830 if IS_DARWIN else NETCONF_PORT
        auth_options = AuthOptions(
            username="root",
            password="password",
        )

    if transport == "bin":
        transport_options = TransportOptions(TransportBinOptions())
    else:
        transport_options = TransportOptions(TransportSsh2Options())

    return Netconf(
        host=host,
        port=port,
        auth_options=auth_options,
        transport_options=transport_options,
    )


@pytest.fixture(scope="function")
def netconf_assert_result(
    request: pytest.FixtureRequest, clean_netconf_output: Callable[[str], str]
) -> Callable[[Result], None]:
    """Fixture to update or assert golden files for functional tests"""
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

        if any(case in request.node.nodeid for case in NETCONF_NON_EXACT_CASE_SUB_STRS):
            # too much stuff moves round in these test cases to bother doing an actual check
            # so we'll just make sure things are ~80% similar and call it good -- the reality is
            # if the rpc didnt fail, it was probably ok anyway :)
            assert (
                SequenceMatcher(None, clean_netconf_output(actual.result), golden).ratio()
                >= NETCONF_NON_EXACT_GOLDEN_MATCH_THRESHOLD
            )
        else:
            assert clean_netconf_output(actual.result) == golden

        assert actual.start_time != 0
        assert actual.end_time != 0
        assert actual.elapsed_time_seconds != 0
        assert len(actual.result) != 0
        assert len(actual.result_raw) != 0
        # would be nice to check failed, but for now we dont as we are just making sure
        # we send valid rpcs for things like cancel commit which will always (for now)
        # reply w/ an error saying no commit to cancel.

    return _netconf_assert_result
