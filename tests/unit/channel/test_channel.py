import pytest

from scrapli.transport import Transport

from ...test_data.unit_test_cases import TEST_CASES


def test_init(sync_cisco_iosxe_conn):
    """Test that all arguments get properly passed from driver/transport to channel on init"""
    assert isinstance(sync_cisco_iosxe_conn.channel.transport, Transport)
    assert (
        sync_cisco_iosxe_conn.channel.comms_prompt_pattern
        == sync_cisco_iosxe_conn._initialization_args["comms_prompt_pattern"]
    )
    assert (
        sync_cisco_iosxe_conn.channel.comms_return_char
        == sync_cisco_iosxe_conn._initialization_args["comms_return_char"]
    )
    assert (
        sync_cisco_iosxe_conn.channel.comms_ansi
        == sync_cisco_iosxe_conn._initialization_args["comms_ansi"]
    )
    # auto expand is not set in initialization args at this point (may 2020)
    assert (
        sync_cisco_iosxe_conn.channel.comms_auto_expand
        == sync_cisco_iosxe_conn._initialization_args.get("comms_auto_expand", False)
    )
    assert (
        sync_cisco_iosxe_conn.channel.timeout_ops
        == sync_cisco_iosxe_conn._initialization_args["timeout_ops"]
    )


def test_read_chunk(sync_cisco_iosxe_conn):
    sync_cisco_iosxe_conn.open()
    chunk = "this is some input for read chunk to read"
    sync_cisco_iosxe_conn.transport.write(chunk)
    sync_cisco_iosxe_conn.transport.write(sync_cisco_iosxe_conn.channel.comms_return_char)
    # keep reading chunks until we have all the input data
    read_chunk = b""
    while chunk.encode() not in read_chunk:
        read_chunk += sync_cisco_iosxe_conn.channel._read_chunk()


def test_read_until_input(sync_cisco_iosxe_conn):
    sync_cisco_iosxe_conn.open()
    chunk = "this is some input for read chunk to read"
    sync_cisco_iosxe_conn.transport.write(chunk)
    sync_cisco_iosxe_conn.transport.write(sync_cisco_iosxe_conn.channel.comms_return_char)
    read_chunk = sync_cisco_iosxe_conn.channel._read_until_input(channel_input=chunk.encode())
    assert chunk.encode() in read_chunk


def test_read_until_prompt(sync_cisco_iosxe_conn):
    expected_prompt = TEST_CASES["cisco_iosxe"]["test_read_until_prompt"]["expected_prompt"]

    sync_cisco_iosxe_conn.open()
    chunk = "this is some input for read chunk to read"
    sync_cisco_iosxe_conn.transport.write(chunk)
    sync_cisco_iosxe_conn.transport.write(sync_cisco_iosxe_conn.channel.comms_return_char)
    read_chunk = sync_cisco_iosxe_conn.channel._read_until_input(channel_input=chunk.encode())
    found_prompt = sync_cisco_iosxe_conn.get_prompt()
    assert chunk.encode() in read_chunk
    assert found_prompt == expected_prompt


def test_read_until_prompt_or_time(sync_cisco_iosxe_conn):
    sync_cisco_iosxe_conn.open()
    chunk = "this is some input for read chunk to read"
    sync_cisco_iosxe_conn.transport.write(chunk)
    sync_cisco_iosxe_conn.transport.write(sync_cisco_iosxe_conn.channel.comms_return_char)
    read_chunk = sync_cisco_iosxe_conn.channel._read_until_prompt_or_time(
        channel_outputs=[b"chunk to read"]
    )
    assert chunk.encode() in read_chunk


def test_get_prompt(sync_cisco_iosxe_conn):
    expected_prompt = TEST_CASES["cisco_iosxe"]["test_get_prompt"]["privilege_exec"]
    sync_cisco_iosxe_conn.open()
    found_prompt = sync_cisco_iosxe_conn.get_prompt()
    assert found_prompt == expected_prompt


@pytest.mark.parametrize(
    "strip_prompt",
    [True, False],
    ids=["strip_prompt", "no_strip_prompt"],
)
def test_send_input(sync_cisco_iosxe_conn, strip_prompt):
    expected_raw = TEST_CASES["cisco_iosxe"]["test_send_input"]["raw_result"]
    expected_processed = (
        TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["strip"]
        if strip_prompt
        else TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["no_strip"]
    )
    sync_cisco_iosxe_conn.open()
    raw_result, processed_result = sync_cisco_iosxe_conn.channel.send_input(
        channel_input="show version", strip_prompt=strip_prompt
    )
    assert raw_result == expected_raw.encode()
    assert processed_result == expected_processed.encode()


def test_send_inputs_interact(sync_cisco_iosxe_conn):
    expected_raw = TEST_CASES["cisco_iosxe"]["test_send_inputs_interact"]["raw_result"]
    expected_processed = TEST_CASES["cisco_iosxe"]["test_send_inputs_interact"]["processed_result"]
    interact_events = TEST_CASES["cisco_iosxe"]["test_send_inputs_interact"]["interact_events"]
    sync_cisco_iosxe_conn.open()
    raw_result, processed_result = sync_cisco_iosxe_conn.channel.send_inputs_interact(
        interact_events=interact_events
    )
    assert raw_result == expected_raw.encode()
    assert processed_result == expected_processed.encode()


@pytest.mark.parametrize(
    "strip_prompt",
    [True, False],
    ids=["strip_prompt", "no_strip_prompt"],
)
def test_send_input_and_read(sync_cisco_iosxe_conn, strip_prompt):
    expected_raw = TEST_CASES["cisco_iosxe"]["test_send_input"]["raw_result"]
    expected_processed = (
        TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["strip"]
        if strip_prompt
        else TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["no_strip"]
    )
    sync_cisco_iosxe_conn.open()
    raw_result, processed_result = sync_cisco_iosxe_conn.channel.send_input_and_read(
        channel_input="show version", strip_prompt=strip_prompt
    )
    assert raw_result == expected_raw.encode()
    assert processed_result == expected_processed.encode()
