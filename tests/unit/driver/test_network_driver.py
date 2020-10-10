from pathlib import Path

import pytest

import scrapli
from scrapli.channel import Channel
from scrapli.driver.core import IOSXEDriver
from scrapli.exceptions import ScrapliTimeout
from scrapli.transport import Transport

from ...test_data.unit_test_cases import TEST_CASES

TEST_DATA_DIR = f"{Path(scrapli.__file__).parents[1]}/tests/test_data"


def test_check_kwargs_comms_prompt_pattern():
    with pytest.warns(UserWarning) as warn:
        conn = IOSXEDriver(host="localhost", comms_prompt_pattern="something")
    assert (
        conn.comms_prompt_pattern
        == "(^[a-z0-9.\\-_@()/:]{1,63}>$)|(^[a-z0-9.\\-_@/:]{1,63}#$)|(^[a-z0-9.\\-_@/:]{1,63}\\([a-z0-9.\\-@/:\\+]{"
        "0,32}\\)#$)"
    )
    assert (
        str(warn[0].message) == "\n***** `comms_prompt_pattern` found in kwargs! "
        "*****************************************\n`comms_prompt_pattern` is ignored (dropped) when using network "
        "drivers. If you wish to modify the patterns for any network driver sub-classes, please do so by modifying "
        "or providing your own `privilege_levels`.\n***** `comms_prompt_pattern` found in kwargs! "
        "*****************************************"
    )


def test_init(sync_cisco_iosxe_conn):
    """Test that all arguments get properly passed from driver/transport to channel on init"""
    assert isinstance(sync_cisco_iosxe_conn.channel.transport, Transport)
    assert isinstance(sync_cisco_iosxe_conn.channel, Channel)
    assert sync_cisco_iosxe_conn.auth_secondary == "scrapli"
    assert list(sync_cisco_iosxe_conn.privilege_levels.keys()) == [
        "exec",
        "privilege_exec",
        "configuration",
    ]
    assert sync_cisco_iosxe_conn.default_desired_privilege_level == "privilege_exec"
    assert sync_cisco_iosxe_conn.textfsm_platform == "cisco_iosxe"
    assert sync_cisco_iosxe_conn.genie_platform == "iosxe"
    assert sync_cisco_iosxe_conn.failed_when_contains == [
        "% Ambiguous command",
        "% Incomplete command",
        "% Invalid input detected",
        "% Unknown command",
    ]


def test_escalate(sync_cisco_iosxe_conn):
    expected_prompt_privilege_exec = TEST_CASES["cisco_iosxe"]["test_get_prompt"]["privilege_exec"]
    expected_prompt_configuration = TEST_CASES["cisco_iosxe"]["test_get_prompt"]["configuration"]
    sync_cisco_iosxe_conn.open()
    assert sync_cisco_iosxe_conn._current_priv_level.name == "privilege_exec"
    assert sync_cisco_iosxe_conn.get_prompt() == expected_prompt_privilege_exec
    sync_cisco_iosxe_conn._escalate(
        escalate_priv=sync_cisco_iosxe_conn.privilege_levels["configuration"]
    )
    assert sync_cisco_iosxe_conn.get_prompt() == expected_prompt_configuration


def test_deescalate(sync_cisco_iosxe_conn):
    expected_prompt_privilege_exec = TEST_CASES["cisco_iosxe"]["test_get_prompt"]["privilege_exec"]
    expected_prompt_exec = TEST_CASES["cisco_iosxe"]["test_get_prompt"]["exec"]
    sync_cisco_iosxe_conn.open()
    assert sync_cisco_iosxe_conn._current_priv_level.name == "privilege_exec"
    assert sync_cisco_iosxe_conn.get_prompt() == expected_prompt_privilege_exec
    sync_cisco_iosxe_conn._deescalate(
        current_priv=sync_cisco_iosxe_conn.privilege_levels["privilege_exec"]
    )
    assert sync_cisco_iosxe_conn.get_prompt() == expected_prompt_exec


def test_acquire_priv(sync_cisco_iosxe_conn):
    expected_prompt_privilege_exec = TEST_CASES["cisco_iosxe"]["test_get_prompt"]["privilege_exec"]
    expected_prompt_exec = TEST_CASES["cisco_iosxe"]["test_get_prompt"]["exec"]
    expected_prompt_configuration = TEST_CASES["cisco_iosxe"]["test_get_prompt"]["configuration"]
    sync_cisco_iosxe_conn.open()
    assert sync_cisco_iosxe_conn._current_priv_level.name == "privilege_exec"
    assert sync_cisco_iosxe_conn.get_prompt() == expected_prompt_privilege_exec
    sync_cisco_iosxe_conn.acquire_priv(desired_priv="exec")
    assert sync_cisco_iosxe_conn._current_priv_level.name == "exec"
    assert sync_cisco_iosxe_conn.get_prompt() == expected_prompt_exec
    sync_cisco_iosxe_conn.acquire_priv(desired_priv="configuration")
    assert sync_cisco_iosxe_conn._current_priv_level.name == "configuration"
    assert sync_cisco_iosxe_conn.get_prompt() == expected_prompt_configuration


def test_send_command_not_desired_priv_level(sync_cisco_iosxe_conn):
    expected_prompt_privilege_exec = TEST_CASES["cisco_iosxe"]["test_get_prompt"]["privilege_exec"]
    sync_cisco_iosxe_conn.open()
    sync_cisco_iosxe_conn.send_command(command="terminal length 0")
    sync_cisco_iosxe_conn.acquire_priv(desired_priv="exec")
    sync_cisco_iosxe_conn.send_command(command="show version")
    _ = sync_cisco_iosxe_conn.send_command(command="show version")
    assert sync_cisco_iosxe_conn._current_priv_level.name == "privilege_exec"
    assert sync_cisco_iosxe_conn.get_prompt() == expected_prompt_privilege_exec


@pytest.mark.parametrize(
    "strip_prompt",
    [True, False],
    ids=["strip_prompt", "no_strip_prompt"],
)
def test_send_command(sync_cisco_iosxe_conn, strip_prompt):
    expected_raw = TEST_CASES["cisco_iosxe"]["test_send_input"]["raw_result"]
    expected_processed = (
        TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["strip"]
        if strip_prompt
        else TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["no_strip"]
    )
    sync_cisco_iosxe_conn.open()
    sync_cisco_iosxe_conn.send_command(command="terminal length 0")
    response = sync_cisco_iosxe_conn.send_command(command="show version", strip_prompt=strip_prompt)
    assert response.raw_result == expected_raw.encode()
    assert response.result == expected_processed


@pytest.mark.parametrize(
    "strip_prompt",
    [True, False],
    ids=["strip_prompt", "no_strip_prompt"],
)
def test_send_commands(sync_cisco_iosxe_conn, strip_prompt):
    expected_raw = TEST_CASES["cisco_iosxe"]["test_send_input"]["raw_result"]
    expected_processed = (
        TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["strip"]
        if strip_prompt
        else TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["no_strip"]
    )
    sync_cisco_iosxe_conn.open()
    multi_response = sync_cisco_iosxe_conn.send_commands(
        commands=["terminal length 0", "show version"], strip_prompt=strip_prompt
    )
    assert multi_response[1].raw_result == expected_raw.encode()
    assert multi_response[1].result == expected_processed


@pytest.mark.parametrize(
    "strip_prompt",
    [True, False],
    ids=["strip_prompt", "no_strip_prompt"],
)
def test_send_commands_from_file(sync_cisco_iosxe_conn, strip_prompt):
    expected_raw = TEST_CASES["cisco_iosxe"]["test_send_input"]["raw_result"]
    expected_processed = (
        TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["strip"]
        if strip_prompt
        else TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["no_strip"]
    )
    sync_cisco_iosxe_conn.open()
    sync_cisco_iosxe_conn.send_command(command="terminal length 0")
    multi_response = sync_cisco_iosxe_conn.send_commands_from_file(
        file=f"{TEST_DATA_DIR}/files/cisco_iosxe_commands", strip_prompt=strip_prompt
    )
    assert multi_response[0].raw_result == expected_raw.encode()
    assert multi_response[0].result == expected_processed


def test_send_interactive(sync_cisco_iosxe_conn):
    expected_raw = TEST_CASES["cisco_iosxe"]["test_send_inputs_interact"]["raw_result"]
    expected_processed = TEST_CASES["cisco_iosxe"]["test_send_inputs_interact"]["processed_result"]
    interact_events = TEST_CASES["cisco_iosxe"]["test_send_inputs_interact"]["interact_events"]
    sync_cisco_iosxe_conn.open()
    response = sync_cisco_iosxe_conn.send_interactive(interact_events=interact_events)
    assert expected_raw.encode() in response.raw_result
    assert expected_processed in response.result


def test_get_prompt(sync_cisco_iosxe_conn):
    expected_prompt = TEST_CASES["cisco_iosxe"]["test_get_prompt"]["privilege_exec"]
    sync_cisco_iosxe_conn.open()
    found_prompt = sync_cisco_iosxe_conn.get_prompt()
    assert found_prompt == expected_prompt


@pytest.mark.parametrize(
    "auth_secondary",
    [("scrapli", True), ("", False)],
    ids=["auth_secondary_provided", "auth_secondary_missed"],
)
def test_auth_required_no_auth_secondary(sync_cisco_iosxe_conn, auth_secondary):
    sync_cisco_iosxe_conn.auth_secondary = auth_secondary[0]
    sync_cisco_iosxe_conn.open()
    sync_cisco_iosxe_conn.acquire_priv(desired_priv="exec")

    if auth_secondary[1] is False:
        sync_cisco_iosxe_conn.channel.timeout_ops = 1
        with pytest.warns(UserWarning), pytest.raises(ScrapliTimeout):
            # makes sure we raise a user warning if auth is required for priv escalation
            # this will also fail because the mock ssh server requires a password
            sync_cisco_iosxe_conn.acquire_priv(desired_priv="privilege_exec")
    else:
        sync_cisco_iosxe_conn.acquire_priv(desired_priv="privilege_exec")
