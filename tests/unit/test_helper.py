import importlib
import os
import re
import sys
from io import TextIOWrapper
from logging import getLogger
from pathlib import Path

import pkg_resources  # pylint: disable=C041
import pytest

import scrapli
from scrapli.helper import (
    _find_transport_plugin,
    _textfsm_get_template,
    attach_duplicate_log_filter,
    genie_parse,
    get_prompt_pattern,
    resolve_file,
    strip_ansi,
    textfsm_parse,
    ttp_parse,
)

TEST_DATA_DIR = f"{Path(scrapli.__file__).parents[1]}/tests/test_data"

IOS_ARP = """Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  172.31.254.1            -   0000.0c07.acfe  ARPA   Vlan254
Internet  172.31.254.2            -   c800.84b2.e9c2  ARPA   Vlan254
"""


def test_get_prompt_pattern_class_pattern():
    class_pattern = "^averygoodpattern$"
    result = get_prompt_pattern("", class_pattern)
    assert result == re.compile(b"^averygoodpattern$", re.IGNORECASE | re.MULTILINE)


def test_get_prompt_pattern_class_pattern_no_line_start_end_markers():
    class_pattern = "averygoodpattern"
    result = get_prompt_pattern(class_pattern, "")
    assert result == re.compile(b"averygoodpattern")


def test_get_prompt_pattern_arg_pattern():
    class_pattern = "averygoodpattern"
    result = get_prompt_pattern("^awesomepattern$", class_pattern)
    assert result == re.compile(b"^awesomepattern$", re.IGNORECASE | re.MULTILINE)


def test_get_prompt_pattern_arg_string():
    class_pattern = "averygoodpattern"
    result = get_prompt_pattern("awesomepattern", class_pattern)
    assert result == re.compile(b"awesomepattern")


def test__strip_ansi():
    output = b"[admin@CoolDevice.Sea1: \x1b[1m/\x1b[0;0m]$"
    output = strip_ansi(output)
    assert output == b"[admin@CoolDevice.Sea1: /]$"


@pytest.mark.skipif(sys.platform.startswith("win"), reason="not supporting textfsm on windows")
def test__textfsm_get_template_valid_template():
    template = _textfsm_get_template("cisco_nxos", "show ip arp")
    template_dir = pkg_resources.resource_filename("ntc_templates", "templates")
    assert isinstance(template, TextIOWrapper)
    assert template.name == f"{template_dir}/cisco_nxos_show_ip_arp.textfsm"


@pytest.mark.skipif(sys.platform.startswith("win"), reason="not supporting textfsm on windows")
def test__textfsm_get_template_invalid_template():
    template = _textfsm_get_template("cisco_nxos", "show racecar")
    assert not template


@pytest.mark.skipif(sys.platform.startswith("win"), reason="not supporting textfsm on windows")
@pytest.mark.parametrize(
    "parse_type",
    [
        (
            False,
            ["Internet", "172.31.254.1", "-", "0000.0c07.acfe", "ARPA", "Vlan254"],
        ),
        (
            True,
            {
                "protocol": "Internet",
                "address": "172.31.254.1",
                "age": "-",
                "mac": "0000.0c07.acfe",
                "type": "ARPA",
                "interface": "Vlan254",
            },
        ),
    ],
    ids=["to_dict_false", "to_dict_true"],
)
def test_textfsm_parse_success(parse_type):
    to_dict = parse_type[0]
    expected_result = parse_type[1]
    template = _textfsm_get_template("cisco_ios", "show ip arp")
    result = textfsm_parse(template, IOS_ARP, to_dict=to_dict)
    assert isinstance(result, list)
    assert result[0] == expected_result


@pytest.mark.skipif(sys.platform.startswith("win"), reason="not supporting textfsm on windows")
@pytest.mark.parametrize(
    "parse_type",
    [
        (
            False,
            ["Internet", "172.31.254.1", "-", "0000.0c07.acfe", "ARPA", "Vlan254"],
        ),
        (
            True,
            {
                "protocol": "Internet",
                "address": "172.31.254.1",
                "age": "-",
                "mac": "0000.0c07.acfe",
                "type": "ARPA",
                "interface": "Vlan254",
            },
        ),
    ],
    ids=["to_dict_false", "to_dict_true"],
)
def test_textfsm_parse_success_string_path(parse_type):
    to_dict = parse_type[0]
    expected_result = parse_type[1]
    template = _textfsm_get_template("cisco_ios", "show ip arp")
    result = textfsm_parse(template.name, IOS_ARP, to_dict=to_dict)
    assert isinstance(result, list)
    assert result[0] == expected_result


@pytest.mark.skipif(sys.platform.startswith("win"), reason="not supporting textfsm on windows")
def test_textfsm_parse_failure():
    template = _textfsm_get_template("cisco_ios", "show ip arp")
    result = textfsm_parse(template, "not really arp data")
    assert result == []


@pytest.mark.skipif(
    sys.version_info.minor > 8, reason="genie not currently available for python 3.9"
)
@pytest.mark.skipif(sys.platform.startswith("win"), reason="not supporting genie on windows")
def test_genie_parse_success():
    result = genie_parse("iosxe", "show ip arp", IOS_ARP)
    assert isinstance(result, dict)
    assert (
        result["interfaces"]["Vlan254"]["ipv4"]["neighbors"]["172.31.254.1"]["ip"] == "172.31.254.1"
    )


@pytest.mark.skipif(
    sys.version_info.minor > 8, reason="genie not currently available for python 3.9"
)
@pytest.mark.skipif(sys.platform.startswith("win"), reason="not supporting genie on windows")
def test_genie_parse_failure():
    result = genie_parse("iosxe", "show ip arp", "not really arp data")
    assert result == []
    # w/out killing this module pyfakefs explodes. dont remember why/how i found that out...
    del sys.modules["pyats.configuration"]


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
    assert result == []


@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="not dealing with windows path things in tests"
)
def test_resolve_file():
    resolved_file = resolve_file(file=f"{TEST_DATA_DIR}/files/_ssh_config")
    assert resolved_file == f"{TEST_DATA_DIR}/files/_ssh_config"


@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="not dealing with windows path things in tests"
)
def test_resolve_file_expanduser(fs):
    fs.add_real_file(
        source_path=f"{TEST_DATA_DIR}/files/_ssh_config",
        target_path=f"{os.path.expanduser('~')}/myneatfile",
    )
    resolved_file = resolve_file(file=f"~/myneatfile")
    assert resolved_file == f"{os.path.expanduser('~')}/myneatfile"


@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="not dealing with windows path things in tests"
)
def test_resolve_file_failure():
    with pytest.raises(ValueError) as exc:
        resolve_file(file=f"~/myneatfile")
    assert str(exc.value) == "File path `~/myneatfile` could not be resolved"


def test_attach_duplicate_log_filter():
    dummy_logger = getLogger("this_is_a_dumb_test_log")
    assert dummy_logger.filters == []
    attach_duplicate_log_filter(logger=dummy_logger)
    # simple assert to confirm that we got the dup filter attached to the new logger
    assert dummy_logger.filters[0].__class__.__name__ == "DuplicateFilter"


def test_factory_no_scrapli_community():
    with pytest.raises(ModuleNotFoundError) as exc:
        _find_transport_plugin(transport="blah")
    assert (
        str(exc.value)
        == "\n***** Module 'scrapli_blah' not found! ************************************************\nTo resolve this issue, ensure you are referencing a valid transport plugin. Transport plugins should be named similar to `scrapli_paramiko` or `scrapli_ssh2`, and can be selected by passing simply `paramiko` or `ssh2` into the scrapli driver. You can install most plugins with pip: `pip install scrapli-ssh2` for example.\n***** Module 'scrapli_blah' not found! ************************************************"
    )


def test_textfsm_get_template_no_textfsm(monkeypatch):
    def mock_import_module(name, package):
        raise ModuleNotFoundError

    monkeypatch.setattr(importlib, "import_module", mock_import_module)

    with pytest.warns(UserWarning) as warning_msg:
        _textfsm_get_template(platform="blah", command="blah")
    assert (
        str(warning_msg._list[0].message)
        == "\n***** Module 'None' not installed! ****************************************************\nTo resolve this issue, install 'None'. You can do this in one of the following ways:\n1: 'pip install -r requirements-textfsm.txt'\n2: 'pip install scrapli[textfsm]'\n***** Module 'None' not installed! ****************************************************"
    )


def test_genie_parse_no_genie(monkeypatch):
    def mock_import_module(name, package):
        raise ModuleNotFoundError

    monkeypatch.setattr(importlib, "import_module", mock_import_module)

    with pytest.warns(UserWarning) as warning_msg:
        genie_parse(platform="blah", command="blah", output="blah")
    assert (
        str(warning_msg._list[0].message)
        == "\n***** Module 'None' not installed! ****************************************************\nTo resolve this issue, install 'None'. You can do this in one of the following ways:\n1: 'pip install -r requirements-genie.txt'\n2: 'pip install scrapli[genie]'\n***** Module 'None' not installed! ****************************************************"
    )


def test_ttp_parse_no_ttp(monkeypatch):
    def mock_import_module(name):
        raise ModuleNotFoundError

    monkeypatch.setattr(importlib, "import_module", mock_import_module)

    with pytest.warns(UserWarning) as warning_msg:
        ttp_parse(template="blah", output="blah")
    assert (
        str(warning_msg._list[0].message)
        == "\n***** Module 'None' not installed! ****************************************************\nTo resolve this issue, install 'None'. You can do this in one of the following ways:\n1: 'pip install -r requirements-ttp.txt'\n2: 'pip install scrapli[ttp]'\n***** Module 'None' not installed! ****************************************************"
    )
