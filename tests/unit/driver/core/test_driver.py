import types

import pytest

from nssh.driver.core.driver import PrivilegeLevel
from nssh.exceptions import CouldNotAcquirePrivLevel, UnknownPrivLevel


try:
    import ntc_templates
    import txtfsm

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


@pytest.mark.skipif(textfsm_avail is True, reason="textfsm and/or ntc_templates are not installed")
def test_textfsm_parse_output(mocked_network_driver):
    conn = mocked_network_driver([])
    conn.textfsm_platform = "cisco_ios"
    channel_output = """Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  172.31.254.1            -   0000.0c07.acfe  ARPA   Vlan254
Internet  172.31.254.2            -   c800.84b2.e9c2  ARPA   Vlan254
"""
    result = conn.textfsm_parse_output("show ip arp", channel_output)
    assert isinstance(result, list)
    assert result[0] == ["Internet", "172.31.254.1", "-", "0000.0c07.acfe", "ARPA", "Vlan254"]


@pytest.mark.skipif(textfsm_avail is True, reason="textfsm and/or ntc_templates are not installed")
def test_textfsm_parse_output_failure(mocked_network_driver):
    conn = mocked_network_driver([])
    conn.textfsm_platform = "cisco_ios"
    channel_output = """Protocol  Address          Blahblhablah"""
    result = conn.textfsm_parse_output("show ip arp", channel_output)
    assert result == {}


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
    channel_output_2 = """Password: """
    channel_input_3 = "password123"
    channel_output_3 = "3560CX#"
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
    channel_input_4 = "password123"
    channel_output_4 = "3560CX#"
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


def test_acquire_priv_could_not_acquire_priv(mocked_network_driver):
    channel_input_1 = "\n"
    channel_output_1 = "\n3560CX>"
    channel_input_2 = "\n"
    channel_output_2 = "3560CX>"
    channel_input_3 = "enable"
    channel_output_3 = "Password: "
    channel_input_4 = "password123"
    channel_output_4 = "3560CX#"

    channel_input_5 = "\n"
    channel_output_5 = "\n3560CX>"
    channel_input_6 = "\n"
    channel_output_6 = "3560CX>"
    channel_input_7 = "enable"
    channel_output_7 = "Password: "
    channel_input_8 = "password123"
    channel_output_8 = "3560CX#"

    channel_input_9 = "\n"
    channel_output_9 = "\n3560CX>"
    channel_input_10 = "\n"
    channel_output_10 = "3560CX>"
    channel_input_11 = "enable"
    channel_output_11 = "Password: "
    channel_input_12 = "password123"
    channel_output_12 = "3560CX#"

    channel_input_13 = "\n"
    channel_output_13 = "\n3560CX>"
    # channel_input_14 = "\n"
    # channel_output_14 = "3560CX>"
    # channel_input_15 = "enable"
    # channel_output_15 = "Password: "
    # channel_input_16 = "password123"
    # channel_output_16 = "3560CX>"

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
        # (channel_input_14, channel_output_14),
        # (channel_input_15, channel_output_15),
        # (channel_input_16, channel_output_16),
        # (channel_input_17, channel_output_17),
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

    # TODO - just need to trick this into counting too many escalate attempts

    def _mock_escalate(self):
        self.__class__._escalate(self)
        self.channel.comms_prompt_pattern = mock_privs['exec'].pattern

    def _mock_get_prompt():
        return "3560CX>"

    conn._escalate = types.MethodType(_mock_escalate, conn)
    conn.get_prompt = _mock_get_prompt

    with pytest.raises(CouldNotAcquirePrivLevel) as exc:
        conn.acquire_priv("privilege_exec")
    assert str(exc.value) == "Could not get to 'privilege_exec' privilege level."
