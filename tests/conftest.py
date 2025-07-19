import re

import pytest

from scrapli.ffi_mapping import LibScrapliMapping


def pytest_addoption(parser):
    parser.addoption(
        "--record",
        action="store_true",
        default=False,
        help="record unit/integration test data from the real device",
    )

    parser.addoption(
        "--update",
        action="store_true",
        default=False,
        help="update the unit/integration test golden files",
    )

    parser.addoption(
        "--skip-slow",
        action="store_true",
        default=False,
        help="skip slow tests -- like really huge outputs",
    )


@pytest.fixture(scope="session", autouse=True)
def assert_no_leaks():
    # only works (well... it wont fail, but only will report accurately) when used w/ *non-release*
    # build *or* when `LIBSCRAPLI_DEBUG` env var is set to any value (just has to be present) as
    # this will cuase us to use the debug allocator rather than c allocator.
    yield

    assert LibScrapliMapping().shared_mapping.assert_no_leaks() is True


CLI_USER_AT_HOST_PATTERN = re.compile(r"\b\w+@\w+\b")
CLI_TIMESTAMP_PATTERN = re.compile(
    r"(?im)((mon)|(tue)|(wed)|(thu)|(fri)|(sat)|(sun))\s+"
    r"((jan)|(feb)|(mar)|(apr)|(may)|(jun)|(jul)|(aug)|(sep)|(oct)|(nov)|(dec))\s+"
    r"\d+\s+\d+:\d+:\d+\s\d+"
)
CLI_PASSWORD_PATTERN = re.compile(r"(?im)^\s+password .*$", re.MULTILINE)


@pytest.fixture(scope="function")
def clean_cli_output() -> str:
    def _clean_cli_output(output: str) -> str:
        output = CLI_USER_AT_HOST_PATTERN.sub("user@host", output)
        output = CLI_TIMESTAMP_PATTERN.sub("Mon Jan 1 00:00:00 2025", output)
        output = CLI_PASSWORD_PATTERN.sub("__PASSWORD__", output)

        return output

    return _clean_cli_output


NETCONF_TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}T\d+:\d+:\d+\.\d+(?:([\d:+]+)|Z)")
NETCONF_SESSION_ID_PATTERN = re.compile(r"<session-id>\d+</session-id>")
NETCONF_PASSWORD_PATTERN = re.compile(r"<password>.*?</password>")
NETCONF_KEY_PATTERN = re.compile(r"<cleartext-private-key>.*?</cleartext-private-key>")
NETCONF_DUMMY_COUNTER_PATTERN = re.compile(r"<counter>\d+</counter>")
NETCONF_STATISTICS_ELEMENT_PATTERN = re.compile(r"<statistics>.*?</statistics>")


@pytest.fixture(scope="function")
def clean_netconf_output() -> str:
    def _clean_netconf_output(output: str) -> str:
        output = NETCONF_TIMESTAMP_PATTERN.sub("__TIMESTAMP__", output)
        output = NETCONF_SESSION_ID_PATTERN.sub("__SESSIONID__", output)
        output = NETCONF_PASSWORD_PATTERN.sub("__PASSWORD__", output)
        output = NETCONF_KEY_PATTERN.sub("__KEY__", output)
        output = NETCONF_DUMMY_COUNTER_PATTERN.sub("__COUNTER__", output)
        output = NETCONF_STATISTICS_ELEMENT_PATTERN.sub("__STATISTICS__", output)

        return output

    return _clean_netconf_output
