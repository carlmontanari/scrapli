import pytest

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
