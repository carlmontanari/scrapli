import pytest

from scrapli.driver.core.cisco_nxos.async_driver import AsyncNXOSDriver
from scrapli.driver.core.cisco_nxos.base_driver import PRIVS


def test_base_telnet_prompt():
    async_nxos_driver = AsyncNXOSDriver(
        host="localhost",
        privilege_levels=PRIVS,
        auth_secondary="scrapli",
        default_desired_privilege_level="privilege_exec",
        transport="asynctelnet",
        port=23,
    )

    assert async_nxos_driver.transport.username_prompt == "login:"


@pytest.mark.asyncio
async def test_on_open(monkeypatch, async_nxos_driver):
    _input_counter = 0

    async def _get_prompt(cls):
        return "scrapli#"

    async def _send_input(cls, channel_input, **kwargs):
        nonlocal _input_counter

        if _input_counter == 0:
            assert channel_input == "terminal length 0"
        else:
            assert channel_input == "terminal width 511"

        _input_counter += 1

        return b"", b""

    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.get_prompt", _get_prompt)
    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.send_input", _send_input)

    async_nxos_driver._current_priv_level = async_nxos_driver.privilege_levels["privilege_exec"]
    await async_nxos_driver.on_open(async_nxos_driver)


@pytest.mark.asyncio
async def test_on_close(monkeypatch, async_nxos_driver):
    async def _get_prompt(cls):
        return "scrapli#"

    def _write(cls, channel_input, **kwargs):
        assert channel_input == "exit"

    def _send_return(cls):
        pass

    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.get_prompt", _get_prompt)
    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.write", _write)
    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.send_return", _send_return)

    async_nxos_driver._current_priv_level = async_nxos_driver.privilege_levels["privilege_exec"]
    await async_nxos_driver.on_close(async_nxos_driver)


@pytest.mark.asyncio
async def test_register_and_abort_config(monkeypatch, async_nxos_driver):
    async def _send_input(cls, channel_input, **kwargs):
        assert channel_input == "abort"

    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.send_input", _send_input)

    async_nxos_driver.register_configuration_session(session_name="scrapli")
    async_nxos_driver._current_priv_level = async_nxos_driver.privilege_levels["scrapli"]
    await async_nxos_driver._abort_config()

    assert async_nxos_driver._current_priv_level.name == "privilege_exec"
