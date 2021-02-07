import pytest

from scrapli.exceptions import ScrapliTypeError
from scrapli.response import MultiResponse, Response


def test_pre_send_command(base_generic_driver):
    actual_response = base_generic_driver._pre_send_command(
        host="localhost", command="show version"
    )
    assert isinstance(actual_response, Response)
    assert actual_response.host == "localhost"


def test_pre_send_command_exception(base_generic_driver):
    with pytest.raises(ScrapliTypeError):
        base_generic_driver._pre_send_command(host="localhost", command=None)


def test_post_send_command(base_generic_driver):
    actual_response = base_generic_driver._pre_send_command(
        host="localhost", command="show version"
    )
    assert isinstance(actual_response, Response)
    assert actual_response.host == "localhost"

    updated_actual_response = base_generic_driver._post_send_command(
        raw_response=b"raw", processed_response=b"processed", response=actual_response
    )
    assert updated_actual_response.result == "processed"
    assert updated_actual_response.raw_result == b"raw"


def test_pre_send_commands_exception(base_generic_driver):
    with pytest.raises(ScrapliTypeError):
        base_generic_driver._pre_send_commands(commands="something")


def test_pre_send_commands(base_generic_driver):
    actual_responses = base_generic_driver._pre_send_commands(commands=[])
    assert isinstance(actual_responses, MultiResponse)


def test_pre_send_from_file(fs, real_ssh_config_file_path, base_generic_driver):
    fs.add_real_file(source_path=real_ssh_config_file_path, target_path="/scrapli/mycommands")
    commands = base_generic_driver._pre_send_from_file(
        file="/scrapli/mycommands", caller="commands"
    )
    assert isinstance(commands, list)
    assert isinstance(commands[0], str)


def test_pre_send_from_file_exception(base_generic_driver):
    with pytest.raises(ScrapliTypeError):
        base_generic_driver._pre_send_from_file(file=None, caller="commands")


def test_pre_send_interactive(base_generic_driver):
    actual_response = base_generic_driver._pre_send_interactive(
        host="localhost", interact_events=[("input1", "expected1"), ("input2", "expected2")]
    )
    assert isinstance(actual_response, Response)
    assert actual_response.host == "localhost"
    assert actual_response.channel_input == "input1, input2"
