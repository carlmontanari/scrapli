import pytest

from scrapli.cli_parse import textfsm_get_template
from scrapli.cli_result import Result


def _make_result(failed_indicator: str) -> Result:
    return Result(
        host="localhost",
        port=22,
        inputs=b"show",
        input_lens=[4],
        start_time=1,
        splits=[2],
        result_raw_journals=b"",
        result_raw_journal_lens=[0],
        results=b"output",
        result_lens=[6],
        results_failed_indicator=failed_indicator,
        textfsm_platform="",
        genie_platform="",
    )


@pytest.mark.parametrize(
    ("first_indicator", "second_indicator", "expected_indicator"),
    [
        ("", "", ""),
        ("", "Error:", "Error:"),
        ("Invalid input", "", "Invalid input"),
        ("Invalid input", "Error:", "Invalid input"),
    ],
)
def test_result_extend_preserves_failure(first_indicator, second_indicator, expected_indicator):
    first = _make_result(first_indicator)
    second = _make_result(second_indicator)
    assert first.results_raw == [b"output"]

    first.extend(second)

    assert first.failed is bool(expected_indicator)
    assert first.results_failed_indicator == expected_indicator
    assert first.inputs == ["show", "show"]
    assert first.results == ["output", "output"]
    assert first.results_raw == [b"output", b"output"]
    assert second.results_failed_indicator == second_indicator


def test_result_extend_keeps_failure_across_multiple_extensions():
    result = _make_result("")
    result.extend(_make_result("Error:"))
    result.extend(_make_result(""))
    result.extend(_make_result("Invalid input"))

    assert result.failed is True
    assert result.results_failed_indicator == "Error:"
    assert "failed=True" in repr(result)


@pytest.mark.parametrize(
    ("result", "to_dict", "expected"),
    [
        (
            """
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  172.31.254.1            -   0000.0c07.acfe  ARPA   Vlan254
Internet  172.31.254.2            -   c800.84b2.e9c2  ARPA   Vlan254""",
            False,
            [
                "Internet",
                "172.31.254.1",
                "-",
                "0000.0c07.acfe",
                "ARPA",
                "Vlan254",
            ],
        ),
        (
            """
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  172.31.254.1            -   0000.0c07.acfe  ARPA   Vlan254
Internet  172.31.254.2            -   c800.84b2.e9c2  ARPA   Vlan254""",
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
def test_result_textfsm_parse(result, to_dict, expected):
    _input = b"show ip arp"

    r = Result(
        host="localhost",
        port=22,
        inputs=_input,
        input_lens=[len(_input)],
        start_time=0,
        splits=[1],
        result_raw_journals=b"",
        result_raw_journal_lens=[0],
        results=result.encode(),
        result_lens=[len(result)],
        results_failed_indicator="",
        textfsm_platform="cisco_ios",
        genie_platform="iosxe",
    )

    assert r.textfsm_parse(to_dict=to_dict)[0] == expected


def test_result_textfsm_parse_string_path():
    result = """
Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  172.31.254.1            -   0000.0c07.acfe  ARPA   Vlan254
Internet  172.31.254.2            -   c800.84b2.e9c2  ARPA   Vlan254"""

    expected = {
        "protocol": "Internet",
        "ip_address": "172.31.254.1",
        "age": "-",
        "mac_address": "0000.0c07.acfe",
        "type": "ARPA",
        "interface": "Vlan254",
    }

    template = textfsm_get_template("cisco_ios", "show ip arp").name

    _input = b"show ip arp"

    r = Result(
        host="localhost",
        port=22,
        inputs=_input,
        input_lens=[len(_input)],
        start_time=0,
        splits=[1],
        result_raw_journals=b"",
        result_raw_journal_lens=[0],
        results=result.encode(),
        result_lens=[len(result)],
        results_failed_indicator="",
        textfsm_platform="cisco_ios",
        genie_platform="iosxe",
    )

    assert r.textfsm_parse(template=template)[0] == expected
