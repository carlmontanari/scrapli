import json
from pathlib import Path

import pytest

import scrapli
from scrapli.driver.core.cisco_iosxe.driver import PRIVS as CISCO_IOSXE_PRIVS

from .core.cisco_iosxe.helper import clean_output_data

TEST_DATA_PATH = f"{Path(scrapli.__file__).parents[1]}/tests/functional/test_data"
with open(f"{TEST_DATA_PATH}/devices/cisco_iosxe.json", "r") as f:
    CISCO_IOSXE_DEVICE = json.load(f)
with open(f"{TEST_DATA_PATH}/test_cases/cisco_iosxe.json", "r") as f:
    test_cases = json.load(f)
    CISCO_IOSXE_TEST_CASES = test_cases["test_cases"]

TEST_CASES = {"cisco_iosxe": CISCO_IOSXE_TEST_CASES}


@pytest.mark.parametrize(
    "transport",
    ["system", "ssh2", "paramiko", "telnet"],
    ids=["system", "ssh2", "paramiko", "telnet"],
)
def test_get_prompt(base_driver, transport):
    device = CISCO_IOSXE_DEVICE.copy()
    if transport == "telnet":
        device["port"] = 23
    conn = base_driver(**device, transport=transport)
    result = conn.channel.get_prompt()
    assert result == "csr1000v#"
    conn.close()


@pytest.mark.parametrize(
    "transport",
    ["system", "ssh2", "paramiko", "telnet"],
    ids=["system", "ssh2", "paramiko", "telnet"],
)
@pytest.mark.parametrize(
    "test",
    [t for t in CISCO_IOSXE_TEST_CASES["channel.send_inputs"]["tests"]],
    ids=[n["name"] for n in CISCO_IOSXE_TEST_CASES["channel.send_inputs"]["tests"]],
)
def test_channel_send_inputs(base_driver, transport, test):
    device = CISCO_IOSXE_DEVICE.copy()
    if transport == "telnet":
        device["port"] = 23
    conn = base_driver(**device, transport=transport)
    results = conn.channel.send_inputs(test["inputs"], **test["kwargs"])
    for index, result in enumerate(results):
        cleaned_result = clean_output_data(test, result.result)
        assert cleaned_result == test["outputs"][index]
    conn.close()


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
def test_channel_send_inputs_interact(base_driver, transport, test):
    device = CISCO_IOSXE_DEVICE.copy()
    if transport == "telnet":
        device["port"] = 23
    conn = base_driver(**device, transport=transport)
    results = conn.channel.send_inputs_interact(test["inputs"])
    cleaned_result = clean_output_data(test, results[0].result)
    assert cleaned_result == test["outputs"][0]
    conn.close()


@pytest.mark.parametrize(
    "transport",
    ["system", "ssh2", "paramiko", "telnet"],
    ids=["system", "ssh2", "paramiko", "telnet"],
)
@pytest.mark.parametrize(
    "test",
    [t for t in CISCO_IOSXE_TEST_CASES["send_commands"]["tests"]],
    ids=[n["name"] for n in CISCO_IOSXE_TEST_CASES["send_commands"]["tests"]],
)
def test_send_commands(network_driver, transport, test):
    device = CISCO_IOSXE_DEVICE.copy()
    if transport == "telnet":
        device["port"] = 23
    conn = network_driver(**device, transport=transport)
    conn.default_desired_priv = "privilege_exec"
    conn.privs = CISCO_IOSXE_PRIVS
    try_textfsm = test["kwargs"].pop("textfsm", None)
    results = conn.send_commands(test["inputs"], **test["kwargs"])

    for index, result in enumerate(results):
        cleaned_result = clean_output_data(test, result.result)
        assert cleaned_result == test["outputs"][index]
        if try_textfsm:
            result.textfsm_parse_output()
            assert isinstance(result.structured_result, (list, dict))
    conn.close()


@pytest.mark.parametrize(
    "transport",
    ["system", "ssh2", "paramiko", "telnet"],
    ids=["system", "ssh2", "paramiko", "telnet"],
)
@pytest.mark.parametrize(
    "test",
    [t for t in CISCO_IOSXE_TEST_CASES["send_interactive"]["tests"]],
    ids=[n["name"] for n in CISCO_IOSXE_TEST_CASES["send_interactive"]["tests"]],
)
def test_send_commands(network_driver, transport, test):
    device = CISCO_IOSXE_DEVICE.copy()
    if transport == "telnet":
        device["port"] = 23
    conn = network_driver(**device, transport=transport)
    conn.default_desired_priv = "privilege_exec"
    conn.privs = CISCO_IOSXE_PRIVS
    results = conn.send_interactive(test["inputs"], **test["kwargs"])

    for index, result in enumerate(results):
        cleaned_result = clean_output_data(test, result.result)
        assert cleaned_result == test["outputs"][index]
        if test.get("textfsm", None):
            assert isinstance(result.structured_result, (list, dict))
    conn.close()


@pytest.mark.parametrize(
    "transport",
    ["system", "ssh2", "paramiko", "telnet"],
    ids=["system", "ssh2", "paramiko", "telnet"],
)
def test__acquire_priv_escalate(network_driver, transport):
    device = CISCO_IOSXE_DEVICE.copy()
    if transport == "telnet":
        device["port"] = 23
    conn = network_driver(**device, transport=transport)
    conn.default_desired_priv = "privilege_exec"
    conn.privs = CISCO_IOSXE_PRIVS
    conn.acquire_priv("configuration")
    current_priv = conn._determine_current_priv(conn.get_prompt())
    assert current_priv.name == "configuration"
    conn.close()


@pytest.mark.parametrize(
    "transport",
    ["system", "ssh2", "paramiko", "telnet"],
    ids=["system", "ssh2", "paramiko", "telnet"],
)
def test__acquire_priv_deescalate(network_driver, transport):
    device = CISCO_IOSXE_DEVICE.copy()
    if transport == "telnet":
        device["port"] = 23
    conn = network_driver(**device, transport=transport)
    conn.default_desired_priv = "privilege_exec"
    conn.privs = CISCO_IOSXE_PRIVS
    conn.acquire_priv("exec")
    current_priv = conn._determine_current_priv(conn.get_prompt())
    assert current_priv.name == "exec"
    conn.close()
