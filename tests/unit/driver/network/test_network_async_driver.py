import pytest

from scrapli.exceptions import ScrapliPrivilegeError


async def test_escalate(monkeypatch, async_network_driver):
    async def _send_input(cls, channel_input, **kwargs):
        assert channel_input == "configure terminal"
        return b"raw", b"processed"

    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.send_input", _send_input)

    async_network_driver._current_priv_level = async_network_driver.privilege_levels[
        "privilege_exec"
    ]
    await async_network_driver._escalate(
        escalate_priv=async_network_driver.privilege_levels["configuration"]
    )


async def test_escalate_auth_secondary(monkeypatch, async_network_driver):
    async def _send_inputs_interact(cls, interact_events, **kwargs):
        assert interact_events[0][0] == "enable"
        return b"raw", b"processed"

    monkeypatch.setattr(
        "scrapli.channel.async_channel.AsyncChannel.send_inputs_interact", _send_inputs_interact
    )

    # patching send inputs interactive means if this passes we know we had to do an "authy" escalation
    async_network_driver._current_priv_level = async_network_driver.privilege_levels["exec"]
    await async_network_driver._escalate(
        escalate_priv=async_network_driver.privilege_levels["privilege_exec"]
    )


async def test_deescalate(monkeypatch, async_network_driver):
    async def _send_input(cls, channel_input, **kwargs):
        assert channel_input == "disable"
        return b"raw", b"processed"

    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.send_input", _send_input)

    async_network_driver._current_priv_level = "privilege_exec"
    await async_network_driver._deescalate(
        current_priv=async_network_driver.privilege_levels["privilege_exec"]
    )


async def test_acquire_priv_no_action(monkeypatch, async_network_driver):
    async def _get_prompt(cls):
        return "scrapli#"

    monkeypatch.setattr(
        "scrapli.channel.async_channel.AsyncChannel.get_prompt",
        _get_prompt,
    )

    async_network_driver._current_priv_level = async_network_driver.privilege_levels[
        "privilege_exec"
    ]
    await async_network_driver.acquire_priv(desired_priv="privilege_exec")


async def test_acquire_priv_escalate(monkeypatch, async_network_driver):
    _prompt_counter = 0

    async def _get_prompt(cls):
        nonlocal _prompt_counter
        if _prompt_counter == 0:
            prompt = "scrapli#"
        else:
            prompt = "scrapli(config)#"
        _prompt_counter += 1
        return prompt

    async def _send_input(cls, channel_input, **kwargs):
        assert channel_input == "configure terminal"
        return b"raw", b"processed"

    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.get_prompt", _get_prompt)
    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.send_input", _send_input)

    async_network_driver._current_priv_level = async_network_driver.privilege_levels[
        "privilege_exec"
    ]
    await async_network_driver.acquire_priv(desired_priv="configuration")


async def test_acquire_priv_deescalate(monkeypatch, async_network_driver):
    _prompt_counter = 0

    async def _get_prompt(cls):
        nonlocal _prompt_counter
        if _prompt_counter == 0:
            prompt = "scrapli(config)#"
        else:
            prompt = "scrapli#"
        _prompt_counter += 1
        return prompt

    async def _send_input(cls, channel_input, **kwargs):
        assert channel_input == "end"
        return b"scrapli#", b"scrapli#"

    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.get_prompt", _get_prompt)
    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.send_input", _send_input)

    async_network_driver._current_priv_level = async_network_driver.privilege_levels[
        "configuration"
    ]
    await async_network_driver.acquire_priv(desired_priv="privilege_exec")


async def test_acquire_priv_escalate_not_ready_same_priv(monkeypatch, async_network_driver):
    """
    This tests to make sure that if the device does something like ceos does like this:

    ```
    info::ceos::"sending channelInput: enable; stripPrompt: false; eager: false
    write::ceos::write: enable
    debug::ceos::read: enable
    write::ceos::write:
    debug::ceos::read:
    debug::ceos::read: % Authorization denied for command 'enable': Default authorization provider rejects all commands
    debug::ceos::read: ceos>
    ```

    we gracefully handle returning to the current priv level -- rather than only being okay with
    seeing a password prompt and/or the *next* pirv level. Thank you @ntdvps/@hellt (Roman) for
    helping find this issue!

    """
    _prompt_counter = 0

    async def _get_prompt(cls):
        nonlocal _prompt_counter
        if _prompt_counter == 0:
            prompt = "scrapli>"
        elif _prompt_counter == 1:
            prompt = "scrapli>"
        else:
            prompt = "scrapli#"
        _prompt_counter += 1
        return prompt

    async def __read_until_input(cls, channel_input):
        return channel_input

    async def __read_until_explicit_prompt(cls, prompts):
        # we dont really care what we return here, just needs to be bytes. but we *do* care that
        # in this case we are receiving *three* prompt patterns -- the password pattern, the
        # escalate priv pattern, and the *current* priv pattern.
        assert len(prompts) == 3

        return b"scrapli>"

    def _write(cls, channel_input, **kwargs):
        return

    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.get_prompt", _get_prompt)
    monkeypatch.setattr(
        "scrapli.channel.async_channel.AsyncChannel._read_until_input", __read_until_input
    )
    monkeypatch.setattr(
        "scrapli.channel.async_channel.AsyncChannel._read_until_explicit_prompt",
        __read_until_explicit_prompt,
    )
    monkeypatch.setattr(
        "scrapli.transport.plugins.asynctelnet.transport.AsynctelnetTransport.write", _write
    )

    async_network_driver._current_priv_level = async_network_driver.privilege_levels["exec"]
    await async_network_driver.acquire_priv(desired_priv="privilege_exec")


async def test_acquire_priv_failure(monkeypatch, async_network_driver):
    async def _get_prompt(cls):
        return "scrapli(config)#"

    async def _send_input(cls, channel_input, **kwargs):
        assert channel_input == "end"
        return b"scrapli(config)#", b"scrapli(config)#"

    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.get_prompt", _get_prompt)
    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.send_input", _send_input)

    async_network_driver._current_priv_level = async_network_driver.privilege_levels[
        "configuration"
    ]

    with pytest.raises(ScrapliPrivilegeError):
        await async_network_driver.acquire_priv(desired_priv="privilege_exec")


async def test_acquire_appropriate_privilege_level(monkeypatch, async_network_driver):
    _acquire_priv_called = False

    async def _acquire_priv(cls, **kwargs):
        nonlocal _acquire_priv_called
        _acquire_priv_called = True
        return

    # patching acquire priv so we know its called but dont have to worry about that actually
    # trying to happen
    monkeypatch.setattr(
        "scrapli.driver.network.async_driver.AsyncNetworkDriver.acquire_priv", _acquire_priv
    )

    _validate_privilege_level_name_called = False

    def _validate_privilege_level_name(cls, **kwargs):
        nonlocal _validate_privilege_level_name_called
        _validate_privilege_level_name_called = True
        return

    monkeypatch.setattr(
        "scrapli.driver.network.async_driver.AsyncNetworkDriver._validate_privilege_level_name",
        _validate_privilege_level_name,
    )

    async def _reset_called_flags():
        nonlocal _acquire_priv_called, _validate_privilege_level_name_called
        _acquire_priv_called = False
        _validate_privilege_level_name_called = False

    # Test default_desired_privilege_level
    await _reset_called_flags()
    await async_network_driver._acquire_appropriate_privilege_level()
    assert _validate_privilege_level_name_called is False
    assert _acquire_priv_called is True

    # Test the privilege_level is the same as the async_network_driver._current_priv_level.name
    await _reset_called_flags()
    await async_network_driver._acquire_appropriate_privilege_level(
        async_network_driver._current_priv_level.name
    )
    assert _validate_privilege_level_name_called is True
    assert _acquire_priv_called is False

    # Test privilege_level is different that async_network_driver._current_priv_level.name
    await _reset_called_flags()
    await async_network_driver._acquire_appropriate_privilege_level("configuration")
    assert _validate_privilege_level_name_called is True
    assert _acquire_priv_called is True

    # Test when _generic_driver_mode = True
    await _reset_called_flags()
    async_network_driver._generic_driver_mode = True
    await async_network_driver._acquire_appropriate_privilege_level()
    assert _validate_privilege_level_name_called is False
    assert _acquire_priv_called is False

    # Test when _generic_driver_mode = True and privilege_level is different than _current_priv_level
    await _reset_called_flags()
    async_network_driver._generic_driver_mode = True
    await async_network_driver._acquire_appropriate_privilege_level("configuration")
    assert _validate_privilege_level_name_called is True
    assert _acquire_priv_called is True

    # Test when _generic_driver_mode = True and privilege_level is same as _current_priv_level
    await _reset_called_flags()
    async_network_driver._generic_driver_mode = True
    await async_network_driver._acquire_appropriate_privilege_level(
        async_network_driver._current_priv_level.name
    )
    assert _validate_privilege_level_name_called is True
    assert _acquire_priv_called is False


async def test_send_command(monkeypatch, async_network_driver):
    async def _acquire_appropriate_privilege_level(cls, **kwargs):
        return

    monkeypatch.setattr(
        "scrapli.driver.network.async_driver.AsyncNetworkDriver._acquire_appropriate_privilege_level",
        _acquire_appropriate_privilege_level,
    )

    async def _send_input(cls, channel_input, **kwargs):
        assert channel_input == "show version"
        return b"raw", b"processed"

    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.send_input", _send_input)

    actual_response = await async_network_driver.send_command(command="show version")

    assert actual_response.failed is False
    assert actual_response.result == "processed"
    assert actual_response.raw_result == b"raw"


async def test_send_commands(monkeypatch, async_network_driver):
    async def _acquire_appropriate_privilege_level(cls, **kwargs):
        return

    monkeypatch.setattr(
        "scrapli.driver.network.async_driver.AsyncNetworkDriver._acquire_appropriate_privilege_level",
        _acquire_appropriate_privilege_level,
    )

    _command_counter = 0

    async def _send_input(cls, channel_input, **kwargs):
        nonlocal _command_counter
        if _command_counter == 0:
            assert channel_input == "show version"
        else:
            assert channel_input == "show run"

        _command_counter += 1
        return b"raw", b"processed"

    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.send_input", _send_input)

    actual_response = await async_network_driver.send_commands(
        commands=["show version", "show run"]
    )

    assert actual_response.failed is False
    assert actual_response[0].result == "processed"
    assert actual_response[0].raw_result == b"raw"


async def test_send_commands_from_file(
    fs_, monkeypatch, real_ssh_commands_file_path, async_network_driver
):
    fs_.add_real_file(source_path=real_ssh_commands_file_path, target_path="/commands")

    async def _acquire_appropriate_privilege_level(cls, **kwargs):
        return

    monkeypatch.setattr(
        "scrapli.driver.network.async_driver.AsyncNetworkDriver._acquire_appropriate_privilege_level",
        _acquire_appropriate_privilege_level,
    )

    async def _send_input(cls, channel_input, **kwargs):
        assert channel_input == "show version"
        return b"raw", b"processed"

    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.send_input", _send_input)

    actual_response = await async_network_driver.send_commands_from_file(file="commands")

    assert actual_response.failed is False
    assert actual_response[0].result == "processed"
    assert actual_response[0].raw_result == b"raw"


async def test_send_interactive(monkeypatch, async_network_driver):
    async def _acquire_appropriate_privilege_level(cls, **kwargs):
        return

    monkeypatch.setattr(
        "scrapli.driver.network.async_driver.AsyncNetworkDriver._acquire_appropriate_privilege_level",
        _acquire_appropriate_privilege_level,
    )

    async def _send_inputs_interact(cls, **kwargs):
        return b"raw", b"processed"

    monkeypatch.setattr(
        "scrapli.channel.async_channel.AsyncChannel.send_inputs_interact", _send_inputs_interact
    )

    async_network_driver._current_priv_level = async_network_driver.privilege_levels[
        "privilege_exec"
    ]
    actual_response = await async_network_driver.send_interactive(
        interact_events=[("nada", "scrapli>")]
    )

    assert actual_response.failed is False
    assert actual_response.result == "processed"
    assert actual_response.raw_result == b"raw"


async def test_send_configs(monkeypatch, async_network_driver):
    async def _acquire_priv(cls, **kwargs):
        return

    # patching acquire priv so we know its called but dont have to worry about that actually
    # trying to happen
    monkeypatch.setattr(
        "scrapli.driver.network.async_driver.AsyncNetworkDriver.acquire_priv", _acquire_priv
    )

    _command_counter = 0

    async def _send_input(cls, channel_input, **kwargs):
        nonlocal _command_counter
        if _command_counter == 0:
            assert channel_input == "interface loopback123"
        else:
            assert channel_input == "description tests are boring"

        _command_counter += 1
        return b"raw", b"processed"

    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.send_input", _send_input)

    async_network_driver._current_priv_level = async_network_driver.privilege_levels[
        "privilege_exec"
    ]
    actual_response = await async_network_driver.send_configs(
        configs=["interface loopback123", "description tests are boring"]
    )

    assert actual_response.failed is False
    assert actual_response[0].result == "processed"
    assert actual_response[0].raw_result == b"raw"


async def test_send_config(monkeypatch, async_network_driver):
    async def _acquire_priv(cls, **kwargs):
        return

    # patching acquire priv so we know its called but dont have to worry about that actually
    # trying to happen
    monkeypatch.setattr(
        "scrapli.driver.network.async_driver.AsyncNetworkDriver.acquire_priv", _acquire_priv
    )

    _command_counter = 0

    async def _send_input(cls, channel_input, **kwargs):
        nonlocal _command_counter
        if _command_counter == 0:
            assert channel_input == "interface loopback123"
        else:
            assert channel_input == "description tests are boring"

        _command_counter += 1
        return b"raw", b"processed"

    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.send_input", _send_input)

    async_network_driver._current_priv_level = async_network_driver.privilege_levels[
        "privilege_exec"
    ]
    actual_response = await async_network_driver.send_config(
        config="interface loopback123\ndescription tests are boring"
    )

    assert actual_response.failed is False
    assert actual_response.result == "processed\nprocessed"
    assert actual_response.raw_result == b""


async def test_send_configs_from_file(
    fs_, monkeypatch, real_ssh_commands_file_path, async_network_driver
):
    fs_.add_real_file(source_path=real_ssh_commands_file_path, target_path="/configs")

    async def _acquire_priv(cls, **kwargs):
        return

    # patching acquire priv so we know its called but dont have to worry about that actually
    # trying to happen
    monkeypatch.setattr(
        "scrapli.driver.network.async_driver.AsyncNetworkDriver.acquire_priv", _acquire_priv
    )

    async def _send_input(cls, channel_input, **kwargs):
        assert channel_input == "show version"
        return b"raw", b"processed"

    monkeypatch.setattr("scrapli.channel.async_channel.AsyncChannel.send_input", _send_input)

    async_network_driver._current_priv_level = async_network_driver.privilege_levels[
        "privilege_exec"
    ]
    actual_response = await async_network_driver.send_configs_from_file(file="configs")

    assert actual_response.failed is False
    assert actual_response.result == "show version\nprocessed"
