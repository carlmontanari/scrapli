from pathlib import Path

import pytest

import scrapli
from scrapli.channel import Channel
from scrapli.transport import Transport

from ...test_data.unit_test_cases import TEST_CASES

TEST_DATA_DIR = f"{Path(scrapli.__file__).parents[1]}/tests/test_data"


def test_init(sync_generic_driver_conn):
    """Test that all arguments get properly passed from driver/transport to channel on init"""
    assert isinstance(sync_generic_driver_conn.channel.transport, Transport)
    assert isinstance(sync_generic_driver_conn.channel, Channel)


@pytest.mark.parametrize(
    "strip_prompt",
    [True, False],
    ids=["strip_prompt", "no_strip_prompt"],
)
def test_send_command(sync_generic_driver_conn, strip_prompt):
    expected_raw = TEST_CASES["cisco_iosxe"]["test_send_input"]["raw_result"]
    expected_processed = (
        TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["strip"]
        if strip_prompt
        else TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["no_strip"]
    )
    sync_generic_driver_conn.open()
    sync_generic_driver_conn.send_command(command="terminal length 0")
    response = sync_generic_driver_conn.send_command(
        command="show version", strip_prompt=strip_prompt
    )
    assert response.raw_result == expected_raw.encode()
    assert response.result == expected_processed


@pytest.mark.parametrize(
    "strip_prompt",
    [True, False],
    ids=["strip_prompt", "no_strip_prompt"],
)
def test_send_commands(sync_generic_driver_conn, strip_prompt):
    expected_raw = TEST_CASES["cisco_iosxe"]["test_send_input"]["raw_result"]
    expected_processed = (
        TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["strip"]
        if strip_prompt
        else TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["no_strip"]
    )
    sync_generic_driver_conn.open()
    multi_response = sync_generic_driver_conn.send_commands(
        commands=["terminal length 0", "show version"], strip_prompt=strip_prompt
    )
    assert multi_response[1].raw_result == expected_raw.encode()
    assert multi_response[1].result == expected_processed


@pytest.mark.parametrize(
    "strip_prompt",
    [True, False],
    ids=["strip_prompt", "no_strip_prompt"],
)
def test_send_commands_from_file(sync_generic_driver_conn, strip_prompt):
    expected_raw = TEST_CASES["cisco_iosxe"]["test_send_input"]["raw_result"]
    expected_processed = (
        TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["strip"]
        if strip_prompt
        else TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["no_strip"]
    )
    sync_generic_driver_conn.open()
    sync_generic_driver_conn.send_command(command="terminal length 0")
    multi_response = sync_generic_driver_conn.send_commands_from_file(
        file=f"{TEST_DATA_DIR}/files/cisco_iosxe_commands", strip_prompt=strip_prompt
    )
    assert multi_response[0].raw_result == expected_raw.encode()
    assert multi_response[0].result == expected_processed


def test_send_interactive(sync_generic_driver_conn):
    expected_raw = TEST_CASES["cisco_iosxe"]["test_send_inputs_interact"]["raw_result"]
    expected_processed = TEST_CASES["cisco_iosxe"]["test_send_inputs_interact"]["processed_result"]
    interact_events = TEST_CASES["cisco_iosxe"]["test_send_inputs_interact"]["interact_events"]
    sync_generic_driver_conn.open()
    response = sync_generic_driver_conn.send_interactive(interact_events=interact_events)
    assert expected_raw.encode() in response.raw_result
    assert expected_processed in response.result


def test_get_prompt(sync_generic_driver_conn):
    expected_prompt = TEST_CASES["cisco_iosxe"]["test_get_prompt"]["privilege_exec"]
    sync_generic_driver_conn.open()
    found_prompt = sync_generic_driver_conn.get_prompt()
    assert found_prompt == expected_prompt
