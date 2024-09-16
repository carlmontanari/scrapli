import sys
from io import TextIOWrapper
from pathlib import Path
from shutil import get_terminal_size

import pytest

from scrapli.exceptions import ScrapliValueError
from scrapli.helper import (
    _textfsm_get_template,
    _textfsm_get_template_directory,
    format_user_warning,
    genie_parse,
    output_roughly_contains_input,
    resolve_file,
    textfsm_parse,
    ttp_parse,
    user_warning,
)

IOS_ARP = """Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  172.31.254.1            -   0000.0c07.acfe  ARPA   Vlan254
Internet  172.31.254.2            -   c800.84b2.e9c2  ARPA   Vlan254
"""
IOS_ARP_NTC_TEMPLATE_URL = "https://raw.githubusercontent.com/networktocode/ntc-templates/master/ntc_templates/templates/cisco_ios_show_ip_arp.textfsm"


def test_textfsm_get_template():
    template = _textfsm_get_template("cisco_nxos", "show ip arp")
    template_dir = _textfsm_get_template_directory()
    assert isinstance(template, TextIOWrapper)
    assert template.name == f"{template_dir}/cisco_nxos_show_ip_arp.textfsm"


def test_textfsm_get_template_invalid_template():
    template = _textfsm_get_template("cisco_nxos", "show racecar")
    assert not template


def test_textfsm_no_ntc_templates(monkeypatch):
    def _import_module(name, package):
        raise ModuleNotFoundError

    monkeypatch.setattr("importlib.import_module", _import_module)

    with pytest.warns(UserWarning) as exc:
        _textfsm_get_template("cisco_nxos", "show racecar")

    assert "Optional Extra Not Installed!" in str(exc.list[0].message)


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
    template = _textfsm_get_template("cisco_ios", "show ip arp")
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
    template = _textfsm_get_template("cisco_ios", "show ip arp")
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
    template = _textfsm_get_template("cisco_ios", "show ip arp")
    result = textfsm_parse(template, "not really arp data")
    assert result == []


def test_textfsm_parse_failed_to_parse_with_raise():
    template = _textfsm_get_template("cisco_ios", "show ip arp")
    with pytest.raises(Exception):
        result = textfsm_parse(template, "not really arp data", raise_err=True)
        assert result == []


@pytest.mark.skipif(
    sys.version_info.minor > 10, reason="genie not currently available for python 3.11"
)
def test_genie_parser():
    result = genie_parse("iosxe", "show ip arp", IOS_ARP)
    assert isinstance(result, dict)
    assert (
        result["interfaces"]["Vlan254"]["ipv4"]["neighbors"]["172.31.254.1"]["ip"] == "172.31.254.1"
    )


@pytest.mark.skipif(
    sys.version_info.minor > 10, reason="genie not currently available for python 3.11"
)
def test_genie_parse_failure():
    result = genie_parse("iosxe", "show ip arp", "not really arp data")
    assert result == []


def test_genie_no_genie_installed(monkeypatch):
    def _import_module(name, package):
        raise ModuleNotFoundError

    monkeypatch.setattr("importlib.import_module", _import_module)

    with pytest.warns(UserWarning) as exc:
        output = genie_parse("cisco_nxos", "show racecar", "something")

    assert "Optional Extra Not Installed!" in str(exc.list[0].message)
    assert output == []


def test_ttp_parse():
    # example data lifted straight out of ttp docs
    data_to_parse = """
    interface Loopback0
     description Router-id-loopback
     ip address 192.168.0.113/24
    !
    interface Vlan778
     description CPE_Acces_Vlan
     ip address 2002::fd37/124
     ip vrf CPE1
    !
    """

    ttp_template = """
    interface {{ interface }}
     ip address {{ ip }}/{{ mask }}
     description {{ description }}
     ip vrf {{ vrf }}
    """

    expected = [
        [
            {
                "ip": "192.168.0.113",
                "mask": "24",
                "description": "Router-id-loopback",
                "interface": "Loopback0",
            },
            {
                "vrf": "CPE1",
                "ip": "2002::fd37",
                "mask": "124",
                "description": "CPE_Acces_Vlan",
                "interface": "Vlan778",
            },
        ]
    ]
    result = ttp_parse(template=ttp_template, output=data_to_parse)
    assert result == expected


def test_ttp_parse_invalid_template():
    result = ttp_parse(template=None, output="blah")
    assert result == []


def test_ttp_parse_failed_to_parse():
    result = ttp_parse(template="mytemplateisneat", output="blah")
    assert result == [{}]


def test_ttp_no_ttp_installed(monkeypatch):
    def _import_module(name):
        raise ModuleNotFoundError

    monkeypatch.setattr("importlib.import_module", _import_module)

    with pytest.warns(UserWarning) as exc:
        output = ttp_parse("cisco_nxos", "show racecar")

    assert "Optional Extra Not Installed!" in str(exc.list[0].message)
    assert output == []


def test_resolve_file(fs_, real_ssh_config_file_path):
    # pyfakefs so this is not host dependent
    fs_.add_real_file(source_path=real_ssh_config_file_path, target_path="/some/neat/path/myfile")
    assert resolve_file(file="/some/neat/path/myfile") == "/some/neat/path/myfile"


def test_resolve_file_expanduser(fs_, real_ssh_config_file_path):
    # pyfakefs so this is not host dependent
    fs_.add_real_file(
        source_path=real_ssh_config_file_path, target_path=Path("~/myfile").expanduser()
    )
    assert resolve_file(file="~/myfile") == str(Path("~/myfile").expanduser())


def test_resolve_file_failure():
    with pytest.raises(ScrapliValueError) as exc:
        resolve_file(file=f"~/myneatfile")


def test_format_user_warning():
    warning_string = format_user_warning(title="blah", message="something")
    assert "* blah *" in warning_string
    assert "something" in warning_string


def test_format_user_warning_really_long_title():
    terminal_width = get_terminal_size().columns

    title = "z" * (terminal_width - 5)

    warning_string = format_user_warning(title=title, message="something")

    assert warning_string.strip().startswith("*")
    assert warning_string.strip().endswith("*")
    assert title in warning_string


def test_user_warning():
    with pytest.warns(UserWarning):
        user_warning(title="blah", message="something")


@pytest.mark.parametrize(
    "test_data",
    [
        (
            True,
            b"show version",
            b"show version",
        ),
        (
            True,
            b"configure",
            b"\x1b7c\x1b8\x1b[1C\x1b7o\x1b8\x1b[1C\x1b7n\x1b8\x1b[1C\x1b7f\x1b8\x1b[1C\x1b7i\x1b8\x1b[1C\x1b7g\x1b8\x1b[1C\x1b7u\x1b8\x1b[1C\x1b7r\x1b8\x1b[1C\x1b7e\x1b8\x1b[1C",
        ),
        (
            False,
            b"show version",
            b"foo bar baz",
        ),
    ],
    ids=["simple", "messy_ansi", "does_not_contain"],
)
def test_output_roughly_contains_input(test_data):
    expected, input_, output = test_data
    actual = output_roughly_contains_input(input_=input_, output=output)
    assert actual == expected
