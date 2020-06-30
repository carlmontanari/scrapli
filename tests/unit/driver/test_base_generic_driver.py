from pathlib import Path

import pytest

import scrapli
from scrapli.response import MultiResponse, Response

TEST_DATA_DIR = f"{Path(scrapli.__file__).parents[1]}/tests/test_data/"


def test_pre_send_command_exception(sync_cisco_iosxe_conn):
    with pytest.raises(TypeError) as exc:
        sync_cisco_iosxe_conn._pre_send_command(
            host=sync_cisco_iosxe_conn.transport.host, command=[]
        )
    assert (
        str(exc.value)
        == "`send_command` expects a single string, got <class 'list'>, to send a list of commands use the `send_commands` method instead."
    )


def test_pre_send_command(sync_cisco_iosxe_conn):
    response = sync_cisco_iosxe_conn._pre_send_command(
        host=sync_cisco_iosxe_conn.transport.host,
        command="show version",
        failed_when_contains=["something"],
    )
    assert isinstance(response, Response)
    assert response.host == sync_cisco_iosxe_conn.transport.host
    assert response.failed_when_contains == ["something"]
    assert response.channel_input == "show version"


def test_post_send_command(sync_cisco_iosxe_conn):
    response = sync_cisco_iosxe_conn._pre_send_command(
        host=sync_cisco_iosxe_conn.transport.host,
        command="show version",
        failed_when_contains=["something"],
    )
    final_response = sync_cisco_iosxe_conn._post_send_command(
        raw_response=b"blah", processed_response=b"blahx2", response=response
    )
    # generic driver doesnt know/care about textfsm_platform
    assert final_response.textfsm_platform == ""
    assert final_response.start_time == response.start_time
    assert final_response.elapsed_time > 0


def test_pre_send_commands_exception(sync_cisco_iosxe_conn):
    with pytest.raises(TypeError) as exc:
        sync_cisco_iosxe_conn._pre_send_commands(commands="boo")
    assert (
        str(exc.value)
        == "`send_commands` expects a list of strings, got <class 'str'>, to send a single command use the `send_command` method instead."
    )


def test_pre_send_commands(sync_cisco_iosxe_conn):
    responses = sync_cisco_iosxe_conn._pre_send_commands(commands=["show version"])
    assert isinstance(responses, MultiResponse)
    assert responses.failed is False


def test_pre_send_commands_from_file_exception(sync_cisco_iosxe_conn):
    with pytest.raises(TypeError) as exc:
        sync_cisco_iosxe_conn._pre_send_commands_from_file(file=[])
    assert (
        str(exc.value)
        == "`send_commands_from_file` expects a string path to a file, got <class 'list'>"
    )


def test_pre_send_commands_from_file(sync_cisco_iosxe_conn):
    commands = sync_cisco_iosxe_conn._pre_send_commands_from_file(
        file=f"{TEST_DATA_DIR}/files/vrnetlab_key"
    )
    assert commands[0] == "-----BEGIN OPENSSH PRIVATE KEY-----"
    assert commands[-1] == "-----END OPENSSH PRIVATE KEY-----"


def test_pre_send_commands_interactive(sync_cisco_iosxe_conn):
    response = sync_cisco_iosxe_conn._pre_send_interactive(
        host=sync_cisco_iosxe_conn.transport.host,
        interact_events=[("input1", "expected1"), ("input2", "expected2")],
    )
    assert isinstance(response, Response)
    assert response.host == sync_cisco_iosxe_conn.transport.host
    assert response.failed_when_contains is None
    assert response.channel_input == "input1, input2"
