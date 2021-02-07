def test_on_open(monkeypatch, sync_junos_driver):
    _input_counter = 0

    def _get_prompt(cls):
        return "scrapli>"

    def _send_input(cls, channel_input, **kwargs):
        nonlocal _input_counter

        if _input_counter == 0:
            assert channel_input == "set cli complete-on-space off"
        elif _input_counter == 1:
            assert channel_input == "set cli screen-length 0"
        else:
            assert channel_input == "set cli screen-width 511"

        _input_counter += 1

        return b"", b""

    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.get_prompt", _get_prompt)
    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.send_input", _send_input)

    sync_junos_driver._current_priv_level = sync_junos_driver.privilege_levels["exec"]
    sync_junos_driver.on_open(sync_junos_driver)


def test_on_close(monkeypatch, sync_junos_driver):
    def _get_prompt(cls):
        return "scrapli>"

    def _write(cls, channel_input, **kwargs):
        assert channel_input == "exit"

    def _send_return(cls):
        pass

    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.get_prompt", _get_prompt)
    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.write", _write)
    monkeypatch.setattr("scrapli.channel.sync_channel.Channel.send_return", _send_return)

    sync_junos_driver._current_priv_level = sync_junos_driver.privilege_levels["exec"]
    sync_junos_driver.on_close(sync_junos_driver)
