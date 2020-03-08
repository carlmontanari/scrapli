import json
from pathlib import Path

import pytest

import scrapli

from .helper import clean_output_data

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
def test_get_prompt(cisco_iosxe_driver, transport):
    device = CISCO_IOSXE_DEVICE.copy()
    if transport == "telnet":
        device["port"] = 23
    conn = cisco_iosxe_driver(**device, transport=transport)
    result = conn.channel.get_prompt()
    assert result == "csr1000v#"
    conn.close()


@pytest.mark.parametrize(
    "test",
    [t for t in CISCO_IOSXE_TEST_CASES["send_commands"]["tests"]],
    ids=[n["name"] for n in CISCO_IOSXE_TEST_CASES["send_commands"]["tests"]],
)
@pytest.mark.parametrize(
    "transport",
    ["system", "ssh2", "paramiko", "telnet"],
    ids=["system", "ssh2", "paramiko", "telnet"],
)
def test_send_command(cisco_iosxe_driver, transport, test):
    device = CISCO_IOSXE_DEVICE.copy()
    if transport == "telnet":
        device["port"] = 23
    conn = cisco_iosxe_driver(**device, transport=transport)
    try_textfsm = test["kwargs"].pop("textfsm", None)
    result = conn.send_command(test["inputs"][0], **test["kwargs"])
    conn.close()
    cleaned_result = clean_output_data(test, result.result)
    assert cleaned_result == test["outputs"][0]
    if try_textfsm:
        structured_result = result.textfsm_parse_output()
        assert isinstance(structured_result, (list, dict))


@pytest.mark.parametrize(
    "test",
    [t for t in CISCO_IOSXE_TEST_CASES["send_commands"]["tests"]],
    ids=[n["name"] for n in CISCO_IOSXE_TEST_CASES["send_commands"]["tests"]],
)
@pytest.mark.parametrize(
    "transport",
    ["system", "ssh2", "paramiko", "telnet"],
    ids=["system", "ssh2", "paramiko", "telnet"],
)
def test_send_commands(cisco_iosxe_driver, transport, test):
    device = CISCO_IOSXE_DEVICE.copy()
    if transport == "telnet":
        device["port"] = 23
    conn = cisco_iosxe_driver(**device, transport=transport)
    try_textfsm = test["kwargs"].pop("textfsm", None)
    results = conn.send_commands(test["inputs"], **test["kwargs"])
    conn.close()
    for index, result in enumerate(results):
        cleaned_result = clean_output_data(test, result.result)
        assert cleaned_result == test["outputs"][index]
        if try_textfsm:
            structured_result = result.textfsm_parse_output()
            assert isinstance(structured_result, (list, dict))


@pytest.mark.parametrize(
    "test",
    [t for t in CISCO_IOSXE_TEST_CASES["send_configs"]["tests"]],
    ids=[n["name"] for n in CISCO_IOSXE_TEST_CASES["send_configs"]["tests"]],
)
@pytest.mark.parametrize(
    "transport",
    ["system", "ssh2", "paramiko", "telnet"],
    ids=["system", "ssh2", "paramiko", "telnet"],
)
def test_send_configs(cisco_iosxe_driver, transport, test):
    device = CISCO_IOSXE_DEVICE.copy()
    if transport == "telnet":
        device["port"] = 23
    conn = cisco_iosxe_driver(**device, transport=transport)
    conn.send_configs(test["setup"], **test["kwargs"])
    conn.channel.get_prompt()
    verification_results = conn.send_commands(test["inputs"], **test["kwargs"])
    conn.send_configs(test["teardown"], **test["kwargs"])
    conn.close()
    for index, result in enumerate(verification_results):
        cleaned_result = clean_output_data(test, result.result)
        assert cleaned_result == test["outputs"][index]
        if test.get("textfsm", None):
            assert isinstance(result.structured_result, (list, dict))


@pytest.mark.parametrize(
    "transport",
    ["system", "ssh2", "paramiko", "telnet"],
    ids=["system", "ssh2", "paramiko", "telnet"],
)
def test__acquire_priv_escalate(cisco_iosxe_driver, transport):
    device = CISCO_IOSXE_DEVICE.copy()
    if transport == "telnet":
        device["port"] = 23
    conn = cisco_iosxe_driver(**device, transport=transport)
    conn.acquire_priv("configuration")
    current_priv = conn._determine_current_priv(conn.get_prompt())
    conn.close()
    assert current_priv.name == "configuration"


@pytest.mark.parametrize(
    "transport",
    ["system", "ssh2", "paramiko", "telnet"],
    ids=["system", "ssh2", "paramiko", "telnet"],
)
def test__acquire_priv_deescalate(cisco_iosxe_driver, transport):
    device = CISCO_IOSXE_DEVICE.copy()
    if transport == "telnet":
        device["port"] = 23
    conn = cisco_iosxe_driver(**device, transport=transport)
    conn.acquire_priv("exec")
    current_priv = conn._determine_current_priv(conn.get_prompt())
    conn.close()
    assert current_priv.name == "exec"


@pytest.mark.parametrize(
    "transport",
    ["system", "ssh2", "paramiko", "telnet"],
    ids=["system", "ssh2", "paramiko", "telnet"],
)
@pytest.mark.parametrize(
    "test",
    [t for t in CISCO_IOSXE_TEST_CASES["channel.send_inputs_interact"]["tests"]],
    ids=[n["name"] for n in CISCO_IOSXE_TEST_CASES["channel.send_inputs_interact"]["tests"]],
)
def test_channel_send_inputs_interact(cisco_iosxe_driver, transport, test):
    device = CISCO_IOSXE_DEVICE.copy()
    if transport == "telnet":
        device["port"] = 23
    conn = cisco_iosxe_driver(**device, transport=transport)
    results = conn.send_interactive(test["inputs"])
    cleaned_result = clean_output_data(test, results.result)
    assert cleaned_result == test["outputs"][0]
    conn.close()
