import sys
from datetime import datetime

import pytest

from scrapli.exceptions import ScrapliCommandFailure
from scrapli.response import MultiResponse, Response


def test_response_init():
    response = Response("localhost", "ls -al", failed_when_contains="tacocat")
    response_start_time = str(datetime.now())[:-7]
    assert response.host == "localhost"
    assert response.channel_input == "ls -al"
    assert str(response.start_time)[:-7] == response_start_time
    assert response.failed is True
    assert bool(response) is True
    assert repr(response) == "Response <Success: False>"
    assert str(response) == "Response <Success: False>"
    assert response.failed_when_contains == ["tacocat"]
    with pytest.raises(ScrapliCommandFailure):
        response.raise_for_status()


def test_multi_response():
    response1 = Response("localhost", "ls -al")
    response2 = Response("localhost", "ls -al")
    multi_response = MultiResponse([response1, response2])
    assert len(multi_response) == 2
    assert multi_response.failed is True
    assert repr(multi_response) == "MultiResponse <Success: False; Response Elements: 2>"
    assert str(multi_response) == "MultiResponse <Success: False; Response Elements: 2>"
    with pytest.raises(ScrapliCommandFailure):
        multi_response.raise_for_status()
    multi_response[0].failed = False
    multi_response[1].failed = False
    assert multi_response.failed is False
    assert multi_response.raise_for_status() is None
    assert repr(multi_response) == "MultiResponse <Success: True; Response Elements: 2>"
    assert str(multi_response) == "MultiResponse <Success: True; Response Elements: 2>"


def test_response_record_result():
    response = Response("localhost", "ls -al")
    response_end_time = str(datetime.now())[:-7]
    response_str = """
ls -al
total 264
drwxr-xr-x  34 carl  staff   1088 Jan 27 19:07 ./
drwxr-xr-x  21 carl  staff    672 Jan 25 15:56 ../
-rw-r--r--   1 carl  staff  53248 Jan 27 19:07 .coverage
drwxr-xr-x  12 carl  staff    384 Jan 27 19:13 .git/"""
    response._record_response(response_str)
    assert str(response.finish_time)[:-7] == response_end_time
    assert response.result == response_str
    assert response.failed is False


def test_response_record_result_failed_when_failed():
    response = Response("localhost", "ls -al", failed_when_contains=["!racecar!"])
    response_end_time = str(datetime.now())[:-7]
    response_str = """
ls -al
total 264
drwxr-xr-x  34 carl  staff   1088 Jan 27 19:07 ./
drwxr-xr-x  21 carl  staff    672 Jan 25 15:56 ../
-rw-r--r--   1 carl  staff  53248 Jan 27 19:07 !racecar!
drwxr-xr-x  12 carl  staff    384 Jan 27 19:13 .git/"""
    response._record_response(response_str)
    assert str(response.finish_time)[:-7] == response_end_time
    assert response.result == response_str
    assert response.failed is True


def test_response_record_result_failed_when_success():
    response = Response("localhost", "ls -al", failed_when_contains=["!racecar!"])
    response_end_time = str(datetime.now())[:-7]
    response_str = """
ls -al
total 264
drwxr-xr-x  34 carl  staff   1088 Jan 27 19:07 ./
drwxr-xr-x  21 carl  staff    672 Jan 25 15:56 ../
-rw-r--r--   1 carl  staff  53248 Jan 27 19:07 .coverage
drwxr-xr-x  12 carl  staff    384 Jan 27 19:13 .git/"""
    response._record_response(response_str)
    assert str(response.finish_time)[:-7] == response_end_time
    assert response.result == response_str
    assert response.failed is False


@pytest.mark.skipif(sys.platform.startswith("win"), reason="not supporting textfsm on windows")
@pytest.mark.parametrize(
    "parse_type",
    [
        (False, ["Internet", "172.31.254.1", "-", "0000.0c07.acfe", "ARPA", "Vlan254"],),
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
def test_response_parse_textfsm(parse_type):
    to_dict = parse_type[0]
    expected_result = parse_type[1]
    response = Response("localhost", channel_input="show ip arp", textfsm_platform="cisco_ios")
    response_str = """Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  172.31.254.1            -   0000.0c07.acfe  ARPA   Vlan254
Internet  172.31.254.2            -   c800.84b2.e9c2  ARPA   Vlan254
"""
    response._record_response(response_str)
    assert response.textfsm_parse_output(to_dict=to_dict)[0] == expected_result


@pytest.mark.skipif(sys.platform.startswith("win"), reason="not supporting textfsm on windows")
def test_response_parse_textfsm_fail():
    response = Response("localhost", channel_input="show ip arp", textfsm_platform="cisco_ios")
    response_str = ""
    response._record_response(response_str)
    assert response.textfsm_parse_output() == []


@pytest.mark.skipif(sys.platform.startswith("win"), reason="not supporting genie on windows")
def test_response_parse_genie():
    response = Response("localhost", channel_input="show ip arp", genie_platform="iosxe")
    response_str = """Protocol  Address          Age (min)  Hardware Addr   Type   Interface
Internet  172.31.254.1            -   0000.0c07.acfe  ARPA   Vlan254
Internet  172.31.254.2            -   c800.84b2.e9c2  ARPA   Vlan254
"""
    response._record_response(response_str)
    result = response.genie_parse_output()
    assert (
        result["interfaces"]["Vlan254"]["ipv4"]["neighbors"]["172.31.254.1"]["ip"] == "172.31.254.1"
    )


@pytest.mark.skipif(sys.platform.startswith("win"), reason="not supporting genie on windows")
def test_response_parse_genie_fail():
    response = Response("localhost", channel_input="show ip arp", genie_platform="iosxe")
    response_str = ""
    response._record_response(response_str)
    assert response.genie_parse_output() == []
