def test_on_open(monkeypatch, sync_eos_driver):
    _input_counter = 0

    def _get_prompt(cls):
        return "scrapli#"

    def _send_input(cls, channel_input, **kwargs):
        nonlocal _input_counter

        if _input_counter == 0:
            assert channel_input == "terminal length 0"
        else:
            assert channel_input == "terminal width 32767"

        _input_counter += 1

    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.get_prompt", _get_prompt)
    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.send_input", _send_input)

    sync_eos_driver._current_priv_level = sync_eos_driver.privilege_levels["privilege_exec"]
    sync_eos_driver.on_open(sync_eos_driver)


def test_on_close(monkeypatch, sync_eos_driver):
    def _get_prompt(cls):
        return "scrapli#"

    def _write(cls, channel_input, **kwargs):
        assert channel_input == "exit"

    def _send_return(cls):
        pass

    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.get_prompt", _get_prompt)
    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.write", _write)
    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.send_return", _send_return)

    sync_eos_driver._current_priv_level = sync_eos_driver.privilege_levels["privilege_exec"]
    sync_eos_driver.on_close(sync_eos_driver)


def test_register_and_abort_config(monkeypatch, sync_eos_driver):
    def _send_input(cls, channel_input, **kwargs):
        assert channel_input == "abort"

    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.send_input", _send_input)

    sync_eos_driver.register_configuration_session(session_name="scrapli")
    sync_eos_driver._current_priv_level = sync_eos_driver.privilege_levels["scrapli"]
    sync_eos_driver._abort_config()

    assert sync_eos_driver._current_priv_level.name == "privilege_exec"
