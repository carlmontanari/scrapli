from importlib import resources
from io import TextIOWrapper

import pytest

from scrapli.cli_parse import genie_parse, textfsm_get_template, textfsm_parse
from scrapli.exceptions import ParsingException

IOS_ARP = """Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  172.31.254.1            -   0000.0c07.acfe  ARPA   Vlan254
Internet  172.31.254.2            -   c800.84b2.e9c2  ARPA   Vlan254
"""
IOS_ARP_NTC_TEMPLATE_URL = "https://raw.githubusercontent.com/networktocode/ntc-templates/master/ntc_templates/templates/cisco_ios_show_ip_arp.textfsm"


def test_textfsm_get_template():
    template = textfsm_get_template("cisco_nxos", "show ip arp")
    template_dir = f"{resources.files('ntc_templates')}/templates"
    assert isinstance(template, TextIOWrapper)
    assert template.name == f"{template_dir}/cisco_nxos_show_ip_arp.textfsm"


def test_textfsm_get_template_invalid_template():
    template = textfsm_get_template("cisco_nxos", "show racecar")
    assert not template


@pytest.mark.parametrize(
    "test_data",
    [
        (
            False,
            ["Internet", "172.31.254.1", "-", "0000.0c07.acfe", "ARPA", "Vlan254"],
        ),
        (
            True,
            {
                "protocol": "Internet",
                "ip_address": "172.31.254.1",
                "age": "-",
                "mac_address": "0000.0c07.acfe",
                "type": "ARPA",
                "interface": "Vlan254",
            },
        ),
    ],
    ids=["to_dict_false", "to_dict_true"],
)
def test_textfsm_parse(test_data):
    to_dict, expected_output = test_data
    template = textfsm_get_template("cisco_ios", "show ip arp")
    result = textfsm_parse(template, IOS_ARP, to_dict=to_dict)
    assert isinstance(result, list)
    assert result[0] == expected_output


@pytest.mark.parametrize(
    "test_data",
    [
        (
            False,
            ["Internet", "172.31.254.1", "-", "0000.0c07.acfe", "ARPA", "Vlan254"],
        ),
        (
            True,
            {
                "protocol": "Internet",
                "ip_address": "172.31.254.1",
                "age": "-",
                "mac_address": "0000.0c07.acfe",
                "type": "ARPA",
                "interface": "Vlan254",
            },
        ),
    ],
    ids=["to_dict_false", "to_dict_true"],
)
def test_textfsm_parse_string_path(test_data):
    to_dict, expected_output = test_data
    template = textfsm_get_template("cisco_ios", "show ip arp")
    result = textfsm_parse(template.name, IOS_ARP, to_dict=to_dict)
    assert isinstance(result, list)
    assert result[0] == expected_output


@pytest.mark.parametrize(
    "test_data",
    [
        (
            False,
            ["Internet", "172.31.254.1", "-", "0000.0c07.acfe", "ARPA", "Vlan254"],
        ),
        (
            True,
            {
                "protocol": "Internet",
                "ip_address": "172.31.254.1",
                "age": "-",
                "mac_address": "0000.0c07.acfe",
                "type": "ARPA",
                "interface": "Vlan254",
            },
        ),
    ],
    ids=["to_dict_false", "to_dict_true"],
)
def test_textfsm_parse_url_path(test_data):
    to_dict, expected_output = test_data
    template = IOS_ARP_NTC_TEMPLATE_URL
    result = textfsm_parse(template, IOS_ARP, to_dict=to_dict)
    assert isinstance(result, list)
    assert result[0] == expected_output


def test_textfsm_parse_failed_to_parse():
    template = textfsm_get_template("cisco_ios", "show ip arp")

    with pytest.raises(ParsingException):
        textfsm_parse(template, "not really arp data")


def test_genie_parser():
    result = genie_parse("iosxe", "show ip arp", IOS_ARP)
    assert isinstance(result, dict)
    assert (
        result["interfaces"]["Vlan254"]["ipv4"]["neighbors"]["172.31.254.1"]["ip"] == "172.31.254.1"
    )
