import pytest

from scrapli.exceptions import ScrapliValueError


@pytest.mark.asyncio
async def test_get_prompt(monkeypatch, async_generic_driver):
    async def _get_prompt(cls):
        return "scrapli>"

    # stupid test w/ the patch, but want coverage and in the future maybe the driver actually
    # does something to the prompt it gets from the channel
    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.get_prompt", _get_prompt)
    assert await async_generic_driver.get_prompt() == "scrapli>"


@pytest.mark.asyncio
async def test__send_command(monkeypatch, async_generic_driver):
    async def _send_input(cls, **kwargs):
        return b"raw", b"processed"

    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.send_input", _send_input)
    actual_response = await async_generic_driver._send_command(command="nada")
    assert actual_response.failed is False
    assert actual_response.result == "processed"
    assert actual_response.raw_result == b"raw"


@pytest.mark.asyncio
async def test__send_command_no_base_transport_args(async_generic_driver):
    async_generic_driver._base_transport_args = None
    with pytest.raises(ScrapliValueError):
        await async_generic_driver._send_command(command="nada")


@pytest.mark.asyncio
async def test_send_command(monkeypatch, async_generic_driver):
    async def _send_input(cls, **kwargs):
        return b"raw", b"processed"

    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.send_input", _send_input)
    actual_response = await async_generic_driver.send_command(command="nada")
    assert actual_response.failed is False
    assert actual_response.result == "processed"
    assert actual_response.raw_result == b"raw"


@pytest.mark.asyncio
async def test_send_commands(monkeypatch, async_generic_driver):
    async def _send_input(cls, **kwargs):
        return b"raw", b"processed"

    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.send_input", _send_input)
    actual_response = await async_generic_driver.send_commands(commands=["nada", "nada2"])
    assert len(actual_response) == 2
    assert actual_response.failed is False
    assert actual_response[0].failed is False
    assert actual_response[0].result == "processed"
    assert actual_response[0].raw_result == b"raw"


@pytest.mark.asyncio
async def test_send_commands_from_file(
    fs, monkeypatch, real_ssh_commands_file_path, async_generic_driver
):
    fs.add_real_file(source_path=real_ssh_commands_file_path, target_path="/commands")

    async def _send_input(cls, **kwargs):
        return b"raw", b"processed"

    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.send_input", _send_input)
    actual_response = await async_generic_driver.send_commands_from_file(file="commands")
    assert actual_response.failed is False
    assert actual_response[0].result == "processed"
    assert actual_response[0].raw_result == b"raw"


@pytest.mark.asyncio
async def test_send_and_read(monkeypatch, async_generic_driver):
    async def _send_input_and_read(cls, **kwargs):
        return b"raw", b"processed"

    monkeypatch.setattr(
        "scrapli.channel.async_channel.AsyncChannel.send_input_and_read", _send_input_and_read
    )
    actual_response = await async_generic_driver.send_and_read(channel_input="nada")
    assert actual_response.failed is False
    assert actual_response.result == "processed"
    assert actual_response.raw_result == b"raw"


@pytest.mark.asyncio
async def test_send_and_read_no_base_transport_args(async_generic_driver):
    async_generic_driver._base_transport_args = None
    with pytest.raises(ScrapliValueError):
        await async_generic_driver.send_and_read(channel_input="nada")


@pytest.mark.asyncio
async def test_send_interactive(monkeypatch, async_generic_driver):
    async def _send_inputs_interact(cls, **kwargs):
        return b"raw", b"processed"

    monkeypatch.setattr(
        "scrapli.channel.async_channel.AsyncChannel.send_inputs_interact", _send_inputs_interact
    )

    actual_response = await async_generic_driver.send_interactive(
        interact_events=[("nada", "scrapli>")]
    )
    assert actual_response.failed is False
    assert actual_response.result == "processed"
    assert actual_response.raw_result == b"raw"


@pytest.mark.asyncio
async def test_send_interact_no_base_transport_args(async_generic_driver):
    async_generic_driver._base_transport_args = None
    with pytest.raises(ScrapliValueError):
        await async_generic_driver.send_interactive(interact_events=[])
