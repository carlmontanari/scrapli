import types

import pytest

from scrapli.driver.network_driver import PrivilegeLevel
from scrapli.exceptions import CouldNotAcquirePrivLevel, UnknownPrivLevel

try:
    import ntc_templates
    import textfsm

    textfsm_avail = True
except ImportError:
    textfsm_avail = False


def test__determine_current_priv(mocked_network_driver):
    conn = mocked_network_driver([])
    current_priv = conn._determine_current_priv("execprompt>")
    assert current_priv.name == "exec"


def test__determine_current_priv_unknown(mocked_network_driver):
    conn = mocked_network_driver([])
    with pytest.raises(UnknownPrivLevel):
        conn._determine_current_priv("!!!!thisissoooowrongggg!!!!!!?!")


def test__escalate(mocked_network_driver):
    channel_input_1 = "\n"
    channel_output_1 = "\n3560CX#"
    channel_input_2 = "configure terminal"
    channel_output_2 = """Enter configuration commands, one per line.  End with CNTL/Z.
3560CX(config)#"""
    channel_ops = [(channel_input_1, channel_output_1), (channel_input_2, channel_output_2)]

    conn = mocked_network_driver(channel_ops)
    conn._escalate()


def test__escalate_unknown_priv(mocked_network_driver):
    channel_input_1 = "\n"
    channel_output_1 = "\n3560CX#"
    channel_input_2 = "configure terminal"
    channel_output_2 = """Enter configuration commands, one per line.  End with CNTL/Z.
    3560CX(config)#"""
    channel_ops = [(channel_input_1, channel_output_1), (channel_input_2, channel_output_2)]

    conn = mocked_network_driver(channel_ops)

    mock_privs = {
        "privilege_exec": (
            PrivilegeLevel(
                r"^[a-z0-9.\-@/:]{1,32}#$",
                "privilege_exec",
                "exec",
                "disable",
                "configuration",
                "configure terminal",
                False,
                False,
                True,
                1,
            )
        ),
    }
    conn.privs = mock_privs

    with pytest.raises(UnknownPrivLevel):
        conn._escalate()


def test__escalate_auth(mocked_network_driver):
    channel_input_1 = "\n"
    channel_output_1 = "\n3560CX>"
    channel_input_2 = "enable"
    channel_output_2 = "Password:"
    channel_input_3 = "password"
    channel_output_3 = "\n3560CX#"
    channel_ops = [
        (channel_input_1, channel_output_1),
        (channel_input_2, channel_output_2),
        (channel_input_3, channel_output_3),
    ]

    conn = mocked_network_driver(channel_ops)

    mock_privs = {
        "exec": (
            PrivilegeLevel(
                r"^[a-z0-9.\-@()/:]{1,32}>$",
                "exec",
                None,
                None,
                "privilege_exec",
                "enable",
                True,
                "Password:",
                True,
                0,
            )
        ),
        "privilege_exec": (
            PrivilegeLevel(
                r"^[a-z0-9.\-@/:]{1,32}#$",
                "privilege_exec",
                "exec",
                "disable",
                "configuration",
                "configure terminal",
                False,
                False,
                True,
                1,
            )
        ),
    }
    conn.privs = mock_privs

    conn._escalate()


def test__deescalate(mocked_network_driver):
    channel_input_1 = "\n"
    channel_output_1 = "\n3560CX#"
    channel_input_2 = "end"
    channel_output_2 = "3560CX>"
    channel_ops = [(channel_input_1, channel_output_1), (channel_input_2, channel_output_2)]

    conn = mocked_network_driver(channel_ops)
    conn._deescalate()


def test_acquire_priv(mocked_network_driver):
    channel_input_1 = "\n"
    channel_output_1 = "\n3560CX>"
    channel_input_2 = "\n"
    channel_output_2 = "3560CX>"
    channel_input_3 = "enable"
    channel_output_3 = "Password: "
    channel_input_4 = "password"
    channel_output_4 = "\n3560CX#"
    channel_input_5 = "\n"
    channel_output_5 = "3560CX#"
    channel_input_6 = "\n"
    channel_output_6 = "3560CX#"
    channel_input_7 = "configure terminal"
    channel_output_7 = """Enter configuration commands, one per line.  End with CNTL/Z.
3560CX(config)#"""
    channel_input_8 = "\n"
    channel_output_8 = "3560CX(config)#"
    channel_ops = [
        (channel_input_1, channel_output_1),
        (channel_input_2, channel_output_2),
        (channel_input_3, channel_output_3),
        (channel_input_4, channel_output_4),
        (channel_input_5, channel_output_5),
        (channel_input_6, channel_output_6),
        (channel_input_7, channel_output_7),
        (channel_input_8, channel_output_8),
    ]

    conn = mocked_network_driver(channel_ops)
    conn.acquire_priv("configuration")


def test_acquire_priv_deescalate(mocked_network_driver):
    channel_input_1 = "\n"
    channel_output_1 = "3560CX(config)#"
    channel_input_2 = "\n"
    channel_output_2 = "3560CX(config)#"
    channel_input_3 = "end"
    channel_output_3 = "3560CX#"
    channel_input_4 = "\n"
    channel_output_4 = "3560CX#"
    channel_ops = [
        (channel_input_1, channel_output_1),
        (channel_input_2, channel_output_2),
        (channel_input_3, channel_output_3),
        (channel_input_4, channel_output_4),
    ]

    conn = mocked_network_driver(channel_ops)
    conn.acquire_priv("privilege_exec")


def test_acquire_priv_could_not_acquire_priv(mocked_network_driver):
    channel_input_1 = "\n"
    channel_output_1 = "\n3560CX>"
    channel_input_2 = "\n"
    channel_output_2 = "3560CX>"
    channel_input_3 = "enable"
    channel_output_3 = "Password: "
    channel_input_4 = "password"
    channel_output_4 = "\n3560CX#"

    channel_input_5 = "\n"
    channel_output_5 = "\n3560CX>"
    channel_input_6 = "\n"
    channel_output_6 = "3560CX>"
    channel_input_7 = "enable"
    channel_output_7 = "Password: "
    channel_input_8 = "password"
    channel_output_8 = "\n3560CX#"

    channel_input_9 = "\n"
    channel_output_9 = "\n3560CX>"
    channel_input_10 = "\n"
    channel_output_10 = "3560CX>"
    channel_input_11 = "enable"
    channel_output_11 = "Password: "
    channel_input_12 = "password"
    channel_output_12 = "\n3560CX#"

    channel_input_13 = "\n"
    channel_output_13 = "\n3560CX>"

    channel_ops = [
        (channel_input_1, channel_output_1),
        (channel_input_2, channel_output_2),
        (channel_input_3, channel_output_3),
        (channel_input_4, channel_output_4),
        (channel_input_5, channel_output_5),
        (channel_input_6, channel_output_6),
        (channel_input_7, channel_output_7),
        (channel_input_8, channel_output_8),
        (channel_input_9, channel_output_9),
        (channel_input_10, channel_output_10),
        (channel_input_11, channel_output_11),
        (channel_input_12, channel_output_12),
        (channel_input_13, channel_output_13),
    ]

    conn = mocked_network_driver(channel_ops)
    mock_privs = {
        "exec": (
            PrivilegeLevel(
                r"^[a-z0-9.\-@()/:]{1,32}>$",
                "exec",
                None,
                None,
                "privilege_exec",
                "enable",
                True,
                "Password:",
                True,
                0,
            )
        ),
        "privilege_exec": (
            PrivilegeLevel(
                r"^[a-z0-9.\-@/:]{1,32}#$",
                "privilege_exec",
                "exec",
                "disable",
                "configuration",
                "configure terminal",
                False,
                False,
                True,
                1,
            )
        ),
    }
    conn.privs = mock_privs

    def _mock_escalate(self):
        self.__class__._escalate(self)
        self.channel.comms_prompt_pattern = mock_privs["exec"].pattern

    def _mock_get_prompt():
        return "3560CX>"

    conn._escalate = types.MethodType(_mock_escalate, conn)
    conn.get_prompt = _mock_get_prompt

    with pytest.raises(CouldNotAcquirePrivLevel) as exc:
        conn.acquire_priv("privilege_exec")
    assert str(exc.value) == "Could not get to 'privilege_exec' privilege level."


def test_send_commands(mocked_network_driver):
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
    conn = mocked_network_driver(test_operations)
    conn.default_desired_priv = "privilege_exec"
    output = conn.send_command(channel_input_2, strip_prompt=False)
    assert output.result == channel_output_2


def test_send_inputs_interact(mocked_network_driver):
    channel_input_1 = "\n"
    channel_output_1 = "3560CX#"
    channel_input_2 = "clear logg"
    channel_output_2 = "Clear logging buffer [confirm]"
    channel_input_3 = "\n"
    channel_output_3 = "3560CX#"
    interact = [channel_input_2, channel_output_2, "", channel_output_3]
    test_operations = [
        (channel_input_1, channel_output_1),
        (channel_input_2, channel_output_2),
        (channel_input_3, channel_output_3),
    ]
    conn = mocked_network_driver(test_operations)
    conn.default_desired_priv = "privilege_exec"
    output = conn.send_interactive(interact, hidden_response=False)
    assert output.result == "Clear logging buffer [confirm]\n\n3560CX#"


def test_send_configs(mocked_network_driver):
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
    conn = mocked_network_driver(test_operations)
    conn.default_desired_priv = "privilege_exec"
    output = conn.send_configs(channel_input_5, strip_prompt=False)
    assert output[0].result == channel_output_5


@pytest.mark.skipif(textfsm_avail is False, reason="textfsm and/or ntc_templates are not installed")
def test_send_inputs_textfsm_success(mocked_network_driver):
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
    conn = mocked_network_driver(test_operations)
    conn.default_desired_priv = "privilege_exec"
    conn.textfsm_platform = "cisco_ios"
    results = conn.send_command(channel_input_2)
    parsed_results = results.textfsm_parse_output()
    assert isinstance(parsed_results, list)
    assert parsed_results[0][0] == "15.2(4)E7"


@pytest.mark.skipif(textfsm_avail is False, reason="textfsm and/or ntc_templates are not installed")
def test_send_inputs_textfsm_fail(mocked_network_driver):
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
    conn = mocked_network_driver(test_operations)
    conn.default_desired_priv = "privilege_exec"
    conn.textfsm_platform = "not_real"
    results = conn.send_command(channel_input_2)
    parsed_results = results.textfsm_parse_output()
    assert isinstance(parsed_results, list)
    assert parsed_results == []
