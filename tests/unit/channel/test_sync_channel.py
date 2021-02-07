import logging
import time
from pathlib import Path

import pytest

from scrapli.channel.base_channel import BaseChannelArgs
from scrapli.channel.sync_channel import Channel
from scrapli.exceptions import ScrapliAuthenticationFailed


def test_channel_lock(base_transport_no_abc):
    base_channel_args = BaseChannelArgs(channel_lock=True)
    sync_channel = Channel(transport=base_transport_no_abc, base_channel_args=base_channel_args)
    assert sync_channel.channel_lock


def test_channel_lock_context_manager(base_transport_no_abc):
    base_channel_args = BaseChannelArgs(channel_lock=True)
    sync_channel = Channel(transport=base_transport_no_abc, base_channel_args=base_channel_args)
    assert sync_channel.channel_lock.locked() is False
    with sync_channel._channel_lock():
        assert sync_channel.channel_lock.locked() is True
    assert sync_channel.channel_lock.locked() is False


def test_channel_lock_context_manager_no_channel_lock(base_transport_no_abc):
    base_channel_args = BaseChannelArgs(channel_lock=False)
    sync_channel = Channel(transport=base_transport_no_abc, base_channel_args=base_channel_args)
    with sync_channel._channel_lock():
        assert True


def test_channel_read(fs, caplog, monkeypatch, sync_transport_no_abc):
    # fs needed to mock filesystem for asserting log location
    _ = fs
    caplog.set_level(logging.DEBUG, logger="scrapli.channel")

    channel_read_called = False
    expected_read_output = b"read_data"

    base_channel_args = BaseChannelArgs(channel_log=True)
    sync_channel = Channel(transport=sync_transport_no_abc, base_channel_args=base_channel_args)

    def _read(cls):
        nonlocal channel_read_called
        channel_read_called = True
        return b"read_data\r"

    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.read", _read)

    actual_read_output = sync_channel.read()
    sync_channel.channel_log.close()

    assert channel_read_called is True
    assert actual_read_output == expected_read_output

    # assert the log output/level as expected; skip the first log message that will be about
    # channel_log being on
    log_record = caplog.records[1]
    assert "read: b'read_data'" == log_record.msg
    assert logging.DEBUG == log_record.levelno

    # assert channel log output as expected
    assert Path("/scrapli_channel.log").is_file()
    with open("/scrapli_channel.log", "r") as actual_channel_log:
        assert actual_channel_log.readline() == "read_data"


def test_channel_read_until_input(monkeypatch, sync_channel):
    sync_channel._base_channel_args.comms_ansi = True

    expected_read_output = b"read_data\nthisismyinput"
    _read_counter = 0

    def _read(cls):
        nonlocal _read_counter

        if _read_counter == 0:
            _read_counter += 1
            return b"read_data\x1b[0;0m\n"

        return b"thisismyinput"

    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.read", _read)

    actual_read_output = sync_channel._read_until_input(channel_input=b"thisismyinput")

    assert actual_read_output == expected_read_output


def test_channel_read_until_input_no_input(sync_channel):
    assert sync_channel._read_until_input(channel_input=b"") == b""


def test_channel_read_until_prompt(monkeypatch, sync_channel):
    sync_channel._base_channel_args.comms_ansi = True

    expected_read_output = b"read_data\nscrapli>"
    _read_counter = 0

    def _read(cls):
        nonlocal _read_counter

        if _read_counter == 0:
            _read_counter += 1
            return b"read_data\x1b[0;0m\n"

        return b"scrapli>"

    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.read", _read)

    actual_read_output = sync_channel._read_until_prompt()

    assert actual_read_output == expected_read_output


# TODO read until prompt/time


def test_channel_authenticate_ssh(monkeypatch, sync_channel):
    sync_channel._base_channel_args.comms_ansi = True

    _read_counter = 0
    _write_counter = 0

    def _read(cls):
        nonlocal _read_counter

        if _read_counter == 0:
            _read_counter += 1
            return b"blah blah blah"

        elif _read_counter == 1:
            _read_counter += 1
            return b"enter passphrase for key"

        elif _read_counter == 2:
            _read_counter += 1
            return b"blah blah blah"

        elif _read_counter == 3:
            _read_counter += 1
            return b"password"

        elif _read_counter == 4:
            _read_counter += 1
            return b"blah blah blah"

        return b"scrapli>"

    def _write(cls, channel_input):
        # just making this a non-op
        pass

    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.read", _read)
    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.write", _write)

    sync_channel._base_channel_args.comms_prompt_pattern = "scrapli>"
    sync_channel.channel_authenticate_ssh(
        auth_password="scrapli", auth_private_key_passphrase="scrapli_key"
    )


def test_channel_authenticate_ssh_fail_password(monkeypatch, sync_channel):
    sync_channel._base_channel_args.comms_ansi = True

    def _read(cls):
        return b"password"

    def _write(cls, channel_input):
        # just making this a non-op
        pass

    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.read", _read)
    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.write", _write)

    with pytest.raises(ScrapliAuthenticationFailed):
        sync_channel.channel_authenticate_ssh(
            auth_password="scrapli", auth_private_key_passphrase="scrapli_key"
        )


def test_channel_authenticate_ssh_fail_passphrase(monkeypatch, sync_channel):
    sync_channel._base_channel_args.comms_ansi = True

    def _read(cls):
        return b"enter passphrase for key"

    def _write(cls, channel_input):
        # just making this a non-op
        pass

    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.read", _read)
    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.write", _write)

    with pytest.raises(ScrapliAuthenticationFailed):
        sync_channel.channel_authenticate_ssh(
            auth_password="scrapli", auth_private_key_passphrase="scrapli_key"
        )


def test_channel_authenticate_telnet(monkeypatch, sync_channel):
    sync_channel._base_channel_args.comms_ansi = True

    _read_counter = 0
    _write_counter = 0

    def _read(cls):
        nonlocal _read_counter

        if _read_counter == 0:
            _read_counter += 1
            return b"blah blah blah"

        elif _read_counter == 1:
            _read_counter += 1
            return b"login:"

        elif _read_counter == 2:
            _read_counter += 1
            return b"blah blah blah"

        elif _read_counter == 3:
            _read_counter += 1
            return b"password:"

        elif _read_counter == 4:
            _read_counter += 1
            return b"blah blah blah"

        return b"scrapli>"

    def _write(cls, channel_input):
        # just making this a non-op
        pass

    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.read", _read)
    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.write", _write)

    sync_channel._base_channel_args.comms_prompt_pattern = "scrapli>"
    sync_channel.transport.username_prompt = "login:"
    sync_channel.transport.password_prompt = "password:"
    sync_channel.channel_authenticate_telnet(auth_username="scrapli", auth_password="scrapli")


def test_channel_authenticate_telnet_fail_login(monkeypatch, sync_channel):
    sync_channel._base_channel_args.comms_ansi = True

    def _read(cls):
        return b"login:"

    def _write(cls, channel_input):
        # just making this a non-op
        pass

    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.read", _read)
    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.write", _write)

    sync_channel.transport.username_prompt = "login:"
    sync_channel.transport.password_prompt = "password:"

    with pytest.raises(ScrapliAuthenticationFailed):
        sync_channel.channel_authenticate_telnet(auth_username="scrapli", auth_password="scrapli")


def test_channel_authenticate_telnet_fail_password(monkeypatch, sync_channel):
    sync_channel._base_channel_args.comms_ansi = True

    def _read(cls):
        return b"password:"

    def _write(cls, channel_input):
        # just making this a non-op
        pass

    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.read", _read)
    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.write", _write)

    sync_channel.transport.username_prompt = "login:"
    sync_channel.transport.password_prompt = "password:"

    with pytest.raises(ScrapliAuthenticationFailed):
        sync_channel.channel_authenticate_telnet(auth_username="scrapli", auth_password="scrapli")


def test_channel_authenticate_telnet_send_return(monkeypatch, sync_channel):
    _read_counter = 0
    _write_counter = 0

    def _read(cls):
        nonlocal _read_counter

        if _read_counter == 0:
            _read_counter += 1
            time.sleep(1)
            return b""

        elif _read_counter == 1:
            _read_counter += 1
            return b"login:"

        elif _read_counter == 2:
            _read_counter += 1
            return b"blah blah blah"

        elif _read_counter == 3:
            _read_counter += 1
            return b"password:"

        elif _read_counter == 4:
            _read_counter += 1
            return b"blah blah blah"

        return b"scrapli>"

    def _write(cls, channel_input):
        nonlocal _write_counter

        if _write_counter == 0:
            _write_counter += 1
            # asserting that after the sleep we send a return to "wake up" the telnet channel
            assert channel_input == b"\n"
        pass

    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.read", _read)
    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.write", _write)

    sync_channel._base_channel_args.comms_ansi = True
    sync_channel._base_channel_args.comms_prompt_pattern = "scrapli>"
    sync_channel._base_channel_args.timeout_ops = 3
    sync_channel.transport.username_prompt = "login:"
    sync_channel.transport.password_prompt = "password:"

    sync_channel.channel_authenticate_telnet(auth_username="scrapli", auth_password="scrapli")


def test_get_prompt(monkeypatch, sync_channel):
    _read_counter = 0

    def _read(cls):
        nonlocal _read_counter

        if _read_counter == 0:
            # just sending something bad for first iteration so that we validate it "loops" looking
            # for the prompt
            _read_counter += 1
            return b"blahgarbage"
        return b"scrapli>"

    def _write(cls, channel_input):
        pass

    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.read", _read)
    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.write", _write)

    sync_channel._base_channel_args.comms_ansi = True
    sync_channel._base_channel_args.comms_prompt_pattern = "scrapli>"

    assert sync_channel.get_prompt() == "scrapli>"


def test_send_input(monkeypatch, sync_channel):
    _read_counter = 0

    channel_input = "show version"
    expected_buf = b"output from show version!\nscrapli>"
    expected_processed_buf = b"output from show version!"

    def _read(cls):
        nonlocal _read_counter

        if _read_counter == 0:
            # echo the input back
            _read_counter += 1
            return channel_input.encode()
        elif _read_counter == 1:
            _read_counter += 1
            return b"output from show version!\n"
        return b"scrapli>"

    def _write(cls, channel_input):
        pass

    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.read", _read)
    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.write", _write)

    sync_channel._base_channel_args.comms_prompt_pattern = "scrapli>"

    actual_buf, actual_processed_buf = sync_channel.send_input(channel_input=channel_input)
    assert actual_buf == expected_buf
    assert actual_processed_buf == expected_processed_buf


def test_send_input_and_read(monkeypatch, sync_channel):
    _read_counter = 0

    channel_input = "show version"
    expected_buf = b"output from show version!\nimexpectingtoseethis"

    def _read(cls):
        nonlocal _read_counter

        if _read_counter == 0:
            # echo the input back
            _read_counter += 1
            return channel_input.encode()
        elif _read_counter == 1:
            _read_counter += 1
            return b"output from show version!\n"
        return b"imexpectingtoseethis"

    def _write(cls, channel_input):
        pass

    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.read", _read)
    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.write", _write)

    sync_channel._base_channel_args.comms_prompt_pattern = "scrapli>"

    actual_buf, actual_processed_buf = sync_channel.send_input_and_read(
        channel_input=channel_input, expected_outputs=["imexpectingtoseethis"]
    )
    assert actual_buf == expected_buf
    assert actual_processed_buf == expected_buf


def test_send_inputs_interact(monkeypatch, sync_channel):
    _read_counter = 0
    _event_counter = 0

    interact_events = [("clear logg", "[confirm]\n"), ("", "scrapli>")]
    expected_buf = b"clear logg[confirm]\nscrapli>"

    def _read(cls):
        nonlocal _read_counter
        nonlocal _event_counter
        nonlocal interact_events

        output = interact_events[_read_counter][_event_counter].encode()
        _event_counter += 1

        if _event_counter == 2:
            # reset the "event" counter as there will only be two things to output per event;
            # the "input" (channel_input) then the output/expected prompt... so tl;dr...
            # "read_counter" is more like event stage, then event_counter is counter for each read
            # within the event
            _event_counter = 0
            _read_counter += 1

        return output

    def _write(cls, channel_input):
        # making a non-op... can also assert inputs are right/in the right order at some point
        pass

    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.read", _read)
    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.write", _write)

    sync_channel._base_channel_args.comms_prompt_pattern = "scrapli>"

    actual_buf, actual_processed_buf = sync_channel.send_inputs_interact(
        interact_events=interact_events
    )
    assert actual_buf == expected_buf
    assert actual_processed_buf == expected_buf


def test_send_inputs_interact_hidden_input(monkeypatch, sync_channel):
    _read_counter = 0
    _event_counter = 0

    interact_events = [("enable", "password:"), ("sneakypassword", "scrapli>", True)]
    expected_buf = b"enablepassword:scrapli>"

    def _read(cls):
        nonlocal _read_counter
        nonlocal _event_counter
        nonlocal interact_events

        if _read_counter == 1:
            # if we are on the second event we'll skip reading input as it would be the password
            _event_counter += 1

        output = interact_events[_read_counter][_event_counter].encode()
        _event_counter += 1

        if _event_counter == 2:
            # reset the "event" counter as there will only be two things to output per event;
            # the "input" (channel_input) then the output/expected prompt... so tl;dr...
            # "read_counter" is more like event stage, then event_counter is counter for each read
            # within the event
            _event_counter = 0
            _read_counter += 1

        return output

    def _write(cls, channel_input):
        # making a non-op... can also assert inputs are right/in the right order at some point
        pass

    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.read", _read)
    monkeypatch.setattr("scrapli.transport.base.sync_transport.Transport.write", _write)

    sync_channel._base_channel_args.comms_prompt_pattern = "scrapli>"

    actual_buf, actual_processed_buf = sync_channel.send_inputs_interact(
        interact_events=interact_events
    )
    assert actual_buf == expected_buf
    assert actual_processed_buf == expected_buf
