import json
from pathlib import Path

import pytest

import scrapli

from .core.cisco_iosxe.helper import clean_output_data

TEST_DATA_PATH = f"{Path(scrapli.__file__).parents[1]}/tests/functional/test_data"
with open(f"{TEST_DATA_PATH}/devices/cisco_iosxe.json", "r") as f:
    CISCO_IOSXE_DEVICE = json.load(f)
with open(f"{TEST_DATA_PATH}/test_cases/cisco_iosxe.json", "r") as f:
    test_cases = json.load(f)
    CISCO_IOSXE_TEST_CASES = test_cases["test_cases"]

TEST_CASES = {"cisco_iosxe": CISCO_IOSXE_TEST_CASES}


@pytest.mark.parametrize(
    "transport", ["system", "ssh2", "paramiko"], ids=["system", "ssh2", "paramiko"]
)
def test_get_prompt(base_driver, transport):
    conn = base_driver(**CISCO_IOSXE_DEVICE, transport=transport)
    result = conn.channel.get_prompt()
    assert result == "csr1000v#"
    conn.close()


@pytest.mark.parametrize(
    "test",
    [t for t in CISCO_IOSXE_TEST_CASES["channel.send_inputs"]["tests"]],
    ids=[n["name"] for n in CISCO_IOSXE_TEST_CASES["channel.send_inputs"]["tests"]],
)
@pytest.mark.parametrize(
    "transport", ["system", "ssh2", "paramiko"], ids=["system", "ssh2", "paramiko"]
)
def test_channel_send_inputs(base_driver, transport, test):
    conn = base_driver(**CISCO_IOSXE_DEVICE, transport=transport)
    results = conn.channel.send_inputs(test["inputs"], **test["kwargs"])
    for index, result in enumerate(results):
        cleaned_result = clean_output_data(test, result.result)
        assert cleaned_result == test["outputs"][index]
    conn.close()


@pytest.mark.parametrize(
    "test",
    [t for t in CISCO_IOSXE_TEST_CASES["channel.send_inputs_interact"]["tests"]],
    ids=[n["name"] for n in CISCO_IOSXE_TEST_CASES["channel.send_inputs_interact"]["tests"]],
)
@pytest.mark.parametrize(
    "transport", ["system", "ssh2", "paramiko"], ids=["system", "ssh2", "paramiko"]
)
def test_channel_send_inputs_interact(base_driver, transport, test):
    conn = base_driver(**CISCO_IOSXE_DEVICE, transport=transport)
    results = conn.channel.send_inputs_interact(test["inputs"])
    cleaned_result = clean_output_data(test, results[0].result)
    assert cleaned_result == test["outputs"][0]
    conn.close()
