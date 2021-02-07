import pytest


@pytest.mark.asyncio
async def test_on_open(monkeypatch, async_junos_driver):
    _input_counter = 0

    async def _get_prompt(cls):
        return "scrapli>"

    async def _send_input(cls, channel_input, **kwargs):
        nonlocal _input_counter

        if _input_counter == 0:
            assert channel_input == "set cli complete-on-space off"
        elif _input_counter == 1:
            assert channel_input == "set cli screen-length 0"
        else:
            assert channel_input == "set cli screen-width 511"

        _input_counter += 1

        return b"", b""

    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.get_prompt", _get_prompt)
    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.send_input", _send_input)

    async_junos_driver._current_priv_level = async_junos_driver.privilege_levels["exec"]
    await async_junos_driver.on_open(async_junos_driver)


@pytest.mark.asyncio
async def test_on_close(monkeypatch, async_junos_driver):
    async def _get_prompt(cls):
        return "scrapli>"

    def _write(cls, channel_input, **kwargs):
        assert channel_input == "exit"

    def _send_return(cls):
        pass

    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.get_prompt", _get_prompt)
    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.write", _write)
    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.send_return", _send_return)

    async_junos_driver._current_priv_level = async_junos_driver.privilege_levels["exec"]
    await async_junos_driver.on_close(async_junos_driver)
