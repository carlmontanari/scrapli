import logging
import re
from io import BytesIO
from pathlib import Path

import pytest

from scrapli.channel.base_channel import BaseChannel, BaseChannelArgs
from scrapli.exceptions import ScrapliAuthenticationFailed, ScrapliTypeError, ScrapliValueError


@pytest.mark.parametrize(
    "test_data",
    (
        (
            "auth_telnet_login_pattern",
            r"^(.*username:)|(.*login:)\s?$",
        ),
        (
            "auth_password_pattern",
            r"(.*@.*)?password:\s?$",
        ),
        (
            "auth_passphrase_pattern",
            "enter passphrase for key",
        ),
    ),
    ids=(
        "auth_telnet_login_pattern",
        "auth_password_pattern",
        "auth_passphrase_pattern",
    ),
)
def test_channel_auth_properties(test_data, base_channel):
    """
    Asserts that channel auth properties properly encode and compile their set values
    """
    property_name, default_value = test_data

    compiled_value = re.compile(default_value.encode(), flags=re.I | re.M)
    assert getattr(base_channel, property_name) == compiled_value

    new_value = "somepattern"
    setattr(base_channel, property_name, new_value)

    compiled_new_value = re.compile(new_value.encode(), flags=re.I | re.M)
    assert getattr(base_channel, property_name) == compiled_new_value


def test_channel_log_append(fs, base_transport_no_abc):
    fs.create_file(
        "scrapli_channel.log",
        contents="APPEND TO ME PLEASE!",
    )
    base_channel_args = BaseChannelArgs(channel_log=True, channel_log_mode="append")
    chan = BaseChannel(transport=base_transport_no_abc, base_channel_args=base_channel_args)
    chan.open()
    chan.channel_log.write(b"\nDOIN IT!")
    chan.close()

    channel_log_contents = open("scrapli_channel.log", "rb")
    assert channel_log_contents.read() == b"APPEND TO ME PLEASE!\nDOIN IT!"


def test_channel_log_invalid_mode(base_transport_no_abc):
    with pytest.raises(ScrapliValueError):
        BaseChannelArgs(channel_log=True, channel_log_mode="not valid")


def test_channel_log(fs, base_transport_no_abc):
    # fs needed to mock filesystem for asserting log location
    _ = fs
    base_channel_args = BaseChannelArgs(channel_log=True)
    chan = BaseChannel(transport=base_transport_no_abc, base_channel_args=base_channel_args)
    chan.open()
    assert Path("/scrapli_channel.log").is_file()


def test_channel_log_user_defined(fs, base_transport_no_abc):
    # fs needed to mock filesystem for asserting log location
    _ = fs
    base_channel_args = BaseChannelArgs(channel_log="/log.log")
    chan = BaseChannel(transport=base_transport_no_abc, base_channel_args=base_channel_args)
    chan.open()
    assert Path("/log.log").is_file()


def test_channel_log_user_bytesio(base_transport_no_abc):
    bytes_log = BytesIO()
    base_channel_args = BaseChannelArgs(channel_log=bytes_log)
    chan = BaseChannel(transport=base_transport_no_abc, base_channel_args=base_channel_args)
    chan.open()
    assert chan.channel_log is bytes_log


@pytest.mark.parametrize(
    "test_data",
    (
        (
            b"blah basic stuff>",
            b"blah basic stuff>",
        ),
        (
            b"\noper-status></physical-interface>\nsomeprompt>",
            b"oper-status></physical-interface>\nsomeprompt>",
        ),
    ),
    ids=("simple_buf", "xml_out"),
)
def test_process_read_buf(test_data, base_channel):
    """
    This asserts that the process read buf method always returns a search buf that is "roooted"
    on newlines -- meaning we never scan backwards through the readbuf and return a line that gets
    split up resulting in a section of the line being at the "start" of the search_buf that looks
    exactly like a normal prompt we would match on
    """
    inbuf, expected_buf = test_data

    read_buf = BytesIO(inbuf)
    search_buf = base_channel._process_read_buf(read_buf=read_buf)

    assert search_buf == expected_buf


def test_channel_write(caplog, monkeypatch, base_channel):
    caplog.set_level(logging.DEBUG, logger="scrapli.channel")

    transport_write_called = False

    def _write(cls, channel_input, redacted: bool = False):
        nonlocal transport_write_called
        transport_write_called = True

    monkeypatch.setattr("scrapli.transport.base.base_transport.BaseTransport.write", _write)

    base_channel.write(channel_input="blah")

    assert transport_write_called is True

    log_record = next(iter(caplog.records))
    assert "write: 'blah'" == log_record.msg
    assert logging.DEBUG == log_record.levelno


def test_channel_write_redacted(caplog, monkeypatch, base_channel):
    caplog.set_level(logging.DEBUG, logger="scrapli.channel")
    transport_write_called = False

    def _write(cls, channel_input, redacted: bool = False):
        nonlocal transport_write_called
        transport_write_called = True

    monkeypatch.setattr("scrapli.transport.base.base_transport.BaseTransport.write", _write)

    base_channel.write(channel_input="blah", redacted=True)

    assert transport_write_called is True

    log_record = next(iter(caplog.records))
    assert "write: REDACTED" == log_record.msg
    assert logging.DEBUG == log_record.levelno


def test_channel_send_return(monkeypatch, base_channel):
    base_channel._base_channel_args.comms_return_char = "RETURNCHAR"

    def _write(cls, channel_input, redacted: bool = False):
        assert channel_input == b"RETURNCHAR"

    monkeypatch.setattr("scrapli.transport.base.base_transport.BaseTransport.write", _write)

    base_channel.send_return()


@pytest.mark.parametrize(
    "test_data",
    (
        (
            b"Host key verification failed",
            "Host key verification failed",
        ),
        (
            b"Operation timed out",
            "Timed out connecting",
        ),
        (
            b"Connection timed out",
            "Timed out connecting",
        ),
        (
            b"No route to host",
            "No route to host",
        ),
        (
            b"no matching key exchange found.",
            "No matching key exchange found",
        ),
        (
            b"no matching key exchange found. Their offer: diffie-hellman-group-exchange-sha1,diffie-hellman-group14-sha1",
            "No matching key exchange found for host, their offer: diffie-hellman-group-exchange-sha1,diffie-hellman-group14-sha1",
        ),
        (
            b"no matching cipher found",
            "No matching cipher found",
        ),
        (
            b"no matching cipher found, their offer: aes128-cbc,aes256-cbc",
            "No matching cipher found for host, their offer: aes128-cbc,aes256-cbc",
        ),
        (
            b"command-line: line 0: Bad configuration option: ciphers+",
            "Bad SSH configuration option(s) for host",
        ),
        (
            b"WARNING: UNPROTECTED PRIVATE KEY FILE!",
            # note: empty quotes in the middle is where private key filename would be
            "Permissions for private key are too open, authentication failed!",
        ),
        (
            b"Could not resolve hostname BLAH: No address associated with hostname",
            # note: empty quotes in the middle is where private key filename would be
            "Could not resolve address for host",
        ),
        (
            b"Can't open user config file /etc/ssh/ssh_config: Permission denied",
            "Can't open user config file /etc/ssh/ssh_config: Permission denied",
        ),
    ),
    ids=(
        "host key verification",
        "operation time out",
        "connection time out",
        "no route to host",
        "no matching key exchange",
        "no matching key exchange found key exchange",
        "no matching cipher",
        "no matching cipher found ciphers",
        "bad configuration option",
        "unprotected key",
        "could not resolve host",
        "bad permissions",
    ),
)
def test_ssh_message_handler(base_channel, test_data):
    error_message, expected_message = test_data
    with pytest.raises(ScrapliAuthenticationFailed) as exc:
        base_channel._ssh_message_handler(error_message)
    assert expected_message in str(exc.value)


def test_get_prompt_pattern_no_pattern_provided(base_channel):
    actual_pattern = base_channel._get_prompt_pattern(class_pattern="class_pattern_blah")
    assert actual_pattern == re.compile(b"class_pattern_blah", flags=re.M | re.I)


def test_get_prompt_pattern_provided_multiline(base_channel):
    actual_pattern = base_channel._get_prompt_pattern(
        class_pattern="", pattern="^provided_pattern$"
    )
    assert actual_pattern == re.compile(b"^provided_pattern$", flags=re.M | re.I)


def test_get_prompt_pattern_provided_no_multiline(base_channel):
    actual_pattern = base_channel._get_prompt_pattern(class_pattern="", pattern="some_pattern")
    assert actual_pattern == re.compile(b"some_pattern")


def test_process_output(base_channel):
    base_channel._base_channel_args.comms_prompt_pattern = "^scrapli>$"
    actual_processed_buf = base_channel._process_output(
        buf=b"linewithtrailingspace   \nsomethingelse\nscrapli>", strip_prompt=True
    )
    assert actual_processed_buf == b"linewithtrailingspace\nsomethingelse"


def test_strip_ansi(base_channel):
    actual_strip_ansi_output = base_channel._strip_ansi(
        buf=b"[admin@CoolDevice.Sea1: \x1b[1m/\x1b[0;0m]$"
    )
    assert actual_strip_ansi_output == b"[admin@CoolDevice.Sea1: /]$"


def test_pre_send_input_exception(base_channel):
    with pytest.raises(ScrapliTypeError):
        base_channel._pre_send_input(channel_input=None)


def test_pre_send_inputs_interact_exception(base_channel):
    with pytest.raises(ScrapliTypeError):
        base_channel._pre_send_inputs_interact(interact_events=None)
