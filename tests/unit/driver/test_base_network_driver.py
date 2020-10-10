from pathlib import Path

import pytest

import scrapli
from scrapli.driver.base_network_driver import PrivilegeAction, PrivilegeLevel
from scrapli.driver.core import IOSXEDriver
from scrapli.exceptions import UnknownPrivLevel
from scrapli.response import MultiResponse, Response

TEST_DATA_DIR = f"{Path(scrapli.__file__).parents[1]}/tests/test_data/"


def test_check_kwargs_comms_prompt_pattern():
    with pytest.warns(UserWarning) as warn:
        conn = IOSXEDriver(host="localhost", comms_prompt_pattern="something")
    assert (
        conn.comms_prompt_pattern
        == r"(^[a-z0-9.\-_@()/:]{1,63}>$)|(^[a-z0-9.\-_@/:]{1,63}#$)|(^[a-z0-9.\-_@/:]{1,63}\([a-z0-9.\-@/:\+]{"
        "0,32}\\)#$)"
    )
    assert (
        str(warn[0].message) == "\n***** `comms_prompt_pattern` found in kwargs! "
        "*****************************************\n`comms_prompt_pattern` is ignored (dropped) when using network "
        "drivers. If you wish to modify the patterns for any network driver sub-classes, please do so by modifying "
        "or providing your own `privilege_levels`.\n***** `comms_prompt_pattern` found in kwargs! "
        "*****************************************"
    )


def test_generate_comms_prompt_pattern(sync_cisco_iosxe_conn):
    assert (
        sync_cisco_iosxe_conn.comms_prompt_pattern
        == "(^[a-z0-9.\\-_@()/:]{1,63}>$)|(^[a-z0-9.\\-_@/:]{1,63}#$)|(^[a-z0-9.\\-_@/:]{1,63}\\([a-z0-9.\\-@/:\\+]{0,32}\\)#$)"
    )


def test_build_priv_map(sync_cisco_iosxe_conn):
    assert sync_cisco_iosxe_conn._priv_map == {
        "exec": ["exec"],
        "privilege_exec": ["exec", "privilege_exec"],
        "configuration": ["exec", "privilege_exec", "configuration"],
    }


def test_update_privilege_levels(sync_cisco_iosxe_conn):
    sync_cisco_iosxe_conn.privilege_levels["scrapli"] = PrivilegeLevel(
        pattern=r"^weirdpatterndude$",
        name="scrapli",
        previous_priv="",
        deescalate="",
        escalate="",
        escalate_auth=False,
        escalate_prompt="",
    )
    sync_cisco_iosxe_conn.update_privilege_levels()
    assert (
        sync_cisco_iosxe_conn.comms_prompt_pattern
        == r"(^[a-z0-9.\-_@()/:]{1,63}>$)|(^[a-z0-9.\-_@/:]{1,63}#$)|(^[a-z0-9.\-_@/:]{1,63}\([a-z0-9.\-@/:\+]{0,32}\)#$)|(^weirdpatterndude$)"
    )
    assert sync_cisco_iosxe_conn._priv_map == {
        "exec": ["exec"],
        "privilege_exec": ["exec", "privilege_exec"],
        "configuration": ["exec", "privilege_exec", "configuration"],
        "scrapli": ["scrapli"],
    }


def test_determine_current_priv_exceptions(sync_cisco_iosxe_conn):
    with pytest.raises(UnknownPrivLevel):
        sync_cisco_iosxe_conn._determine_current_priv("!!!!thisissoooowrongggg!!!!!!?!")


def test_determine_current_priv(sync_cisco_iosxe_conn):
    current_priv = sync_cisco_iosxe_conn._determine_current_priv("execprompt>")
    assert len(current_priv) == 1
    assert current_priv[0] == "exec"


def test_get_privilege_level_name_exceptions(sync_cisco_iosxe_conn):
    with pytest.raises(UnknownPrivLevel) as exc:
        sync_cisco_iosxe_conn._get_privilege_level_name(requested_priv="boo")
    assert (
        str(exc.value)
        == "Requested privilege level `boo` not a valid privilege level of `IOSXEDriver`"
    )


def test_get_privilege_level_name(sync_cisco_iosxe_conn):
    resolved_privilege_level = sync_cisco_iosxe_conn._get_privilege_level_name(
        requested_priv="exec"
    )
    assert resolved_privilege_level == "exec"


def test_update_response(sync_cisco_iosxe_conn):
    response = Response("localhost", "some input")
    sync_cisco_iosxe_conn.textfsm_platform = "racecar"
    sync_cisco_iosxe_conn.genie_platform = "tacocat"
    sync_cisco_iosxe_conn._update_response(response)
    assert response.textfsm_platform == "racecar"
    assert response.genie_platform == "tacocat"


def test_register_configuration_session(sync_cisco_iosxe_conn):
    with pytest.raises(NotImplementedError) as exc:
        sync_cisco_iosxe_conn.register_configuration_session(session_name="boo")
    assert str(exc.value) == "Configuration sessions not supported for `IOSXEDriver`"


def test_pre_escalate():
    with pytest.warns(UserWarning) as warn:
        conn = IOSXEDriver(host="localhost", comms_prompt_pattern="something", auth_secondary="")
        conn._pre_escalate(escalate_priv=conn.privilege_levels["privilege_exec"])
    assert (
        str(warn[1].message)
        == "\n***** Privilege escalation generally requires an `auth_secondary` password, but none is set! \nscrapli will try to escalate privilege without entering a password but may fail.\nSet an `auth_secondary` password if your device requires a password to increase privilege, otherwise ignore this message.\n***** Privilege escalation generally requires an `auth_secondary` password, but none is set! "
    )


def test_pre_acquire_priv(sync_cisco_iosxe_conn):
    resolved_priv, map_to_desired_priv = sync_cisco_iosxe_conn._pre_acquire_priv(
        desired_priv="configuration"
    )
    assert resolved_priv == "configuration"
    assert map_to_desired_priv == ["exec", "privilege_exec", "configuration"]


def test_process_acquire_priv_escalate(sync_cisco_iosxe_conn):
    privilege_action, priv = sync_cisco_iosxe_conn._process_acquire_priv(
        resolved_priv="configuration",
        map_to_desired_priv=["exec", "privilege_exec", "configuration"],
        current_prompt="csr1000v#",
    )
    assert privilege_action == PrivilegeAction.ESCALATE


def test_process_acquire_priv_deescalate(sync_cisco_iosxe_conn):
    privilege_action, priv = sync_cisco_iosxe_conn._process_acquire_priv(
        resolved_priv="exec",
        map_to_desired_priv=["exec", "privilege_exec", "configuration"],
        current_prompt="csr1000v#",
    )
    assert privilege_action == PrivilegeAction.DEESCALATE


def test_process_acquire_priv_no_action(sync_cisco_iosxe_conn):
    privilege_action, priv = sync_cisco_iosxe_conn._process_acquire_priv(
        resolved_priv="privilege_exec",
        map_to_desired_priv=["exec", "privilege_exec", "configuration"],
        current_prompt="csr1000v#",
    )
    assert privilege_action == PrivilegeAction.NO_ACTION


def test_pre_send_config_exceptions(sync_cisco_iosxe_conn):
    with pytest.raises(TypeError) as exc:
        sync_cisco_iosxe_conn._pre_send_config(config=["boo"])
    assert (
        str(exc.value)
        == "`send_config` expects a single string, got <class 'list'>, to send a list of configs use the `send_configs` method instead."
    )


def test_pre_send_config(sync_cisco_iosxe_conn):
    split_configs = sync_cisco_iosxe_conn._pre_send_config(
        config="interface loopback0\ndescription scrapli is neat"
    )
    assert isinstance(split_configs, list)
    assert split_configs[0] == "interface loopback0"
    assert split_configs[1] == "description scrapli is neat"


def test_post_send_config(sync_cisco_iosxe_conn):
    response_one = Response("localhost", "some input", failed_when_contains=["something"])
    response_one._record_response(result=b"greatsucccess")
    response_two = Response("localhost", "some input")
    response_two._record_response(result=b"alsosucess")
    multi_response = MultiResponse()
    multi_response.append(response_one)
    multi_response.append(response_two)
    unified_response = sync_cisco_iosxe_conn._post_send_config(
        config="interface loopback0\ndescription scrapli is neat", multi_response=multi_response
    )
    assert unified_response.failed is False
    assert unified_response.result == "greatsucccess\nalsosucess"


def test_pre_send_configs_exceptions(sync_cisco_iosxe_conn):
    with pytest.raises(TypeError) as exc:
        sync_cisco_iosxe_conn._pre_send_configs(configs="boo")
    assert (
        str(exc.value)
        == "`send_configs` expects a list of strings, got <class 'str'>, to send a single configuration line/string use the `send_config` method instead."
    )


def test_pre_send_configs_standard(sync_cisco_iosxe_conn):
    resolved_privilege_level, failed_when_contains = sync_cisco_iosxe_conn._pre_send_configs(
        configs=[]
    )
    assert resolved_privilege_level == "configuration"
    assert failed_when_contains == [
        "% Ambiguous command",
        "% Incomplete command",
        "% Invalid input detected",
        "% Unknown command",
    ]


def test_pre_send_configs_user_defined(sync_cisco_iosxe_conn):
    resolved_privilege_level, failed_when_contains = sync_cisco_iosxe_conn._pre_send_configs(
        configs=[], privilege_level="privilege_exec", failed_when_contains=["somethingneat"]
    )
    assert resolved_privilege_level == "privilege_exec"
    assert failed_when_contains == ["somethingneat"]


def test_post_send_configs(sync_cisco_iosxe_conn):
    response_one = Response("localhost", "some input", failed_when_contains=["something"])
    response_one._record_response(result=b"greatsucccess")
    multi_response = MultiResponse()
    multi_response.append(response_one)
    updated_responses = sync_cisco_iosxe_conn._post_send_configs(responses=multi_response)
    assert updated_responses[0].textfsm_platform == "cisco_iosxe"
    assert updated_responses[0].genie_platform == "iosxe"


def test_pre_send_configs_from_file_exceptions(sync_cisco_iosxe_conn):
    with pytest.raises(TypeError) as exc:
        sync_cisco_iosxe_conn._pre_send_configs_from_file(file=["boo"])
    assert (
        str(exc.value)
        == "`send_configs_from_file` expects a string path to a file, got <class 'list'>"
    )


def test_pre_send_configs_from_file(sync_cisco_iosxe_conn):
    configs = sync_cisco_iosxe_conn._pre_send_configs_from_file(
        file=f"{TEST_DATA_DIR}/files/vrnetlab_key"
    )
    assert configs[0] == "-----BEGIN OPENSSH PRIVATE KEY-----"
    assert configs[-1] == "-----END OPENSSH PRIVATE KEY-----"
