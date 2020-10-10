import pytest

from ...test_data.unit_test_cases import TEST_CASES


def test__str(sync_cisco_iosxe_conn):
    assert str(sync_cisco_iosxe_conn.channel) == "scrapli Channel Object"


def test__repr(sync_cisco_iosxe_conn):
    assert (
        repr(sync_cisco_iosxe_conn.channel)
        == "scrapli Channel {'logger': 'scrapli.channel-localhost', 'comms_prompt_pattern': '(^[a-z0-9.\\\\-_@()/:]{1,"
        "63}>$)|(^[a-z0-9.\\\\-_@/:]{1,63}#$)|(^[a-z0-9.\\\\-_@/:]{1,63}\\\\([a-z0-9.\\\\-@/:\\\\+]{0,32}\\\\)#$)', "
        "'comms_return_char': '\\n', 'comms_ansi': True, 'comms_auto_expand': False, 'timeout_ops': 30.0, 'session_lock': False}"
    )


@pytest.mark.parametrize(
    "attr_setup",
    [
        ({"strip_prompt": True}, b"hostname 3560CX"),
        ({"strip_prompt": False}, b"hostname 3560CX\n3560CX#"),
    ],
    ids=[
        "strip_prompt_true",
        "strip_prompt_false",
    ],
)
def test__restructure_output(sync_cisco_iosxe_conn, attr_setup):
    args = attr_setup[0]
    expected = attr_setup[1]
    channel_output = b"hostname 3560CX\r\n3560CX#"
    output = sync_cisco_iosxe_conn.channel._restructure_output(channel_output, **args)
    assert output == expected


def test_pre_send_input(sync_cisco_iosxe_conn):
    with pytest.raises(TypeError) as exc:
        sync_cisco_iosxe_conn.channel._pre_send_input(channel_input=[])
    assert str(exc.value) == "`send_input` expects a single string, got <class 'list'>."


def test_pre_send_inputs_interact(sync_cisco_iosxe_conn):
    with pytest.raises(TypeError) as exc:
        sync_cisco_iosxe_conn.channel._pre_send_inputs_interact(interact_events="blah")
    assert str(exc.value) == "`interact_events` expects a List, got <class 'str'>"


def test_post_send_inputs_interact(sync_cisco_iosxe_conn):
    expected_raw = TEST_CASES["cisco_iosxe"]["test_send_input"]["raw_result"]
    expected_processed = TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"][
        "no_strip"
    ]
    raw_result, processed_result = sync_cisco_iosxe_conn.channel._post_send_inputs_interact(
        output=expected_raw.encode()
    )
    assert raw_result == expected_raw.encode()
    assert processed_result == expected_processed.encode()


@pytest.mark.parametrize(
    "attr_setup",
    [(True, "show version", "sho ver"), (False, "show vkasjflkdsjafl", "sho ver")],
    ids=["not expanded", "expanded"],
)
def test_process_auto_expand(sync_cisco_iosxe_conn, attr_setup):
    expanded = attr_setup[0]
    output = attr_setup[1]
    channel_input = attr_setup[2]
    result = sync_cisco_iosxe_conn.channel._process_auto_expand(
        output=output, channel_input=channel_input
    )
    assert expanded == result
