import json
from pathlib import Path

import pytest

import nssh
from nssh.driver.core.cisco_iosxe.driver import PRIVS as CISCO_IOSXE_PRIVS

from .core.cisco_iosxe.helper import clean_output_data

TEST_DATA_PATH = f"{Path(nssh.__file__).parents[1]}/tests/functional/test_data"
with open(f"{TEST_DATA_PATH}/devices/cisco_iosxe.json", "r") as f:
    CISCO_IOSXE_DEVICE = json.load(f)
with open(f"{TEST_DATA_PATH}/test_cases/cisco_iosxe.json", "r") as f:
    test_cases = json.load(f)
    CISCO_IOSXE_TEST_CASES = test_cases["test_cases"]

TEST_CASES = {"cisco_iosxe": CISCO_IOSXE_TEST_CASES}


@pytest.mark.parametrize(
    "driver", ["system", "ssh2", "paramiko"], ids=["system", "ssh2", "paramiko"]
)
def test_get_prompt(base_driver, driver):
    conn = base_driver(**CISCO_IOSXE_DEVICE, driver=driver)
    result = conn.channel.get_prompt()
    assert result == "csr1000v#"
    conn.close()


@pytest.mark.parametrize(
    "test",
    [t for t in CISCO_IOSXE_TEST_CASES["channel.send_inputs"]["tests"]],
    ids=[n["name"] for n in CISCO_IOSXE_TEST_CASES["channel.send_inputs"]["tests"]],
)
@pytest.mark.parametrize(
    "driver", ["system", "ssh2", "paramiko"], ids=["system", "ssh2", "paramiko"]
)
def test_channel_send_inputs(base_driver, driver, test):
    conn = base_driver(**CISCO_IOSXE_DEVICE, driver=driver)
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
    "driver", ["system", "ssh2", "paramiko"], ids=["system", "ssh2", "paramiko"]
)
def test_channel_send_inputs_interact(base_driver, driver, test):
    conn = base_driver(**CISCO_IOSXE_DEVICE, driver=driver)
    results = conn.channel.send_inputs_interact(test["inputs"])
    cleaned_result = clean_output_data(test, results[0].result)
    assert cleaned_result == test["outputs"][0]
    conn.close()


@pytest.mark.parametrize(
    "test",
    [t for t in CISCO_IOSXE_TEST_CASES["send_commands"]["tests"]],
    ids=[n["name"] for n in CISCO_IOSXE_TEST_CASES["send_commands"]["tests"]],
)
@pytest.mark.parametrize(
    "driver", ["system", "ssh2", "paramiko"], ids=["system", "ssh2", "paramiko"]
)
def test_send_commands(network_driver, driver, test):
    conn = network_driver(**CISCO_IOSXE_DEVICE, driver=driver)
    conn.default_desired_priv = "privilege_exec"
    conn.privs = CISCO_IOSXE_PRIVS
    results = conn.send_commands(test["inputs"], **test["kwargs"])

    for index, result in enumerate(results):
        cleaned_result = clean_output_data(test, result.result)
        assert cleaned_result == test["outputs"][index]
        if test.get("textfsm", None):
            assert isinstance(result.structured_result, (list, dict))
    conn.close()


@pytest.mark.parametrize(
    "test",
    [t for t in CISCO_IOSXE_TEST_CASES["send_interactive"]["tests"]],
    ids=[n["name"] for n in CISCO_IOSXE_TEST_CASES["send_interactive"]["tests"]],
)
@pytest.mark.parametrize(
    "driver", ["system", "ssh2", "paramiko"], ids=["system", "ssh2", "paramiko"]
)
def test_send_commands(network_driver, driver, test):
    conn = network_driver(**CISCO_IOSXE_DEVICE, driver=driver)
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
    "driver", ["system", "ssh2", "paramiko"], ids=["system", "ssh2", "paramiko"]
)
def test__acquire_priv_escalate(network_driver, driver):
    conn = network_driver(**CISCO_IOSXE_DEVICE, driver=driver)
    conn.default_desired_priv = "privilege_exec"
    conn.privs = CISCO_IOSXE_PRIVS
    conn.acquire_priv("configuration")
    current_priv = conn._determine_current_priv(conn.get_prompt())
    assert current_priv.name == "configuration"
    conn.close()


@pytest.mark.parametrize(
    "driver", ["system", "ssh2", "paramiko"], ids=["system", "ssh2", "paramiko"]
)
def test__acquire_priv_deescalate(network_driver, driver):
    conn = network_driver(**CISCO_IOSXE_DEVICE, driver=driver)
    conn.default_desired_priv = "privilege_exec"
    conn.privs = CISCO_IOSXE_PRIVS
    conn.acquire_priv("exec")
    current_priv = conn._determine_current_priv(conn.get_prompt())
    assert current_priv.name == "exec"
    conn.close()
