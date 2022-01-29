import pytest

from scrapli.driver.generic.base_driver import ReadCallback
from scrapli.exceptions import ScrapliValueError


def test_get_prompt(monkeypatch, sync_generic_driver):
    # stupid test w/ the patch, but want coverage and in the future maybe the driver actually
    # does something to the prompt it gets from the channel
    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.get_prompt", lambda x: "scrapli>")
    assert sync_generic_driver.get_prompt() == "scrapli>"


def test__send_command(monkeypatch, sync_generic_driver):
    monkeypatch.setattr(
        "scrapli.channel.sync_channel.Channel.send_input",
        lambda _, **kwargs: (b"raw", b"processed"),
    )
    actual_response = sync_generic_driver._send_command(command="nada")
    assert actual_response.failed is False
    assert actual_response.result == "processed"
    assert actual_response.raw_result == b"raw"


def test__send_command_no_base_transport_args(sync_generic_driver):
    sync_generic_driver._base_transport_args = None
    with pytest.raises(ScrapliValueError):
        sync_generic_driver._send_command(command="nada")


def test_send_command(monkeypatch, sync_generic_driver):
    monkeypatch.setattr(
        "scrapli.channel.sync_channel.Channel.send_input",
        lambda _, **kwargs: (b"raw", b"processed"),
    )
    actual_response = sync_generic_driver.send_command(command="nada")
    assert actual_response.failed is False
    assert actual_response.result == "processed"
    assert actual_response.raw_result == b"raw"


def test_send_commands(monkeypatch, sync_generic_driver):
    monkeypatch.setattr(
        "scrapli.channel.sync_channel.Channel.send_input",
        lambda _, **kwargs: (b"raw", b"processed"),
    )
    actual_response = sync_generic_driver.send_commands(commands=["nada", "nada2"])
    assert len(actual_response) == 2
    assert actual_response.failed is False
    assert actual_response[0].failed is False
    assert actual_response[0].result == "processed"
    assert actual_response[0].raw_result == b"raw"


def test_send_commands_from_file(fs, monkeypatch, real_ssh_commands_file_path, sync_generic_driver):
    fs.add_real_file(source_path=real_ssh_commands_file_path, target_path="/commands")
    monkeypatch.setattr(
        "scrapli.channel.sync_channel.Channel.send_input",
        lambda _, **kwargs: (b"raw", b"processed"),
    )
    actual_response = sync_generic_driver.send_commands_from_file(file="commands")
    assert actual_response.failed is False
    assert actual_response[0].result == "processed"
    assert actual_response[0].raw_result == b"raw"


def test_send_and_read(monkeypatch, sync_generic_driver):
    monkeypatch.setattr(
        "scrapli.channel.sync_channel.Channel.send_input_and_read",
        lambda _, **kwargs: (b"raw", b"processed"),
    )
    actual_response = sync_generic_driver.send_and_read(channel_input="nada")
    assert actual_response.failed is False
    assert actual_response.result == "processed"
    assert actual_response.raw_result == b"raw"


def test_send_and_read_no_base_transport_args(sync_generic_driver):
    sync_generic_driver._base_transport_args = None
    with pytest.raises(ScrapliValueError):
        sync_generic_driver.send_and_read(channel_input="nada")


def test_send_interactive(monkeypatch, sync_generic_driver):
    monkeypatch.setattr(
        "scrapli.channel.sync_channel.Channel.send_inputs_interact",
        lambda _, **kwargs: (b"raw", b"processed"),
    )
    actual_response = sync_generic_driver.send_interactive(interact_events=[("nada", "scrapli>")])
    assert actual_response.failed is False
    assert actual_response.result == "processed"
    assert actual_response.raw_result == b"raw"


def test_send_interact_no_base_transport_args(sync_generic_driver):
    sync_generic_driver._base_transport_args = None
    with pytest.raises(ScrapliValueError):
        sync_generic_driver.send_interactive(interact_events=[])


def test_readcallback_basic(monkeypatch, sync_generic_driver):
    def _read(cls):
        return b"rtr1#"

    def _write(cls, channel_input, redacted=False):
        return

    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.read", _read)
    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.write", _write)

    callback_one_counter = 0
    callback_two_counter = 0

    def callback_one(cls, read_output):
        nonlocal callback_one_counter

        callback_one_counter += 1

    def callback_two(cls, read_output):
        nonlocal callback_two_counter

        callback_two_counter += 1

    callbacks = [
        ReadCallback(
            contains="rtr1#",
            callback=callback_one,
            name="call1",
            case_insensitive=False,
            only_once=True,
        ),
        ReadCallback(
            contains_re=r"^rtr1#",
            callback=callback_two,
            complete=True,
        ),
    ]

    sync_generic_driver.read_callback(callbacks=callbacks, initial_input="nada")

    assert callback_one_counter == 1
    assert callback_two_counter == 1
