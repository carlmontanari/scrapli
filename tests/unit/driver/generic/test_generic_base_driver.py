import re

import pytest

from scrapli.driver.generic.base_driver import ReadCallback
from scrapli.exceptions import ScrapliTypeError
from scrapli.response import MultiResponse, Response


def test_readcallback_contains_bytes_property():
    read_callback = ReadCallback(callback=lambda _: None, name="testing", contains="contains")

    assert read_callback.name == "testing"
    assert read_callback.contains_bytes == b"contains"


def test_readcallback_not_contains_bytes_property():
    read_callback = ReadCallback(callback=lambda _: None, name="testing", not_contains="contains")

    assert read_callback.name == "testing"
    assert read_callback.not_contains_bytes == b"contains"


def test_readcallback_contains_re_bytes_property():
    read_callback = ReadCallback(callback=lambda x: x + 1, name="testing", contains_re="contains")

    assert read_callback.name == "testing"
    assert read_callback.contains_re_bytes == re.compile(b"contains", re.IGNORECASE | re.MULTILINE)


def test_readcallback_contains_re_bytes_property_sensitive():
    read_callback = ReadCallback(
        callback=lambda _: None, name="testing", contains_re="contains", case_insensitive=False
    )

    assert read_callback.name == "testing"
    assert read_callback.contains_re_bytes == re.compile(b"contains", re.MULTILINE)


def test_readcallback_contains_re_bytes_property_nomultiline():
    read_callback = ReadCallback(
        callback=lambda _: None, name="testing", contains_re="contains", multiline=False
    )

    assert read_callback.name == "testing"
    assert read_callback.contains_re_bytes == re.compile(b"contains", re.IGNORECASE)


def test_readcallback_check_contains():
    read_callback = ReadCallback(
        callback=lambda _: None, name="testing", contains="contains", case_insensitive=False
    )

    assert read_callback.name == "testing"
    assert read_callback.check(b"this contains some stuff") is True


def test_readcallback_check_re_contains():
    read_callback = ReadCallback(callback=lambda _: None, name="testing", contains_re="contains")

    assert read_callback.name == "testing"
    assert read_callback.check(b"this contains some stuff") is True


def test_readcallback_check_fail():
    read_callback = ReadCallback(callback=lambda _: None, name="testing", contains_re="contains")

    assert read_callback.name == "testing"
    assert read_callback.check(b"nope, not here") is False


def test_readcallback_run_sync():
    callback_executed = False

    def callback(driver, read_output):
        nonlocal callback_executed
        callback_executed = True

    read_callback = ReadCallback(
        callback=callback,
        name="testing",
        contains_re="contains",
        case_insensitive=False,
        only_once=True,
    )

    assert read_callback.name == "testing"

    assert read_callback._triggered is False
    read_callback.run(None)

    assert callback_executed is True
    assert read_callback._triggered is True


async def test_readcallback_run_async():
    callback_executed = False

    async def callback(driver, read_output):
        nonlocal callback_executed
        callback_executed = True

    read_callback = ReadCallback(callback=callback, contains_re="contains", only_once=True)

    assert read_callback.name == "callback"

    assert read_callback._triggered is False
    await read_callback.run(None)

    assert callback_executed is True
    assert read_callback._triggered is True


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
