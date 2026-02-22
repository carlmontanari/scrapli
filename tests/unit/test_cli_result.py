import pytest

from scrapli.cli_parse import textfsm_get_template
from scrapli.cli_result import Result


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
    r = Result(
        host="localhost",
        port=22,
        inputs="show ip arp",
        start_time=0,
        splits=[1],
        results_raw=result.encode(),
        results=result,
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

    r = Result(
        host="localhost",
        port=22,
        inputs="show ip arp",
        start_time=0,
        splits=[1],
        results_raw=result.encode(),
        results=result,
        results_failed_indicator="",
        textfsm_platform="cisco_ios",
        genie_platform="iosxe",
    )

    assert r.textfsm_parse(template=template)[0] == expected
