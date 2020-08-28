import pytest

from scrapli.transport import AsyncTransport

from ...test_data.unit_test_cases import TEST_CASES


def test_init(async_cisco_iosxe_conn):
    """Test that all arguments get properly passed from driver/transport to channel on init"""
    assert isinstance(async_cisco_iosxe_conn.channel.transport, AsyncTransport)
    assert (
        async_cisco_iosxe_conn.channel.comms_prompt_pattern
        == async_cisco_iosxe_conn._initialization_args["comms_prompt_pattern"]
    )
    assert (
        async_cisco_iosxe_conn.channel.comms_return_char
        == async_cisco_iosxe_conn._initialization_args["comms_return_char"]
    )
    assert (
        async_cisco_iosxe_conn.channel.comms_ansi
        == async_cisco_iosxe_conn._initialization_args["comms_ansi"]
    )
    # auto expand is not set in initialization args at this point (may 2020)
    assert (
        async_cisco_iosxe_conn.channel.comms_auto_expand
        == async_cisco_iosxe_conn._initialization_args.get("comms_auto_expand", False)
    )
    assert (
        async_cisco_iosxe_conn.channel.timeout_ops
        == async_cisco_iosxe_conn._initialization_args["timeout_ops"]
    )


@pytest.mark.asyncio
async def test_read_chunk(async_cisco_iosxe_conn):
    await async_cisco_iosxe_conn.open()
    chunk = "this is some input for read chunk to read"
    async_cisco_iosxe_conn.transport.write(chunk)
    async_cisco_iosxe_conn.transport.write(async_cisco_iosxe_conn.channel.comms_return_char)
    # keep reading chunks until we have all the input data
    read_chunk = b""
    while chunk.encode() not in read_chunk:
        read_chunk += await async_cisco_iosxe_conn.channel._read_chunk()


@pytest.mark.asyncio
async def test_read_until_input(async_cisco_iosxe_conn):
    await async_cisco_iosxe_conn.open()
    chunk = "this is some input for read chunk to read"
    async_cisco_iosxe_conn.transport.write(chunk)
    async_cisco_iosxe_conn.transport.write(async_cisco_iosxe_conn.channel.comms_return_char)
    read_chunk = await async_cisco_iosxe_conn.channel._read_until_input(
        channel_input=chunk.encode()
    )
    assert chunk.encode() in read_chunk


@pytest.mark.asyncio
async def test_read_until_prompt(async_cisco_iosxe_conn):
    expected_prompt = TEST_CASES["cisco_iosxe"]["test_read_until_prompt"]["expected_prompt"]

    await async_cisco_iosxe_conn.open()
    chunk = "this is some input for read chunk to read"
    async_cisco_iosxe_conn.transport.write(chunk)
    async_cisco_iosxe_conn.transport.write(async_cisco_iosxe_conn.channel.comms_return_char)
    read_chunk = await async_cisco_iosxe_conn.channel._read_until_input(
        channel_input=chunk.encode()
    )
    found_prompt = await async_cisco_iosxe_conn.get_prompt()
    assert chunk.encode() in read_chunk
    assert found_prompt == expected_prompt


@pytest.mark.asyncio
async def test_read_until_prompt_or_time(async_cisco_iosxe_conn):
    await async_cisco_iosxe_conn.open()
    chunk = "this is some input for read chunk to read"
    async_cisco_iosxe_conn.transport.write(chunk)
    async_cisco_iosxe_conn.transport.write(async_cisco_iosxe_conn.channel.comms_return_char)
    read_chunk = await async_cisco_iosxe_conn.channel._read_until_prompt_or_time(
        channel_outputs=[b"chunk to read"]
    )
    assert chunk.encode() in read_chunk


@pytest.mark.asyncio
async def test_get_prompt(async_cisco_iosxe_conn):
    expected_prompt = TEST_CASES["cisco_iosxe"]["test_get_prompt"]["privilege_exec"]
    await async_cisco_iosxe_conn.open()
    found_prompt = await async_cisco_iosxe_conn.get_prompt()
    assert found_prompt == expected_prompt


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "strip_prompt",
    [True, False],
    ids=["strip_prompt", "no_strip_prompt"],
)
async def test_send_input(async_cisco_iosxe_conn, strip_prompt):
    expected_raw = TEST_CASES["cisco_iosxe"]["test_send_input"]["raw_result"]
    expected_processed = (
        TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["strip"]
        if strip_prompt
        else TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["no_strip"]
    )
    await async_cisco_iosxe_conn.open()
    raw_result, processed_result = await async_cisco_iosxe_conn.channel.send_input(
        channel_input="show version", strip_prompt=strip_prompt
    )
    assert raw_result == expected_raw.encode()
    assert processed_result == expected_processed.encode()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "strip_prompt",
    [True, False],
    ids=["strip_prompt", "no_strip_prompt"],
)
async def test_send_input_and_read(async_cisco_iosxe_conn, strip_prompt):
    expected_raw = TEST_CASES["cisco_iosxe"]["test_send_input"]["raw_result"]
    expected_processed = (
        TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["strip"]
        if strip_prompt
        else TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["no_strip"]
    )
    await async_cisco_iosxe_conn.open()
    raw_result, processed_result = await async_cisco_iosxe_conn.channel.send_input_and_read(
        channel_input="show version", strip_prompt=strip_prompt
    )
    assert raw_result == expected_raw.encode()
    assert processed_result == expected_processed.encode()


@pytest.mark.asyncio
async def test_send_inputs_interact(async_cisco_iosxe_conn):
    expected_raw = TEST_CASES["cisco_iosxe"]["test_send_inputs_interact"]["raw_result"]
    expected_processed = TEST_CASES["cisco_iosxe"]["test_send_inputs_interact"]["processed_result"]
    interact_events = TEST_CASES["cisco_iosxe"]["test_send_inputs_interact"]["interact_events"]
    await async_cisco_iosxe_conn.open()
    raw_result, processed_result = await async_cisco_iosxe_conn.channel.send_inputs_interact(
        interact_events=interact_events
    )
    assert raw_result == expected_raw.encode()
    assert processed_result == expected_processed.encode()
