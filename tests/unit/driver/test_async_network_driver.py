from pathlib import Path

import pytest

import scrapli
from scrapli.channel import AsyncChannel
from scrapli.driver.core import AsyncIOSXEDriver
from scrapli.exceptions import ScrapliTimeout
from scrapli.transport import AsyncTransport

from ...test_data.unit_test_cases import TEST_CASES

TEST_DATA_DIR = f"{Path(scrapli.__file__).parents[1]}/tests/test_data"


def test_check_kwargs_comms_prompt_pattern():
    with pytest.warns(UserWarning) as warn:
        conn = AsyncIOSXEDriver(
            host="localhost", transport="asyncssh", comms_prompt_pattern="something"
        )
    assert (
        conn.comms_prompt_pattern
        == "(^[a-z0-9.\\-_@()/:]{1,63}>$)|(^[a-z0-9.\\-_@/:]{1,63}#$)|(^[a-z0-9.\\-_@/:]{1,63}\\([a-z0-9.\\-@/:\\+]{"
        "0,32}\\)#$)"
    )
    assert (
        str(warn[0].message) == "\n***** `comms_prompt_pattern` found in kwargs! "
        "*****************************************\n`comms_prompt_pattern` is ignored (dropped) when using network "
        "drivers. If you wish to modify the patterns for any network driver sub-classes, please do so by modifying "
        "or providing your own `privilege_levels`.\n***** `comms_prompt_pattern` found in kwargs! "
        "*****************************************"
    )


@pytest.mark.asyncio
async def test_init(async_cisco_iosxe_conn):
    """Test that all arguments get properly passed from driver/transport to channel on init"""
    assert isinstance(async_cisco_iosxe_conn.channel.transport, AsyncTransport)
    assert isinstance(async_cisco_iosxe_conn.channel, AsyncChannel)
    assert async_cisco_iosxe_conn.auth_secondary == "scrapli"
    assert list(async_cisco_iosxe_conn.privilege_levels.keys()) == [
        "exec",
        "privilege_exec",
        "configuration",
    ]
    assert async_cisco_iosxe_conn.default_desired_privilege_level == "privilege_exec"
    assert async_cisco_iosxe_conn.textfsm_platform == "cisco_iosxe"
    assert async_cisco_iosxe_conn.genie_platform == "iosxe"
    assert async_cisco_iosxe_conn.failed_when_contains == [
        "% Ambiguous command",
        "% Incomplete command",
        "% Invalid input detected",
        "% Unknown command",
    ]


@pytest.mark.asyncio
async def test_escalate(async_cisco_iosxe_conn):
    expected_prompt_privilege_exec = TEST_CASES["cisco_iosxe"]["test_get_prompt"]["privilege_exec"]
    expected_prompt_configuration = TEST_CASES["cisco_iosxe"]["test_get_prompt"]["configuration"]
    await async_cisco_iosxe_conn.open()
    assert async_cisco_iosxe_conn._current_priv_level.name == "privilege_exec"
    assert await async_cisco_iosxe_conn.get_prompt() == expected_prompt_privilege_exec
    await async_cisco_iosxe_conn._escalate(
        escalate_priv=async_cisco_iosxe_conn.privilege_levels["configuration"]
    )
    assert await async_cisco_iosxe_conn.get_prompt() == expected_prompt_configuration


@pytest.mark.asyncio
async def test_deescalate(async_cisco_iosxe_conn):
    expected_prompt_privilege_exec = TEST_CASES["cisco_iosxe"]["test_get_prompt"]["privilege_exec"]
    expected_prompt_exec = TEST_CASES["cisco_iosxe"]["test_get_prompt"]["exec"]
    await async_cisco_iosxe_conn.open()
    assert async_cisco_iosxe_conn._current_priv_level.name == "privilege_exec"
    assert await async_cisco_iosxe_conn.get_prompt() == expected_prompt_privilege_exec
    await async_cisco_iosxe_conn._deescalate(
        current_priv=async_cisco_iosxe_conn.privilege_levels["privilege_exec"]
    )
    assert await async_cisco_iosxe_conn.get_prompt() == expected_prompt_exec


@pytest.mark.asyncio
async def test_acquire_priv(async_cisco_iosxe_conn):
    expected_prompt_privilege_exec = TEST_CASES["cisco_iosxe"]["test_get_prompt"]["privilege_exec"]
    expected_prompt_exec = TEST_CASES["cisco_iosxe"]["test_get_prompt"]["exec"]
    expected_prompt_configuration = TEST_CASES["cisco_iosxe"]["test_get_prompt"]["configuration"]
    await async_cisco_iosxe_conn.open()
    assert async_cisco_iosxe_conn._current_priv_level.name == "privilege_exec"
    assert await async_cisco_iosxe_conn.get_prompt() == expected_prompt_privilege_exec
    await async_cisco_iosxe_conn.acquire_priv(desired_priv="exec")
    assert async_cisco_iosxe_conn._current_priv_level.name == "exec"
    assert await async_cisco_iosxe_conn.get_prompt() == expected_prompt_exec
    await async_cisco_iosxe_conn.acquire_priv(desired_priv="configuration")
    assert async_cisco_iosxe_conn._current_priv_level.name == "configuration"
    assert await async_cisco_iosxe_conn.get_prompt() == expected_prompt_configuration


@pytest.mark.asyncio
async def test_send_command_not_desired_priv_level(async_cisco_iosxe_conn):
    expected_prompt_privilege_exec = TEST_CASES["cisco_iosxe"]["test_get_prompt"]["privilege_exec"]
    await async_cisco_iosxe_conn.open()
    await async_cisco_iosxe_conn.send_command(command="terminal length 0")
    await async_cisco_iosxe_conn.acquire_priv(desired_priv="exec")
    await async_cisco_iosxe_conn.send_command(command="show version")
    _ = await async_cisco_iosxe_conn.send_command(command="show version")
    assert async_cisco_iosxe_conn._current_priv_level.name == "privilege_exec"
    assert await async_cisco_iosxe_conn.get_prompt() == expected_prompt_privilege_exec


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "strip_prompt",
    [True, False],
    ids=["strip_prompt", "no_strip_prompt"],
)
async def test_send_command(async_cisco_iosxe_conn, strip_prompt):
    expected_raw = TEST_CASES["cisco_iosxe"]["test_send_input"]["raw_result"]
    expected_processed = (
        TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["strip"]
        if strip_prompt
        else TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["no_strip"]
    )
    await async_cisco_iosxe_conn.open()
    await async_cisco_iosxe_conn.send_command(command="terminal length 0")
    response = await async_cisco_iosxe_conn.send_command(
        command="show version", strip_prompt=strip_prompt
    )
    assert response.raw_result == expected_raw.encode()
    assert response.result == expected_processed


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "strip_prompt",
    [True, False],
    ids=["strip_prompt", "no_strip_prompt"],
)
async def test_send_commands(async_cisco_iosxe_conn, strip_prompt):
    expected_raw = TEST_CASES["cisco_iosxe"]["test_send_input"]["raw_result"]
    expected_processed = (
        TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["strip"]
        if strip_prompt
        else TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["no_strip"]
    )
    await async_cisco_iosxe_conn.open()
    multi_response = await async_cisco_iosxe_conn.send_commands(
        commands=["terminal length 0", "show version"], strip_prompt=strip_prompt
    )
    assert multi_response[1].raw_result == expected_raw.encode()
    assert multi_response[1].result == expected_processed


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "strip_prompt",
    [True, False],
    ids=["strip_prompt", "no_strip_prompt"],
)
async def test_send_commands_from_file(async_cisco_iosxe_conn, strip_prompt):
    expected_raw = TEST_CASES["cisco_iosxe"]["test_send_input"]["raw_result"]
    expected_processed = (
        TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["strip"]
        if strip_prompt
        else TEST_CASES["cisco_iosxe"]["test_send_input"]["processed_result"]["no_strip"]
    )
    await async_cisco_iosxe_conn.open()
    await async_cisco_iosxe_conn.send_command(command="terminal length 0")
    multi_response = await async_cisco_iosxe_conn.send_commands_from_file(
        file=f"{TEST_DATA_DIR}/files/cisco_iosxe_commands", strip_prompt=strip_prompt
    )
    assert multi_response[0].raw_result == expected_raw.encode()
    assert multi_response[0].result == expected_processed


@pytest.mark.asyncio
async def test_send_interactive(async_cisco_iosxe_conn):
    expected_raw = TEST_CASES["cisco_iosxe"]["test_send_inputs_interact"]["raw_result"]
    expected_processed = TEST_CASES["cisco_iosxe"]["test_send_inputs_interact"]["processed_result"]
    interact_events = TEST_CASES["cisco_iosxe"]["test_send_inputs_interact"]["interact_events"]
    await async_cisco_iosxe_conn.open()
    response = await async_cisco_iosxe_conn.send_interactive(interact_events=interact_events)
    assert expected_raw.encode() in response.raw_result
    assert expected_processed in response.result


@pytest.mark.asyncio
async def test_get_prompt(async_cisco_iosxe_conn):
    expected_prompt = TEST_CASES["cisco_iosxe"]["test_get_prompt"]["privilege_exec"]
    await async_cisco_iosxe_conn.open()
    found_prompt = await async_cisco_iosxe_conn.get_prompt()
    assert found_prompt == expected_prompt


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "auth_secondary",
    [("scrapli", True), ("", False)],
    ids=["auth_secondary_provided", "auth_secondary_missed"],
)
async def test_auth_required_no_auth_secondary(async_cisco_iosxe_conn, auth_secondary):
    async_cisco_iosxe_conn.auth_secondary = auth_secondary[0]
    await async_cisco_iosxe_conn.open()
    await async_cisco_iosxe_conn.acquire_priv(desired_priv="exec")

    if auth_secondary[1] is False:
        async_cisco_iosxe_conn.channel.timeout_ops = 1
        with pytest.warns(UserWarning), pytest.raises(ScrapliTimeout):
            # makes sure we raise a user warning if auth is required for priv escalation
            # this will also fail because the mock ssh server requires a password
            await async_cisco_iosxe_conn.acquire_priv(desired_priv="privilege_exec")
    else:
        await async_cisco_iosxe_conn.acquire_priv(desired_priv="privilege_exec")
