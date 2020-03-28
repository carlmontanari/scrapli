try:
    import ntc_templates
    import textfsm

    textfsm_avail = True
except ImportError:
    textfsm_avail = False


def test_send_command(mocked_generic_driver):
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
    conn = mocked_generic_driver(test_operations)
    output = conn.send_command(channel_input_1, strip_prompt=False)
    assert output.result == channel_output_1


def test_send_commands(mocked_generic_driver):
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
    channel_input_2 = "show ip access-lists"
    channel_output_2 = """Extended IP access list ext_acl_fw
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
    test_operations = [
        (channel_input_1, channel_output_1),
        (channel_input_2, channel_output_2),
    ]
    conn = mocked_generic_driver(test_operations)
    outputs = conn.send_commands([channel_input_1, channel_input_2], strip_prompt=False)
    assert outputs[0].result == channel_output_1
    assert outputs[1].result == channel_output_2


def test_send_inputs_interact(mocked_generic_driver):
    channel_input_1 = "clear logg"
    channel_output_1 = "Clear logging buffer [confirm]"
    channel_input_2 = "\n"
    channel_output_2 = "3560CX#"
    interact = [channel_input_1, channel_output_1, "", channel_output_2]
    test_operations = [
        (channel_input_1, channel_output_1),
        (channel_input_2, channel_output_2),
    ]
    conn = mocked_generic_driver(test_operations)
    output = conn.send_interactive(interact, hidden_response=False)
    assert output.result == "Clear logging buffer [confirm]\n\n3560CX#"
