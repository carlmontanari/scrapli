import pytest


def test__str(mocked_channel):
    conn = mocked_channel([])
    assert str(conn.channel) == "scrapli Channel Object"


def test__repr(mocked_channel):
    conn = mocked_channel([])
    assert (
        repr(conn.channel)
        == r"scrapli Channel {'comms_prompt_pattern': '^[a-z0-9.\\-@()/:]{1,32}[#>$]$', 'comms_return_char': '\n', 'comms_ansi': False, 'timeout_ops': 10}"
    )


def test__restructure_output_strip_prompt(mocked_channel):
    channel_output_1 = b"hostname 3560CX\r\n3560CX#"
    conn = mocked_channel([])
    output = conn.channel._restructure_output(channel_output_1, strip_prompt=False)
    assert output == b"hostname 3560CX\n3560CX#"


def test__restructure_output_strip_prompt(mocked_channel):
    channel_output_1 = b"hostname 3560CX\r\n3560CX#"
    conn = mocked_channel([])
    output = conn.channel._restructure_output(channel_output_1, strip_prompt=True)
    assert output == b"hostname 3560CX\n"


def test__read_until_prompt_default_pattern(mocked_channel):
    channel_output_1 = b"!\r\nntp server 172.31.255.1 prefer\r\n!\r\nend\r\n\r\n"
    conn = mocked_channel([])
    output = conn.channel._read_until_prompt(channel_output_1)
    assert output == b"!\nntp server 172.31.255.1 prefer\n!\nend\n\n3560CX#"


def test__read_until_prompt_regex_pattern(mocked_channel):
    channel_output_1 = b"!\r\nntp server 172.31.255.1 prefer\r\n!\r\nend\r\n\r\n"
    conn = mocked_channel([], comms_prompt_pattern="^3560CX#$")
    output = conn.channel._read_until_prompt(channel_output_1)
    assert output == b"!\nntp server 172.31.255.1 prefer\n!\nend\n\n3560CX#"


def test__read_until_prompt_string_pattern(mocked_channel):
    channel_output_1 = b"!\r\nntp server 172.31.255.1 prefer\r\n!\r\nend\r\n\r\n"
    conn = mocked_channel([], comms_prompt_pattern="3560CX#")
    output = conn.channel._read_until_prompt(channel_output_1)
    assert output == b"!\nntp server 172.31.255.1 prefer\n!\nend\n\n3560CX#"


#  TODO i may not be stripping ansi from get prompt which could break shit w/ ansi in the prompt
def test__strip_ansi(mocked_channel):
    initial_bytes = b"\x1b[0;0m3560CX#\x1b[0;0m"
    conn = mocked_channel([], comms_ansi=True, initial_bytes=initial_bytes)
    output = conn.channel._read_chunk()
    assert output == b"3560CX#"


def test_get_prompt(mocked_channel):
    channel_input_1 = "\n"
    channel_output_1 = "\n3560CX#"
    test_operations = [(channel_input_1, channel_output_1)]
    conn = mocked_channel(test_operations)
    output = conn.channel.get_prompt()
    assert output == "3560CX#"


def test__send_input(mocked_channel):
    channel_input_1 = "show ip access-lists"
    channel_output_1 = """Extended IP access list ext_acl_fw
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
3560CX#"""
    test_operations = [(channel_input_1, channel_output_1)]
    conn = mocked_channel(test_operations)
    output, processed_output = conn.channel._send_input(channel_input_1, strip_prompt=False)
    assert output.lstrip() == channel_output_1.encode()
    assert processed_output.lstrip().decode() == channel_output_1


def test_send_inputs(mocked_channel):
    channel_input_1 = "show ip access-lists"
    channel_output_1 = """Extended IP access list ext_acl_fw
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
3560CX#"""
    test_operations = [(channel_input_1, channel_output_1)]
    conn = mocked_channel(test_operations)
    output = conn.channel.send_inputs(channel_input_1, strip_prompt=False)
    assert output[0].result == channel_output_1


def test_send_inputs_multiple(mocked_channel):
    channel_input_1 = "show ip access-lists"
    channel_output_1 = """Extended IP access list ext_acl_fw
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
3560CX#"""
    channel_input_2 = "show ip prefix-list"
    channel_output_2 = """ip prefix-list pl_default: 1 entries
   seq 5 permit 0.0.0.0/0 le 32
3560CX#"""
    test_operations = [(channel_input_1, channel_output_1), (channel_input_2, channel_output_2)]
    conn = mocked_channel(test_operations)
    output = conn.channel.send_inputs((channel_input_1, channel_input_2), strip_prompt=False)
    assert output[0].result == channel_output_1
    assert output[1].result == channel_output_2


def test_send_inputs_interact(mocked_channel):
    interact = ("clear logg", "Clear logging buffer [confirm]", "", "3560CX#")
    test_operations = [(interact[0], interact[1]), (interact[2], interact[3])]
    conn = mocked_channel(test_operations)
    output = conn.channel.send_inputs_interact(interact, hidden_response=False)
    assert output[0].result == "Clear logging buffer [confirm]\n\n3560CX#"


def test_send_inputs_interact_invalid_input(mocked_channel):
    interact = "not a list or tuple"
    conn = mocked_channel([])
    with pytest.raises(TypeError) as exc:
        conn.channel.send_inputs_interact(interact, hidden_response=False)
    assert str(exc.value) == "send_inputs_interact expects a List or Tuple, got <class 'str'>"


def test__send_return(mocked_channel):
    channel_input_1 = "\n"
    channel_output_1 = "\n3560CX#"
    test_operations = [(channel_input_1, channel_output_1)]
    conn = mocked_channel(test_operations)
    output = conn.channel.get_prompt()
    assert output == "3560CX#"
