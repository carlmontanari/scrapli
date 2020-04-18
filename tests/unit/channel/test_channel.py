import pytest


def test__str(mocked_channel):
    conn = mocked_channel([])
    assert str(conn.channel) == "scrapli Channel Object"


def test__repr(mocked_channel):
    conn = mocked_channel([])
    assert (
        repr(conn.channel)
        == r"scrapli Channel {'comms_prompt_pattern': '^[a-z0-9.\\-@()/:]{1,48}[#>$]\\s*$', 'comms_return_char': '\n', "
        r"'comms_ansi': False, 'comms_auto_expand': False, 'timeout_ops': 30}"
    )


@pytest.mark.parametrize(
    "attr_setup",
    [
        (
            "send_input",
            {"channel_input": ["stuff", "more stuff"]},
            TypeError,
            "`send_input` expects a single string, got <class 'list'>. to send a list of inputs use the `send_inputs` method instead",
        ),
        (
            "send_inputs_interact",
            {"interact_events": "stuff"},
            TypeError,
            "`interact_events` expects a List, got <class 'str'>",
        ),
    ],
    ids=["send_input", "send_inputs_interact"],
)
def test_exceptions_raised(attr_setup, mocked_channel):
    method_name = attr_setup[0]
    methd_args = attr_setup[1]
    method_exc = attr_setup[2]
    method_msg = attr_setup[3]
    with pytest.raises(method_exc) as exc:
        conn = mocked_channel([])
        method = getattr(conn.channel, method_name)
        method(**methd_args)
    assert str(exc.value) == method_msg


@pytest.mark.parametrize(
    "attr_setup",
    [
        ({"strip_prompt": True}, b"hostname 3560CX\n"),
        ({"strip_prompt": False}, b"hostname 3560CX\n3560CX#"),
    ],
    ids=["strip_prompt_true", "strip_prompt_false",],
)
def test__restructure_output(attr_setup, mocked_channel):
    args = attr_setup[0]
    expected = attr_setup[1]
    channel_output = b"hostname 3560CX\r\n3560CX#"
    conn = mocked_channel([])
    output = conn.channel._restructure_output(channel_output, **args)
    assert output == expected


@pytest.mark.parametrize(
    "attr_setup",
    [
        ({"comms_ansi": False}, b"3560CX#", b"3560CX#"),
        ({"comms_ansi": True}, b"\x1b[0;0m3560CX#\x1b[0;0m", b"3560CX#"),
    ],
    ids=["read_chunk", "read_chunk_strip_ansi",],
)
def test__read_chunk(attr_setup, mocked_channel):
    args = attr_setup[0]
    initial_bytes = attr_setup[1]
    expected = attr_setup[2]
    conn = mocked_channel([], initial_bytes=initial_bytes, **args)
    output = conn.channel._read_chunk()
    assert output == expected


@pytest.mark.parametrize(
    "attr_setup",
    [
        ({"comms_ansi": False}, b"3560CX#", b"3560CX#"),
        ({"comms_ansi": True}, b"\x1b[0;0m3560CX#\x1b[0;0m", b"3560CX#"),
    ],
    ids=["read_chunk", "read_chunk_strip_ansi"],
)
def test__read_until_input(attr_setup, mocked_channel):
    args = attr_setup[0]
    initial_bytes = attr_setup[1]
    expected = attr_setup[2]
    conn = mocked_channel([], initial_bytes=initial_bytes, **args)
    output = conn.channel._read_until_input(expected)
    assert output == expected


def test__read_until_input_auto_expand(mocked_channel):
    initial_bytes = b"show version"
    expected = b"show version"
    conn = mocked_channel([], initial_bytes=initial_bytes)
    output = conn.channel._read_until_input(b"sho ver", auto_expand=True)
    assert output == expected


@pytest.mark.parametrize(
    "attr_setup",
    [
        ({}, b"hostname 3560CX\r\n3560CX#"),
        ({"comms_prompt_pattern": "^3560CX#$"}, b"hostname 3560CX\r\n3560CX#"),
        ({"comms_prompt_pattern": "3560CX#"}, b"hostname 3560CX\r\n3560CX#"),
    ],
    ids=[
        "default_comms_prompt_pattern",
        "regex_comms_prompt_pattern",
        "string_comms_prompt_pattern",
    ],
)
def test__read_until_prompt(attr_setup, mocked_channel):
    args = attr_setup[0]
    expected = attr_setup[1]
    channel_output = b"hostname 3560CX\r\n"
    conn = mocked_channel([], **args)
    output = conn.channel._read_until_prompt(channel_output)
    assert output == expected


@pytest.mark.parametrize(
    "attr_setup",
    [
        ({}, "3560CX#"),
        ({"comms_prompt_pattern": "^3560CX#$"}, "3560CX#"),
        ({"comms_prompt_pattern": "3560CX#"}, "3560CX#"),
    ],
    ids=[
        "default_comms_prompt_pattern",
        "regex_comms_prompt_pattern",
        "string_comms_prompt_pattern",
    ],
)
def test_get_prompt(attr_setup, mocked_channel):
    args = attr_setup[0]
    expected = attr_setup[1]
    conn = mocked_channel([("\n", "\n3560CX#")], **args)
    output = conn.channel.get_prompt()
    assert output == expected


@pytest.mark.parametrize(
    "attr_setup",
    [
        (
            {},
            "show ip access-lists",
            """Extended IP access list ext_acl_fw
    10 deny ip 0.0.0.0 0.255.255.255 any
    20 deny ip 10.0.0.0 0.255.255.255 any
    30 deny ip 100.64.0.0 0.63.255.255 any (2 matches)
    40 deny ip 127.0.0.0 0.255.255.255 any
    50 deny ip 169.254.0.0 0.0.255.255 any
    60 deny ip 172.16.0.0 0.15.255.255 any
    70 deny ip 192.0.0.0 0.0.0.255 any
    80 deny ip 192.0.2.0 0.0.0.255 any
    90 deny ip 192.168.0.0 0.0.255.255 any
    100 deny ip 198.18.0.0 0.1.255.255 any
    110 deny ip 198.51.100.0 0.0.0.255 any
    120 deny ip 203.0.113.0 0.0.0.255 any
    130 deny ip 224.0.0.0 15.255.255.255 any
    140 deny ip 240.0.0.0 15.255.255.255 any
3560CX#""",
            """Extended IP access list ext_acl_fw
    10 deny ip 0.0.0.0 0.255.255.255 any
    20 deny ip 10.0.0.0 0.255.255.255 any
    30 deny ip 100.64.0.0 0.63.255.255 any (2 matches)
    40 deny ip 127.0.0.0 0.255.255.255 any
    50 deny ip 169.254.0.0 0.0.255.255 any
    60 deny ip 172.16.0.0 0.15.255.255 any
    70 deny ip 192.0.0.0 0.0.0.255 any
    80 deny ip 192.0.2.0 0.0.0.255 any
    90 deny ip 192.168.0.0 0.0.255.255 any
    100 deny ip 198.18.0.0 0.1.255.255 any
    110 deny ip 198.51.100.0 0.0.0.255 any
    120 deny ip 203.0.113.0 0.0.0.255 any
    130 deny ip 224.0.0.0 15.255.255.255 any
    140 deny ip 240.0.0.0 15.255.255.255 any""",
        ),
        (
            {"strip_prompt": False},
            "show ip access-lists",
            """Extended IP access list ext_acl_fw
    10 deny ip 0.0.0.0 0.255.255.255 any
    20 deny ip 10.0.0.0 0.255.255.255 any
    30 deny ip 100.64.0.0 0.63.255.255 any (2 matches)
    40 deny ip 127.0.0.0 0.255.255.255 any
    50 deny ip 169.254.0.0 0.0.255.255 any
    60 deny ip 172.16.0.0 0.15.255.255 any
    70 deny ip 192.0.0.0 0.0.0.255 any
    80 deny ip 192.0.2.0 0.0.0.255 any
    90 deny ip 192.168.0.0 0.0.255.255 any
    100 deny ip 198.18.0.0 0.1.255.255 any
    110 deny ip 198.51.100.0 0.0.0.255 any
    120 deny ip 203.0.113.0 0.0.0.255 any
    130 deny ip 224.0.0.0 15.255.255.255 any
    140 deny ip 240.0.0.0 15.255.255.255 any
3560CX#""",
            """Extended IP access list ext_acl_fw
    10 deny ip 0.0.0.0 0.255.255.255 any
    20 deny ip 10.0.0.0 0.255.255.255 any
    30 deny ip 100.64.0.0 0.63.255.255 any (2 matches)
    40 deny ip 127.0.0.0 0.255.255.255 any
    50 deny ip 169.254.0.0 0.0.255.255 any
    60 deny ip 172.16.0.0 0.15.255.255 any
    70 deny ip 192.0.0.0 0.0.0.255 any
    80 deny ip 192.0.2.0 0.0.0.255 any
    90 deny ip 192.168.0.0 0.0.255.255 any
    100 deny ip 198.18.0.0 0.1.255.255 any
    110 deny ip 198.51.100.0 0.0.0.255 any
    120 deny ip 203.0.113.0 0.0.0.255 any
    130 deny ip 224.0.0.0 15.255.255.255 any
    140 deny ip 240.0.0.0 15.255.255.255 any
3560CX#""",
        ),
    ],
    ids=["strip_prompt_true", "strip_prompt_false",],
)
def test_send_input(attr_setup, mocked_channel):
    args = attr_setup[0]
    channel_input = attr_setup[1]
    channel_output = attr_setup[2]
    expected = attr_setup[3]
    conn = mocked_channel([(channel_input, channel_output)])
    raw_output, processed_output = conn.channel.send_input(channel_input, **args)
    assert processed_output == expected


@pytest.mark.parametrize(
    "attr_setup",
    [
        (
            [("clear logg", "Clear logging buffer [confirm]"), ("", "3560CX#", False)],
            "clear logg\nClear logging buffer [confirm]\n3560CX#",
        ),
        (
            [("clear logg", "Clear logging buffer [confirm]"), ("", "3560CX#", True)],
            "clear logg\nClear logging buffer [confirm]\n3560CX#",
        ),
    ],
    ids=["basic", "hidden_response"],
)
def test_send_inputs_interact(attr_setup, mocked_channel):
    interact_events = attr_setup[0]
    expected = attr_setup[1]
    test_operations = [
        [interact_events[0][0], interact_events[0][1]],
        [interact_events[1][0], interact_events[1][1]],
    ]
    if interact_events[1][2] is True:
        test_operations[1][0] = ""
    conn = mocked_channel(test_operations)
    output, _ = conn.channel.send_inputs_interact(interact_events=interact_events)
    assert output == expected
