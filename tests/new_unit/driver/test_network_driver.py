from pathlib import Path

import pytest

import scrapli
from scrapli.channel import Channel
from scrapli.driver.core import IOSXEDriver
from scrapli.transport import Transport

from ...test_data.unit_test_cases import TEST_CASES

TEST_DATA_DIR = f"{Path(scrapli.__file__).parents[1]}/tests/test_data"


def test_check_kwargs_comms_prompt_pattern():
    with pytest.warns(UserWarning) as warn:
        conn = IOSXEDriver(host="localhost", comms_prompt_pattern="something")
    assert (
        conn.comms_prompt_pattern
        == "(^[a-z0-9.\\-@()/:]{1,32}>$)|(^[a-z0-9.\\-@/:]{1,32}#$)|(^[a-z0-9.\\-@/:]{1,32}\\(conf[a-z0-9.\\-@/:]{"
        "0,32}\\)#$)"
    )
    assert (
        str(warn[0].message) == "\n***** `comms_prompt_pattern` found in kwargs! "
        "*****************************************\n`comms_prompt_pattern` is ignored (dropped) when using network "
        "drivers. If you wish to modify the patterns for any network driver sub-classes, please do so by modifying "
        "or providing your own `privilege_levels`.\n***** `comms_prompt_pattern` found in kwargs! "
        "*****************************************"
    )


def test_init(sync_cisco_iosxe_conn):
    """Test that all arguments get properly passed from driver/transport to channel on init"""
    assert isinstance(sync_cisco_iosxe_conn.channel.transport, Transport)
    assert isinstance(sync_cisco_iosxe_conn.channel, Channel)
    assert sync_cisco_iosxe_conn.auth_secondary == "scrapli"
    assert list(sync_cisco_iosxe_conn.privilege_levels.keys()) == [
        "exec",
        "privilege_exec",
        "configuration",
    ]
    assert sync_cisco_iosxe_conn.default_desired_privilege_level == "privilege_exec"
    assert sync_cisco_iosxe_conn.textfsm_platform == "cisco_iosxe"
    assert sync_cisco_iosxe_conn.genie_platform == "iosxe"
    assert sync_cisco_iosxe_conn.failed_when_contains == [
        "% Ambiguous command",
        "% Incomplete command",
        "% Invalid input detected",
        "% Unknown command",
    ]


# def test_escalate(sync_cisco_iosxe_conn):
#     expected_prompt_privilege_exec = TEST_CASES["cisco_iosxe"]["test_get_prompt"]["privilege_exec"]
#     expected_prompt_configuration = TEST_CASES["cisco_iosxe"]["test_get_prompt"]["configuration"]
#     sync_cisco_iosxe_conn.open()
#     assert sync_cisco_iosxe_conn._current_priv_level.name == "privilege_exec"
#     assert sync_cisco_iosxe_conn.get_prompt() == expected_prompt_privilege_exec
#     sync_cisco_iosxe_conn._escalate(escalate_priv=sync_cisco_iosxe_conn.privilege_levels["configuration"])
#     assert sync_cisco_iosxe_conn._current_priv_level.name == "configuration"
#     assert sync_cisco_iosxe_conn.get_prompt() == expected_prompt_configuration
