import pytest

from scrapli.exceptions import ScrapliPrivilegeError


def test_escalate(monkeypatch, sync_network_driver):
    def _send_input(cls, channel_input, **kwargs):
        assert channel_input == "configure terminal"
        return b"raw", b"processed"

    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.send_input", _send_input)

    sync_network_driver._current_priv_level = sync_network_driver.privilege_levels["privilege_exec"]
    sync_network_driver._escalate(
        escalate_priv=sync_network_driver.privilege_levels["configuration"]
    )


def test_escalate_auth_secondary(monkeypatch, sync_network_driver):
    def _send_inputs_interact(cls, interact_events, **kwargs):
        assert interact_events[0][0] == "enable"
        return b"raw", b"processed"

    monkeypatch.setattr(
        "scrapli.channel.sync_channel.Channel.send_inputs_interact", _send_inputs_interact
    )

    # patching send inputs interactive means if this passes we know we had to do an "authy" escalation
    sync_network_driver._current_priv_level = sync_network_driver.privilege_levels["exec"]
    sync_network_driver._escalate(
        escalate_priv=sync_network_driver.privilege_levels["privilege_exec"]
    )


def test_deescalate(monkeypatch, sync_network_driver):
    def _send_input(cls, channel_input, **kwargs):
        assert channel_input == "disable"
        return b"raw", b"processed"

    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.send_input", _send_input)

    sync_network_driver._current_priv_level = "privilege_exec"
    sync_network_driver._deescalate(
        current_priv=sync_network_driver.privilege_levels["privilege_exec"]
    )


def test_acquire_priv_no_action(monkeypatch, sync_network_driver):
    monkeypatch.setattr(
        "scrapli.channel.sync_channel.Channel.get_prompt",
        lambda _, **kwargs: "scrapli#",
    )

    sync_network_driver._current_priv_level = "privilege_exec"
    sync_network_driver.acquire_priv(desired_priv="privilege_exec")


def test_acquire_priv_escalate(monkeypatch, sync_network_driver):
    _prompt_counter = 0

    def _get_prompt(cls):
        nonlocal _prompt_counter
        if _prompt_counter == 0:
            prompt = "scrapli#"
        else:
            prompt = "scrapli(config)#"
        _prompt_counter += 1
        return prompt

    def _send_input(cls, channel_input, **kwargs):
        assert channel_input == "configure terminal"
        return b"scrapli(config)#", b"scrapli(config)#"

    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.get_prompt", _get_prompt)
    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.send_input", _send_input)

    sync_network_driver._current_priv_level = "privilege_exec"
    sync_network_driver.acquire_priv(desired_priv="configuration")


def test_acquire_priv_deescalate(monkeypatch, sync_network_driver):
    _prompt_counter = 0

    def _get_prompt(cls):
        nonlocal _prompt_counter
        if _prompt_counter == 0:
            prompt = "scrapli(config)#"
        else:
            prompt = "scrapli#"
        _prompt_counter += 1
        return prompt

    def _send_input(cls, channel_input, **kwargs):
        assert channel_input == "end"
        return b"scrapli#", b"scrapli#"

    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.get_prompt", _get_prompt)
    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.send_input", _send_input)

    sync_network_driver._current_priv_level = "configuration"
    sync_network_driver.acquire_priv(desired_priv="privilege_exec")


def test_acquire_priv_failure(monkeypatch, sync_network_driver):
    def _get_prompt(cls):
        return "scrapli(config)#"

    def _send_input(cls, channel_input, **kwargs):
        assert channel_input == "end"
        return b"scrapli(config)#", b"scrapli(config)#"

    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.get_prompt", _get_prompt)
    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.send_input", _send_input)

    sync_network_driver._current_priv_level = "configuration"

    with pytest.raises(ScrapliPrivilegeError):
        sync_network_driver.acquire_priv(desired_priv="privilege_exec")


def test_send_command(monkeypatch, sync_network_driver):
    def _acquire_priv(cls, **kwargs):
        return

    # patching acquire priv so we know its called but dont have to worry about that actually
    # trying to happen
    monkeypatch.setattr(
        "scrapli.driver.network.sync_driver.NetworkDriver.acquire_priv", _acquire_priv
    )

    def _send_input(cls, channel_input, **kwargs):
        assert channel_input == "show version"
        return b"raw", b"processed"

    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.send_input", _send_input)

    sync_network_driver._current_priv_level = sync_network_driver.privilege_levels["privilege_exec"]
    sync_network_driver.default_desired_privilege_level = "exec"
    actual_response = sync_network_driver.send_command(command="show version")

    assert actual_response.failed is False
    assert actual_response.result == "processed"
    assert actual_response.raw_result == b"raw"


def test_send_commands(monkeypatch, sync_network_driver):
    def _acquire_priv(cls, **kwargs):
        return

    # patching acquire priv so we know its called but dont have to worry about that actually
    # trying to happen
    monkeypatch.setattr(
        "scrapli.driver.network.sync_driver.NetworkDriver.acquire_priv", _acquire_priv
    )

    _command_counter = 0

    def _send_input(cls, channel_input, **kwargs):
        nonlocal _command_counter
        if _command_counter == 0:
            assert channel_input == "show version"
        else:
            assert channel_input == "show run"

        _command_counter += 1
        return b"raw", b"processed"

    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.send_input", _send_input)

    sync_network_driver._current_priv_level = sync_network_driver.privilege_levels["privilege_exec"]
    sync_network_driver.default_desired_privilege_level = "exec"
    actual_response = sync_network_driver.send_commands(commands=["show version", "show run"])

    assert actual_response.failed is False
    assert actual_response[0].result == "processed"
    assert actual_response[0].raw_result == b"raw"


def test_send_commands_from_file(fs, monkeypatch, real_ssh_commands_file_path, sync_network_driver):
    fs.add_real_file(source_path=real_ssh_commands_file_path, target_path="/commands")

    def _acquire_priv(cls, **kwargs):
        return

    # patching acquire priv so we know its called but dont have to worry about that actually
    # trying to happen
    monkeypatch.setattr(
        "scrapli.driver.network.sync_driver.NetworkDriver.acquire_priv", _acquire_priv
    )

    def _send_input(cls, channel_input, **kwargs):
        assert channel_input == "show version"
        return b"raw", b"processed"

    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.send_input", _send_input)

    sync_network_driver._current_priv_level = sync_network_driver.privilege_levels["privilege_exec"]
    sync_network_driver.default_desired_privilege_level = "exec"
    actual_response = sync_network_driver.send_commands_from_file(file="commands")

    assert actual_response.failed is False
    assert actual_response[0].result == "processed"
    assert actual_response[0].raw_result == b"raw"


def test_send_interactive(monkeypatch, sync_network_driver):
    def _acquire_priv(cls, **kwargs):
        return

    # patching acquire priv so we know its called but dont have to worry about that actually
    # trying to happen
    monkeypatch.setattr(
        "scrapli.driver.network.sync_driver.NetworkDriver.acquire_priv", _acquire_priv
    )

    def _send_inputs_interact(cls, **kwargs):
        return b"raw", b"processed"

    monkeypatch.setattr(
        "scrapli.channel.sync_channel.Channel.send_inputs_interact", _send_inputs_interact
    )

    sync_network_driver._current_priv_level = sync_network_driver.privilege_levels["privilege_exec"]
    sync_network_driver.default_desired_privilege_level = "exec"
    actual_response = sync_network_driver.send_interactive(interact_events=[("nada", "scrapli>")])

    assert actual_response.failed is False
    assert actual_response.result == "processed"
    assert actual_response.raw_result == b"raw"


def test_send_configs(monkeypatch, sync_network_driver):
    def _acquire_priv(cls, **kwargs):
        return

    # patching acquire priv so we know its called but dont have to worry about that actually
    # trying to happen
    monkeypatch.setattr(
        "scrapli.driver.network.sync_driver.NetworkDriver.acquire_priv", _acquire_priv
    )

    _command_counter = 0

    def _send_input(cls, channel_input, **kwargs):
        nonlocal _command_counter
        if _command_counter == 0:
            assert channel_input == "interface loopback123"
        else:
            assert channel_input == "description tests are boring"

        _command_counter += 1
        return b"raw", b"processed"

    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.send_input", _send_input)

    sync_network_driver._current_priv_level = sync_network_driver.privilege_levels["privilege_exec"]
    actual_response = sync_network_driver.send_configs(
        configs=["interface loopback123", "description tests are boring"]
    )

    assert actual_response.failed is False
    assert actual_response[0].result == "processed"
    assert actual_response[0].raw_result == b"raw"


def test_send_config(monkeypatch, sync_network_driver):
    def _acquire_priv(cls, **kwargs):
        return

    # patching acquire priv so we know its called but dont have to worry about that actually
    # trying to happen
    monkeypatch.setattr(
        "scrapli.driver.network.sync_driver.NetworkDriver.acquire_priv", _acquire_priv
    )

    _command_counter = 0

    def _send_input(cls, channel_input, **kwargs):
        nonlocal _command_counter
        if _command_counter == 0:
            assert channel_input == "interface loopback123"
        else:
            assert channel_input == "description tests are boring"

        _command_counter += 1
        return b"raw", b"processed"

    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.send_input", _send_input)

    sync_network_driver._current_priv_level = sync_network_driver.privilege_levels["privilege_exec"]
    actual_response = sync_network_driver.send_config(
        config="interface loopback123\ndescription tests are boring"
    )

    assert actual_response.failed is False
    assert actual_response.result == "processed\nprocessed"
    assert actual_response.raw_result == b""


def test_send_configs_from_file(fs, monkeypatch, real_ssh_commands_file_path, sync_network_driver):
    fs.add_real_file(source_path=real_ssh_commands_file_path, target_path="/configs")

    def _acquire_priv(cls, **kwargs):
        return

    # patching acquire priv so we know its called but dont have to worry about that actually
    # trying to happen
    monkeypatch.setattr(
        "scrapli.driver.network.sync_driver.NetworkDriver.acquire_priv", _acquire_priv
    )

    def _send_input(cls, channel_input, **kwargs):
        assert channel_input == "show version"
        return b"raw", b"processed"

    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.send_input", _send_input)

    sync_network_driver._current_priv_level = sync_network_driver.privilege_levels["privilege_exec"]
    actual_response = sync_network_driver.send_configs_from_file(file="configs")

    assert actual_response.failed is False
    assert actual_response.result == "show version\nprocessed"
