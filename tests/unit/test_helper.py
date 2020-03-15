import os
import re
import sys
from io import TextIOWrapper
from pathlib import Path

import pkg_resources  # pylint: disable=C041
import pytest

import scrapli
from scrapli.helper import (
    _textfsm_get_template,
    get_prompt_pattern,
    resolve_ssh_config,
    strip_ansi,
    textfsm_parse,
)

UNIT_TEST_DIR = f"{Path(scrapli.__file__).parents[1]}/tests/unit/"

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
    result = get_prompt_pattern("", class_pattern)
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


def test__textfsm_get_template_invalid_template():
    template = _textfsm_get_template("cisco_nxos", "show racecar")
    assert not template


@pytest.mark.skipif(sys.platform.startswith("win"), reason="not supporting textfsm on windows")
def test_text_textfsm_parse_success():
    template = _textfsm_get_template("cisco_ios", "show ip arp")
    result = textfsm_parse(template, IOS_ARP)
    assert isinstance(result, list)
    assert result[0] == ["Internet", "172.31.254.1", "-", "0000.0c07.acfe", "ARPA", "Vlan254"]


@pytest.mark.skipif(sys.platform.startswith("win"), reason="not supporting textfsm on windows")
def test_text_textfsm_parse_success_string_path():
    template = _textfsm_get_template("cisco_ios", "show ip arp")
    result = textfsm_parse(template.name, IOS_ARP)
    assert isinstance(result, list)
    assert result[0] == ["Internet", "172.31.254.1", "-", "0000.0c07.acfe", "ARPA", "Vlan254"]


@pytest.mark.skipif(sys.platform.startswith("win"), reason="not supporting textfsm on windows")
def test_text_textfsm_parse_failure():
    template = _textfsm_get_template("cisco_ios", "show ip arp")
    result = textfsm_parse(template, "not really arp data")
    assert result == []


def test_resolve_ssh_config_file_explicit():
    ssh_conf = resolve_ssh_config(f"{UNIT_TEST_DIR}_ssh_config")
    assert ssh_conf == f"{UNIT_TEST_DIR}_ssh_config"


@pytest.mark.skipif(sys.platform.startswith("win"), reason="not supporting ssh config on windows")
def test_resolve_ssh_config_file_user(fs):
    fs.add_real_file("/etc/ssh/ssh_config", target_path=f"{os.path.expanduser('~')}/.ssh/config")
    ssh_conf = resolve_ssh_config("")
    assert ssh_conf == f"{os.path.expanduser('~')}/.ssh/config"


@pytest.mark.skipif(sys.platform.startswith("win"), reason="not supporting ssh config on windows")
def test_resolve_ssh_config_file_system(fs):
    fs.add_real_file("/etc/ssh/ssh_config")
    ssh_conf = resolve_ssh_config("")
    assert ssh_conf == "/etc/ssh/ssh_config"
