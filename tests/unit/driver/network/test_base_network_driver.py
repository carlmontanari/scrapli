import pytest

from scrapli.driver.network.base_driver import PrivilegeAction
from scrapli.exceptions import ScrapliPrivilegeError, ScrapliTypeError
from scrapli.response import Response


def test_generate_comms_prompt_pattern(base_network_driver):
    assert base_network_driver.comms_prompt_pattern == r"^\S{0,48}[#>$~@:\]]\s*$"

    base_network_driver._generate_comms_prompt_pattern()

    assert (
        base_network_driver.comms_prompt_pattern
        == r"(^[a-z0-9.\-_@()/:]{1,63}>$)|(^[a-z0-9.\-_@/:]{1,63}#$)|(^["
        r"a-z0-9.\-_@/:]{1,63}\((?!tcl)[a-z0-9.\-@/:\+]{0,32}\)#$)|(("
        r"^[a-z0-9.\-_@/:]{1,63}\(tcl\)#$)|(^\+>$))"
    )


@pytest.mark.parametrize(
    "test_data",
    (("exec", "scrapli>"), ("privilege_exec", "scrapli#"), ("configuration", "scrapli(config)#")),
    ids=("priv1", "priv2", "priv3"),
)
def test_determine_current_priv(base_network_driver, test_data):
    priv_name, current_prompt = test_data

    assert (
        base_network_driver._determine_current_priv(current_prompt=current_prompt)[0] == priv_name
    )


def test_determine_current_priv_exception(base_network_driver):
    with pytest.raises(ScrapliPrivilegeError):
        base_network_driver._determine_current_priv(current_prompt="tacocat")


def test_build_priv_graph(base_network_driver):
    assert base_network_driver._priv_graph is None

    base_network_driver._build_priv_graph()

    assert dict(base_network_driver._priv_graph) == {
        "exec": {"privilege_exec"},
        "privilege_exec": {"exec", "configuration", "tclsh"},
        "configuration": {"privilege_exec"},
        "tclsh": {"privilege_exec"},
    }


@pytest.mark.parametrize(
    "test_data",
    (
        ("exec", "configuration", ["exec", "privilege_exec", "configuration"]),
        ("configuration", "exec", ["configuration", "privilege_exec", "exec"]),
        ("exec", "exec", ["exec"]),
    ),
    ids=("priv1", "priv2", "priv3"),
)
def test_build_priv_change_map(base_network_driver, test_data):
    starting_priv, destination_priv, expected_map = test_data
    base_network_driver._build_priv_graph()
    actual_map = base_network_driver._build_priv_change_map(
        starting_priv_name=starting_priv, destination_priv_name=destination_priv
    )

    assert actual_map == expected_map


def test_update_privilege_levels(base_network_driver):
    # create a dummy channel that will let us update prompt pattern since base network driver has
    # no channel attribute
    base_network_driver.channel = type("", (), {})()
    assert base_network_driver._priv_graph is None
    assert base_network_driver.comms_prompt_pattern == r"^\S{0,48}[#>$~@:\]]\s*$"

    base_network_driver.update_privilege_levels()

    assert (
        base_network_driver.comms_prompt_pattern
        == r"(^[a-z0-9.\-_@()/:]{1,63}>$)|(^[a-z0-9.\-_@/:]{1,63}#$)|(^["
        r"a-z0-9.\-_@/:]{1,63}\((?!tcl)[a-z0-9.\-@/:\+]{0,32}\)#$)|(("
        r"^[a-z0-9.\-_@/:]{1,63}\(tcl\)#$)|(^\+>$))"
    )
    assert (
        base_network_driver.channel.comms_prompt_pattern
        == r"(^[a-z0-9.\-_@()/:]{1,63}>$)|(^[a-z0-9.\-_@/:]{1,63}#$)|(^["
        r"a-z0-9.\-_@/:]{1,63}\((?!tcl)[a-z0-9.\-@/:\+]{0,32}\)#$)|(("
        r"^[a-z0-9.\-_@/:]{1,63}\(tcl\)#$)|(^\+>$))"
    )
    assert dict(base_network_driver._priv_graph) == {
        "exec": {"privilege_exec"},
        "privilege_exec": {"exec", "configuration", "tclsh"},
        "configuration": {"privilege_exec"},
        "tclsh": {"privilege_exec"},
    }


def test_validate_privilege_level_name_exception(base_network_driver):
    with pytest.raises(ScrapliPrivilegeError):
        base_network_driver._validate_privilege_level_name(privilege_level_name="tacocat")


def test_pre_escalate(base_network_driver):
    base_network_driver.auth_secondary = ""
    with pytest.warns(UserWarning):
        base_network_driver._pre_escalate(
            escalate_priv=base_network_driver.privilege_levels["privilege_exec"]
        )


@pytest.mark.parametrize(
    "test_data",
    (
        ("exec", "scrapli>", PrivilegeAction.NO_ACTION, "exec"),
        ("configuration", "scrapli>", PrivilegeAction.ESCALATE, "privilege_exec"),
        ("exec", "scrapli(config)#", PrivilegeAction.DEESCALATE, "configuration"),
    ),
    ids=("priv1", "priv2", "priv3"),
)
def test_process_acquire_priv(base_network_driver, test_data):
    base_network_driver.channel = type("", (), {})()
    base_network_driver.update_privilege_levels()
    destination_priv, current_prompt, expected_action, action_priv = test_data

    actual_action, current_priv = base_network_driver._process_acquire_priv(
        destination_priv=destination_priv, current_prompt=current_prompt
    )

    assert actual_action == expected_action
    assert current_priv.name == action_priv


def test_update_response(base_network_driver):
    response = Response(host="localhost", channel_input="nothing")
    base_network_driver._update_response(response=response)
    assert response.textfsm_platform == "cisco_iosxe"
    assert response.genie_platform == "cisco_iosxe"


def test_pre_send_config(base_network_driver):
    config = "int loopback123\ndes tacocat"
    actual_configs = base_network_driver._pre_send_config(config=config)
    assert actual_configs == ["int loopback123", "des tacocat"]


def test_pre_send_config_exception(base_network_driver):
    with pytest.raises(ScrapliTypeError):
        base_network_driver._pre_send_config(config=None)


def test_post_send_config(base_network_driver):
    responses = [
        Response(host="localhost", channel_input="nothing1"),
        Response(host="localhost", channel_input="nothing2"),
    ]
    for response in responses:
        response.record_response(result=b"nada")
    responses[0].failed = True
    actual_response = base_network_driver._post_send_config(
        multi_response=responses, config="nothing1\nnothing2"
    )
    assert actual_response.result == "nada\nnada"
    assert actual_response.failed is True


def test_pre_send_configs(base_network_driver):
    actual_resolved_privilege_level, _ = base_network_driver._pre_send_configs(
        configs=["some config"], privilege_level="exec"
    )
    assert actual_resolved_privilege_level == "exec"


def test_pre_send_configs_list_failed_when_contains(base_network_driver):
    _, final_failed_when_contains = base_network_driver._pre_send_configs(
        configs=["some config"], failed_when_contains=["something"]
    )
    assert final_failed_when_contains == ["something"]


def test_pre_send_configs_string_failed_when_contains(base_network_driver):
    _, final_failed_when_contains = base_network_driver._pre_send_configs(
        configs=["some config"], failed_when_contains="something"
    )
    assert final_failed_when_contains == ["something"]


def test_pre_send_configs_driver_failed_when_contains(base_network_driver):
    base_network_driver.failed_when_contains = ["something"]
    _, final_failed_when_contains = base_network_driver._pre_send_configs(configs=["some config"])
    assert final_failed_when_contains == ["something"]


def test_pre_send_configs_exception(base_network_driver):
    with pytest.raises(ScrapliTypeError):
        base_network_driver._pre_send_configs(configs=None)


def test_post_send_configs(base_network_driver):
    responses = [Response(host="localhost", channel_input="nothing")]
    base_network_driver._post_send_configs(responses=responses)
    assert responses[0].textfsm_platform == "cisco_iosxe"
    assert responses[0].genie_platform == "cisco_iosxe"
