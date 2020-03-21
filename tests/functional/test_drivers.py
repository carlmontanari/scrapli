import time

import pytest

from scrapli.exceptions import ScrapliAuthenticationFailed

from .test_data.devices import DEVICES, INVALID_PRIVATE_KEY, PRIVATE_KEY
from .test_data.test_cases import TEST_CASES


class TestDevice:
    def test_get_prompt(self, nix_conn, transport):
        prompt = nix_conn.channel.get_prompt()
        assert prompt == TEST_CASES["linux"]["get_prompt"]

    @pytest.mark.parametrize(
        "strip_prompt", [True, False], ids=["strip_prompt", "no_strip_prompt"],
    )
    def test_send_command_short(self, nix_conn, transport, strip_prompt):
        command = TEST_CASES["linux"]["send_command_short"]["command"]
        expected_type = "expected_no_strip" if not strip_prompt else "expected_strip"
        expected_response = TEST_CASES["linux"]["send_command_short"][expected_type]
        response = nix_conn.channel.send_input(channel_input=command, strip_prompt=strip_prompt)
        assert response.result == expected_response

    @pytest.mark.parametrize(
        "strip_prompt", [True, False], ids=["strip_prompt", "no_strip_prompt"],
    )
    def test_send_command_long(self, nix_conn, transport, strip_prompt):
        command = TEST_CASES["linux"]["send_command_long"]["command"]
        expected_type = "expected_no_strip" if not strip_prompt else "expected_strip"
        expected_response = TEST_CASES["linux"]["send_command_long"][expected_type]
        response = nix_conn.channel.send_input(channel_input=command, strip_prompt=strip_prompt)
        assert response.result == expected_response

    @pytest.mark.parametrize(
        "strip_prompt", [True, False], ids=["strip_prompt", "no_strip_prompt"],
    )
    def test_send_commands(self, nix_conn, transport, strip_prompt):
        commands = []
        expected_responses = []
        commands.append(TEST_CASES["linux"]["send_command_short"]["command"])
        commands.append(TEST_CASES["linux"]["send_command_long"]["command"])
        expected_type = "expected_no_strip" if not strip_prompt else "expected_strip"
        expected_responses.append(TEST_CASES["linux"]["send_command_short"][expected_type])
        expected_responses.append(TEST_CASES["linux"]["send_command_long"][expected_type])
        responses = nix_conn.channel.send_inputs(channel_inputs=commands, strip_prompt=strip_prompt)
        for expected_response, response in zip(expected_responses, responses):
            assert response.result == expected_response

    def test_isalive_and_close(self, nix_conn, transport):
        assert nix_conn.isalive() is True
        nix_conn.close()
        # unsure why but w/out a tiny sleep pytest just plows ahead and the connection doesnt
        # close in time for the next assert
        time.sleep(0.1)
        assert nix_conn.isalive() is False


class TestNetworkDevice:
    @pytest.mark.parametrize(
        "priv_level",
        ["exec", "privilege_exec", "configuration"],
        ids=["exec", "privilege_exec", "configuration"],
    )
    def test_get_prompt_and_acquire_priv(self, conn, priv_level, device_type, transport):
        if TEST_CASES[device_type]["get_prompt"][priv_level] is None:
            pytest.skip(f"Priv level {priv_level} for device type {device_type} not tested")
        conn.acquire_priv(priv_level)
        prompt = conn.get_prompt()
        assert prompt == TEST_CASES[device_type]["get_prompt"][priv_level]

    @pytest.mark.parametrize(
        "strip_prompt", [True, False], ids=["strip_prompt", "no_strip_prompt"],
    )
    def test_send_command_short(self, conn, device_type, transport, strip_prompt):
        command = TEST_CASES[device_type]["send_command_short"]["command"]
        expected_type = "expected_no_strip" if not strip_prompt else "expected_strip"
        expected_response = TEST_CASES[device_type]["send_command_short"][expected_type]
        sanitize_response = TEST_CASES[device_type]["sanitize_response"]
        response = conn.send_command(command=command, strip_prompt=strip_prompt)
        assert sanitize_response(response.result) == expected_response

    @pytest.mark.parametrize(
        "strip_prompt", [True, False], ids=["strip_prompt", "no_strip_prompt"],
    )
    def test_send_command_long(self, conn, device_type, transport, strip_prompt):
        command = TEST_CASES[device_type]["send_command_long"]["command"]
        expected_type = "expected_no_strip" if not strip_prompt else "expected_strip"
        expected_response = TEST_CASES[device_type]["send_command_long"][expected_type]
        sanitize_response = TEST_CASES[device_type]["sanitize_response"]
        response = conn.send_command(command=command, strip_prompt=strip_prompt)
        assert sanitize_response(response.result) == expected_response

    @pytest.mark.parametrize(
        "strip_prompt", [True, False], ids=["strip_prompt", "no_strip_prompt"],
    )
    def test_send_commands(self, conn, device_type, transport, strip_prompt):
        commands = []
        expected_responses = []
        commands.append(TEST_CASES[device_type]["send_command_short"]["command"])
        commands.append(TEST_CASES[device_type]["send_command_long"]["command"])
        expected_type = "expected_no_strip" if not strip_prompt else "expected_strip"
        expected_responses.append(TEST_CASES[device_type]["send_command_short"][expected_type])
        expected_responses.append(TEST_CASES[device_type]["send_command_long"][expected_type])
        sanitize_response = TEST_CASES[device_type]["sanitize_response"]
        responses = conn.send_commands(commands=commands, strip_prompt=strip_prompt)
        for expected_response, response in zip(expected_responses, responses):
            assert sanitize_response(response.result) == expected_response

    def test_send_interactive_normal_response(self, conn, device_type, transport):
        if TEST_CASES[device_type]["send_interactive_normal_response"] is None:
            pytest.skip(
                f"send_interactive_normal_response for device type {device_type} not tested"
            )
        interact = TEST_CASES[device_type]["send_interactive_normal_response"]["command"]
        expected_response = TEST_CASES[device_type]["send_interactive_normal_response"]["expected"]
        response = conn.send_interactive(interact=interact)
        assert response.result == expected_response

    def test_send_interactive_hidden_response(self, conn, device_type, transport):
        if TEST_CASES[device_type]["send_interactive_hidden_response"] is None:
            pytest.skip(
                f"send_interactive_hidden_response for device type {device_type} not tested"
            )
        interact = TEST_CASES[device_type]["send_interactive_hidden_response"]["command"]
        expected_response = TEST_CASES[device_type]["send_interactive_hidden_response"]["expected"]
        response = conn.send_interactive(interact=interact)
        assert response.result == expected_response

    @pytest.mark.parametrize(
        "strip_prompt", [True, False], ids=["strip_prompt", "no_strip_prompt"],
    )
    def test_send_configs(self, conn, device_type, transport, strip_prompt):
        configs = TEST_CASES[device_type]["send_configs"]["configs"]
        expected_type = "expected_no_strip" if not strip_prompt else "expected_strip"
        expected_responses = TEST_CASES[device_type]["send_configs"][expected_type]
        verification = TEST_CASES[device_type]["send_configs"]["verification"]
        expected_verification = TEST_CASES[device_type]["send_configs"][
            f"verification_{expected_type}"
        ]
        teardown_configs = TEST_CASES[device_type]["send_configs"]["teardown_configs"]
        sanitize_response = TEST_CASES[device_type]["sanitize_response"]
        responses = conn.send_configs(configs=configs, strip_prompt=strip_prompt)
        for expected_response, response in zip(expected_responses, responses):
            assert response.result == expected_response
        verification_response = conn.send_command(command=verification, strip_prompt=strip_prompt)
        assert sanitize_response(verification_response.result) == expected_verification
        conn.send_configs(configs=teardown_configs)

    def test_isalive_and_close(self, conn, device_type, transport):
        assert conn.isalive() is True
        conn.close()
        # unsure why but w/out a tiny sleep pytest just plows ahead and the connection doesnt
        # close in time for the next assert
        time.sleep(0.1)
        assert conn.isalive() is False


def test_context_manager(device_type, transport):
    if device_type == "arista_eos" and transport == "ssh2":
        pytest.skip(
            "SSH2 (on pypi) doesn't support keyboard interactive auth, skipping ssh2 for arista_eos testing"
        )

    device = DEVICES[device_type].copy()
    driver = device.pop("driver")
    device.pop("base_config")

    port = 22
    if transport == "telnet":
        port = 23

    device["port"] = port
    device["transport"] = transport
    device["timeout_socket"] = 2
    device["timeout_transport"] = 2
    device["timeout_ops"] = 2

    with driver(**device) as conn:
        assert conn.isalive() is True
    # unsure why but w/out a tiny sleep pytest just plows ahead and the connection doesnt
    # close in time for the next assert
    time.sleep(0.1)
    assert conn.isalive() is False


def test_public_key_auth(device_type, transport):
    if device_type != "cisco_iosxe" or transport == "telnet":
        pytest.skip("public key auth only tested against iosxe at the moment, and never on telnet!")

    device = DEVICES[device_type].copy()
    driver = device.pop("driver")
    device.pop("base_config")

    device["transport"] = transport
    device["timeout_socket"] = 2
    device["timeout_transport"] = 2
    device["timeout_ops"] = 2
    device["auth_private_key"] = PRIVATE_KEY

    with driver(**device) as conn:
        assert conn.isalive() is True
    # unsure why but w/out a tiny sleep pytest just plows ahead and the connection doesnt
    # close in time for the next assert
    time.sleep(0.1)
    assert conn.isalive() is False


def test_public_key_auth_failure(device_type, transport):
    if device_type != "cisco_iosxe" or transport == "telnet":
        pytest.skip("public key auth only tested against iosxe at the moment, and never on telnet!")

    device = DEVICES[device_type].copy()
    driver = device.pop("driver")
    device.pop("base_config")

    device["transport"] = transport
    device["timeout_socket"] = 2
    device["timeout_transport"] = 2
    device["timeout_ops"] = 2
    device["auth_private_key"] = INVALID_PRIVATE_KEY
    device.pop("auth_password")
    conn = driver(**device)

    with pytest.raises(ScrapliAuthenticationFailed) as exc:
        conn.open()
    assert str(exc.value) == (
        f"Public key authentication to host {device['host']} failed. Missing username or "
        "password unable to attempt password authentication."
    )
