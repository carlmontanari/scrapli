import pkg_resources  # pylint: disable=C0411
import pytest

from scrapli.netmiko_compatability import connect_handler, transform_netmiko_kwargs

try:
    import ntc_templates
    import textfsm

    textfsm_avail = True
except ImportError:
    textfsm_avail = False


def test_connect_handler_invalid_device_type():
    device = {"device_type": "tacocat"}
    with pytest.raises(TypeError):
        connect_handler(**device)


def test_connect_handler_invalid_device_type_type():
    device = {"device_type": True}
    with pytest.raises(TypeError):
        connect_handler(**device)


def test_connect_handler_ip_no_hostname():
    netmiko_args = {
        "ip": "1.2.3.4",
        "username": "person",
        "password": "password",
        "port": 123,
        "global_delay_factor": 5,
        "device_type": "cisco_xe",
    }
    conn = connect_handler(auto_open=False, **netmiko_args)
    assert conn.textfsm_platform == "cisco_ios"


def test_connect_handler_valid_connection():
    netmiko_args = {
        "host": "1.2.3.4",
        "username": "person",
        "password": "password",
        "port": 123,
        "global_delay_factor": 5,
        "device_type": "cisco_xe",
    }
    conn = connect_handler(auto_open=False, **netmiko_args)
    assert conn.textfsm_platform == "cisco_ios"


def test_transform_netmiko_args():
    netmiko_args = {
        "host": "1.2.3.4",
        "username": "person",
        "password": "password",
        "port": 123,
        "global_delay_factor": 5,
    }
    transformed_args = transform_netmiko_kwargs(netmiko_args)
    assert transformed_args["host"] == "1.2.3.4"
    assert transformed_args["timeout_transport"] == 25000


def test_transform_netmiko_args_setup_timeout():
    netmiko_args = {"host": "1.2.3.4", "username": "person", "password": "password", "port": 123}
    transformed_args = transform_netmiko_kwargs(netmiko_args)
    assert transformed_args["host"] == "1.2.3.4"
    assert transformed_args["timeout_transport"] == 5000


def test_netmiko_find_prompt(mocked_netmiko_driver):
    channel_input_1 = "\n"
    channel_output_1 = "\n3560CX#"
    channel_ops = [(channel_input_1, channel_output_1)]

    conn = mocked_netmiko_driver(channel_ops)
    result = conn.find_prompt()
    assert result == "3560CX#"


def test_netmiko_send_command(mocked_netmiko_driver):
    channel_input_1 = "\n"
    channel_output_1 = "\n3560CX#"
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
    test_operations = [(channel_input_1, channel_output_1), (channel_input_2, channel_output_2)]
    conn = mocked_netmiko_driver(test_operations)
    conn.default_desired_priv = "privilege_exec"
    result = conn.send_command(channel_input_2, strip_prompt=False)
    assert result == channel_output_2


def test_netmiko_send_command_timing(mocked_netmiko_driver):
    channel_input_1 = "\n"
    channel_output_1 = "\n3560CX#"
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
    test_operations = [(channel_input_1, channel_output_1), (channel_input_2, channel_output_2)]
    conn = mocked_netmiko_driver(test_operations)
    conn.default_desired_priv = "privilege_exec"
    result = conn.send_command_timing(channel_input_2, strip_prompt=False)
    assert result == channel_output_2


def test_netmiko_send_command_strip_prompt(mocked_netmiko_driver):
    channel_input_1 = "\n"
    channel_output_1 = "\n3560CX#"
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
    test_operations = [(channel_input_1, channel_output_1), (channel_input_2, channel_output_2)]
    conn = mocked_netmiko_driver(test_operations)
    conn.default_desired_priv = "privilege_exec"
    result = conn.send_command(channel_input_2, strip_prompt=True)
    assert result == channel_output_2[:-8]


def test_netmiko_send_command_strip_prompt_not_provided(mocked_netmiko_driver):
    channel_input_1 = "\n"
    channel_output_1 = "\n3560CX#"
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
    test_operations = [(channel_input_1, channel_output_1), (channel_input_2, channel_output_2)]
    conn = mocked_netmiko_driver(test_operations)
    conn.default_desired_priv = "privilege_exec"
    result = conn.send_command(channel_input_2)
    assert result == channel_output_2[:-8]


def test_netmiko_send_command_expect_string(mocked_netmiko_driver):
    channel_input_1 = "\n"
    channel_output_1 = "\n3560CX#"
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
    test_operations = [(channel_input_1, channel_output_1), (channel_input_2, channel_output_2)]
    conn = mocked_netmiko_driver(test_operations)
    conn.default_desired_priv = "privilege_exec"
    with pytest.warns(UserWarning) as record:
        result = conn.send_command(channel_input_2, strip_prompt=False, expect_string="something")
    assert (
        record[0].message.args[0]
        == """
***** scrapli netmiko interoperability does not support expect_string! ****************
To resolve this issue, use native or driver mode with `send_inputs_interact`  method.
***** scrapli netmiko interoperability does not support expect_string! ****************"""
    )
    assert result == channel_output_2


def test_netmiko_send_command_list_of_commands(mocked_netmiko_driver):
    channel_input_1 = "\n"
    channel_output_1 = "\n3560CX#"
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
    test_operations = [(channel_input_1, channel_output_1), (channel_input_2, channel_output_2)]
    conn = mocked_netmiko_driver(test_operations)
    conn.default_desired_priv = "privilege_exec"
    with pytest.warns(UserWarning) as record:
        result = conn.send_command([channel_input_2], strip_prompt=False)
    assert (
        record[0].message.args[0]
        == """
***** netmiko does not support sending list of commands, using only the first command! 
To resolve this issue, use native or driver mode with `send_inputs` method.
***** netmiko does not support sending list of commands, using only the first command! """
    )
    assert result == channel_output_2


@pytest.mark.skipif(textfsm_avail is False, reason="textfsm and/or ntc_templates are not installed")
def test_netmiko_send_command_textfsm_success(mocked_netmiko_driver):
    channel_input_1 = "\n"
    channel_output_1 = "\n3560CX#"
    channel_input_2 = "show version"
    channel_output_2 = """Cisco IOS Software, C3560CX Software (C3560CX-UNIVERSALK9-M), Version 15.2(4)E7, RELEASE SOFTWARE (fc2)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2018 by Cisco Systems, Inc.
Compiled Tue 18-Sep-18 13:20 by prod_rel_team

ROM: Bootstrap program is C3560CX boot loader
BOOTLDR: C3560CX Boot Loader (C3560CX-HBOOT-M) Version 15.2(4r)E5, RELEASE SOFTWARE (fc4)

3560CX uptime is 2 weeks, 3 days, 18 hours, 3 minutes
System returned to ROM by power-on
System restarted at 15:59:35 PST Wed Jan 15 2020
System image file is "flash:c3560cx-universalk9-mz.152-4.E7.bin"
Last reload reason: power-on



This product contains cryptographic features and is subject to United
States and local country laws governing import, export, transfer and
use. Delivery of Cisco cryptographic products does not imply
third-party authority to import, export, distribute or use encryption.
Importers, exporters, distributors and users are responsible for
compliance with U.S. and local country laws. By using this product you
agree to comply with applicable laws and regulations. If you are unable
to comply with U.S. and local laws, return this product immediately.

A summary of U.S. laws governing Cisco cryptographic products may be found at:
http://www.cisco.com/wwl/export/crypto/tool/stqrg.html

If you require further assistance please contact us by sending email to
export@cisco.com.

License Level: ipservices
License Type: Permanent Right-To-Use
Next reload license Level: ipservices

cisco WS-C3560CX-8PC-S (APM86XXX) processor (revision A0) with 524288K bytes of memory.
Processor board ID FOCXXXXXXXX
Last reset from power-on
5 Virtual Ethernet interfaces
12 Gigabit Ethernet interfaces
The password-recovery mechanism is enabled.

512K bytes of flash-simulated non-volatile configuration memory.
Base ethernet MAC Address       : FF:FF:FF:FF:FF:FF
Motherboard assembly number     : XX-XXXXX-XX
Power supply part number        : XXX-XXXX-XX
Motherboard serial number       : FOCXXXXXXXX
Power supply serial number      : FOCXXXXXXXX
Model revision number           : A0
Motherboard revision number     : A0
Model number                    : WS-C3560CX-8PC-S
System serial number            : FOCXXXXXXXX
Top Assembly Part Number        : XX-XXXX-XX
Top Assembly Revision Number    : A0
Version ID                      : V01
CLEI Code Number                : XXXXXXXXXX
Hardware Board Revision Number  : 0x02


Switch Ports Model                     SW Version            SW Image
------ ----- -----                     ----------            ----------
*    1 12    WS-C3560CX-8PC-S          15.2(4)E7             C3560CX-UNIVERSALK9-M


Configuration register is 0xF

3560CX#"""
    test_operations = [(channel_input_1, channel_output_1), (channel_input_2, channel_output_2)]
    conn = mocked_netmiko_driver(test_operations)
    conn.default_desired_priv = "privilege_exec"
    conn.textfsm_platform = "cisco_ios"
    result = conn.send_command(channel_input_2, use_textfsm=True)
    assert isinstance(result, list)
    assert result[0][0] == "15.2(4)E7"


@pytest.mark.skipif(textfsm_avail is False, reason="textfsm and/or ntc_templates are not installed")
def test_netmiko_send_command_textfsm_success_manual_template(mocked_netmiko_driver):
    channel_input_1 = "\n"
    channel_output_1 = "\n3560CX#"
    channel_input_2 = "show version"
    channel_output_2 = """Cisco IOS Software, C3560CX Software (C3560CX-UNIVERSALK9-M), Version 15.2(4)E7, RELEASE SOFTWARE (fc2)
Technical Support: http://www.cisco.com/techsupport
Copyright (c) 1986-2018 by Cisco Systems, Inc.
Compiled Tue 18-Sep-18 13:20 by prod_rel_team

ROM: Bootstrap program is C3560CX boot loader
BOOTLDR: C3560CX Boot Loader (C3560CX-HBOOT-M) Version 15.2(4r)E5, RELEASE SOFTWARE (fc4)

3560CX uptime is 2 weeks, 3 days, 18 hours, 3 minutes
System returned to ROM by power-on
System restarted at 15:59:35 PST Wed Jan 15 2020
System image file is "flash:c3560cx-universalk9-mz.152-4.E7.bin"
Last reload reason: power-on



This product contains cryptographic features and is subject to United
States and local country laws governing import, export, transfer and
use. Delivery of Cisco cryptographic products does not imply
third-party authority to import, export, distribute or use encryption.
Importers, exporters, distributors and users are responsible for
compliance with U.S. and local country laws. By using this product you
agree to comply with applicable laws and regulations. If you are unable
to comply with U.S. and local laws, return this product immediately.

A summary of U.S. laws governing Cisco cryptographic products may be found at:
http://www.cisco.com/wwl/export/crypto/tool/stqrg.html

If you require further assistance please contact us by sending email to
export@cisco.com.

License Level: ipservices
License Type: Permanent Right-To-Use
Next reload license Level: ipservices

cisco WS-C3560CX-8PC-S (APM86XXX) processor (revision A0) with 524288K bytes of memory.
Processor board ID FOCXXXXXXXX
Last reset from power-on
5 Virtual Ethernet interfaces
12 Gigabit Ethernet interfaces
The password-recovery mechanism is enabled.

512K bytes of flash-simulated non-volatile configuration memory.
Base ethernet MAC Address       : FF:FF:FF:FF:FF:FF
Motherboard assembly number     : XX-XXXXX-XX
Power supply part number        : XXX-XXXX-XX
Motherboard serial number       : FOCXXXXXXXX
Power supply serial number      : FOCXXXXXXXX
Model revision number           : A0
Motherboard revision number     : A0
Model number                    : WS-C3560CX-8PC-S
System serial number            : FOCXXXXXXXX
Top Assembly Part Number        : XX-XXXX-XX
Top Assembly Revision Number    : A0
Version ID                      : V01
CLEI Code Number                : XXXXXXXXXX
Hardware Board Revision Number  : 0x02


Switch Ports Model                     SW Version            SW Image
------ ----- -----                     ----------            ----------
*    1 12    WS-C3560CX-8PC-S          15.2(4)E7             C3560CX-UNIVERSALK9-M


Configuration register is 0xF

3560CX#"""
    test_operations = [(channel_input_1, channel_output_1), (channel_input_2, channel_output_2)]
    conn = mocked_netmiko_driver(test_operations)
    conn.default_desired_priv = "privilege_exec"
    conn.textfsm_platform = "cisco_ios"
    template_dir = pkg_resources.resource_filename("ntc_templates", "templates")
    cli_table = textfsm.clitable.CliTable("index", template_dir)
    template_index = cli_table.index.GetRowMatch(
        {"Platform": conn.textfsm_platform, "Command": channel_input_2}
    )
    template_name = cli_table.index.index[template_index]["Template"]
    template = open(f"{template_dir}/{template_name}")
    result = conn.send_command(channel_input_2, use_textfsm=True, textfsm_template=template)
    assert isinstance(result, list)
    assert result[0][0] == "15.2(4)E7"


def test_netmiko_send_configs(mocked_netmiko_driver):
    channel_input_1 = "\n"
    channel_output_1 = "\n3560CX#"
    channel_input_2 = "\n"
    channel_output_2 = "\n3560CX#"
    channel_input_3 = "configure terminal"
    channel_output_3 = """Enter configuration commands, one per line.  End with CNTL/Z.
3560CX(config)#"""
    channel_input_4 = "\n"
    channel_output_4 = "3560CX(config)#"
    channel_input_5 = "hostname XC0653"
    channel_output_5 = "XC0653(config)#"
    channel_input_6 = "\n"
    channel_output_6 = "XC0653(config)#"
    channel_input_7 = "\n"
    channel_output_7 = "XC0653(config)#"
    channel_input_8 = "end"
    channel_output_8 = "3560CX#"
    channel_input_9 = "\n"
    channel_output_9 = "\n3560CX#"
    test_operations = [
        (channel_input_1, channel_output_1),
        (channel_input_2, channel_output_2),
        (channel_input_3, channel_output_3),
        (channel_input_4, channel_output_4),
        (channel_input_5, channel_output_5),
        (channel_input_6, channel_output_6),
        (channel_input_7, channel_output_7),
        (channel_input_8, channel_output_8),
        (channel_input_9, channel_output_9),
    ]
    conn = mocked_netmiko_driver(test_operations)
    conn.default_desired_priv = "privilege_exec"
    result = conn.send_config_set(channel_input_5, strip_prompt=False)
    assert result == channel_output_5
