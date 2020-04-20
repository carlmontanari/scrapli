"""examples.test_examples"""
import pytest

from .basic_usage import generic_driver, iosxe_driver, scrapli_driver
from .logging import basic_logging
from .ssh_keys import ssh_keys
from .structured_data import structured_data_genie

# simply making sure the examples don't blow up!


@pytest.mark.parametrize(
    "example_script",
    [generic_driver, iosxe_driver, scrapli_driver],
    ids=["generic_driver", "iosxe_driver", "scrapli_driver"],
)
def test_basic_usage(example_script):
    example_script.main()


def test_logging():
    basic_logging.main()


def test_ssh_keys():
    ssh_keys.main()


@pytest.mark.parametrize(
    "example_script", [structured_data_genie, structured_data_genie], ids=["genie", "textfsm"],
)
def test_structured_data(example_script):
    example_script.main()
