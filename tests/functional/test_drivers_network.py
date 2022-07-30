import time

import pytest
from expected import get_expected, write_expected

from scrapli.exceptions import ScrapliAuthenticationFailed


class TestNetworkDevice:
    @pytest.fixture(autouse=True)
    def __setup(self, test_cases):
        self.test_cases = test_cases

    @pytest.mark.parametrize(
        "priv_level",
        ["exec", "privilege_exec", "configuration"],
        ids=["exec", "privilege_exec", "configuration"],
    )
    def test_get_prompt_and_acquire_priv(self, conn, priv_level, device_type, transport, update):
        if (device_type in ("cisco_nxos", "cisco_iosxr") and priv_level == "exec") or (
            device_type == "juniper_junos" and priv_level == "privilege_exec"
        ):
            pytest.skip(f"Priv level {priv_level} for device type {device_type} not tested")

        conn.acquire_priv(priv_level)
        actual = conn.get_prompt()

        if update:
            write_expected(f=__file__, result=actual)

        assert actual == get_expected(f=__file__)

    @pytest.mark.parametrize(
        "strip_prompt",
        [True, False],
        ids=["strip_prompt", "no_strip_prompt"],
    )
    def test_send_command_short(self, conn, device_type, transport, strip_prompt, update):
        command = self.test_cases[device_type]["send_command_short"]["command"]
        sanitize_response = self.test_cases[device_type]["sanitize_response"]

        response = conn.send_command(command=command, strip_prompt=strip_prompt)

        actual = sanitize_response(response.result)

        if update:
            write_expected(f=__file__, result=actual)

        assert actual == get_expected(f=__file__)

    @pytest.mark.parametrize(
        "strip_prompt",
        [True, False],
        ids=["strip_prompt", "no_strip_prompt"],
    )
    def test_send_command_long(self, conn, device_type, transport, strip_prompt, update):
        command = self.test_cases[device_type]["send_command_long"]["command"]
        sanitize_response = self.test_cases[device_type]["sanitize_response"]

        response = conn.send_command(command=command, strip_prompt=strip_prompt)

        actual = sanitize_response(response.result)

        if update:
            write_expected(f=__file__, result=actual)

        assert actual == get_expected(f=__file__)

    @pytest.mark.parametrize(
        "strip_prompt",
        [True, False],
        ids=["strip_prompt", "no_strip_prompt"],
    )
    def test_send_commands(self, conn, device_type, transport, strip_prompt, update):
        commands = [
            self.test_cases[device_type]["send_command_short"]["command"],
            self.test_cases[device_type]["send_command_long"]["command"],
        ]
        sanitize_response = self.test_cases[device_type]["sanitize_response"]

        response = conn.send_commands(commands=commands, strip_prompt=strip_prompt)

        actual = sanitize_response(response.result)

        if update:
            write_expected(f=__file__, result=actual)

        assert actual == get_expected(f=__file__)

    @pytest.mark.parametrize(
        "strip_prompt",
        [True, False],
        ids=["strip_prompt", "no_strip_prompt"],
    )
    def test_send_commands_from_file(self, conn, device_type, transport, strip_prompt, update):
        file = self.test_cases[device_type]["send_commands_from_file"]["file"]
        sanitize_response = self.test_cases[device_type]["sanitize_response"]

        response = conn.send_commands_from_file(file=file, strip_prompt=strip_prompt)

        actual = sanitize_response(response.result)

        if update:
            write_expected(f=__file__, result=actual)

        assert actual == get_expected(f=__file__)

    def test_send_commands_stop_on_failed(self, conn, device_type, transport):
        commands = self.test_cases[device_type]["send_commands_error"]["commands"]

        responses = conn.send_commands(commands=commands, stop_on_failed=True)

        assert len(responses) == 2
        assert responses[0].failed is False
        assert responses[1].failed is True

    def test_send_interactive_normal_response(self, conn, device_type, transport, update):
        if self.test_cases[device_type]["send_interactive_normal_response"] is None:
            pytest.skip(
                f"send_interactive_normal_response for device type {device_type} not tested"
            )
        interact = self.test_cases[device_type]["send_interactive_normal_response"]["command"]

        response = conn.send_interactive(interact_events=interact)

        actual = response.result

        if update:
            write_expected(f=__file__, result=actual)

        assert actual == get_expected(f=__file__)

    @pytest.mark.parametrize(
        "strip_prompt",
        [True, False],
        ids=["strip_prompt", "no_strip_prompt"],
    )
    def test_send_config(self, conn, device_type, transport, strip_prompt, update):
        config = self.test_cases[device_type]["send_config"]["configs"]
        teardown_configs = self.test_cases[device_type]["send_config"]["teardown_configs"]
        sanitize_response = self.test_cases[device_type]["sanitize_response"]

        response = conn.send_config(config=config)
        if isinstance(teardown_configs, list):
            conn.send_configs(configs=teardown_configs)
        else:
            conn.send_config(config=teardown_configs)

        actual = sanitize_response(response.result)

        if update:
            write_expected(f=__file__, result=actual)

        assert actual == get_expected(f=__file__)

    @pytest.mark.parametrize(
        "strip_prompt",
        [True, False],
        ids=["strip_prompt", "no_strip_prompt"],
    )
    def test_send_configs(self, conn, device_type, transport, strip_prompt, update):
        configs = self.test_cases[device_type]["send_configs"]["configs"]
        teardown_configs = self.test_cases[device_type]["send_config"]["teardown_configs"]
        sanitize_response = self.test_cases[device_type]["sanitize_response"]

        response = conn.send_configs(configs=configs)
        if isinstance(teardown_configs, list):
            conn.send_configs(configs=teardown_configs)
        else:
            conn.send_config(config=teardown_configs)

        actual = sanitize_response(response.result)

        if update:
            write_expected(f=__file__, result=actual)

        assert actual == get_expected(f=__file__)

    @pytest.mark.parametrize(
        "strip_prompt",
        [True, False],
        ids=["strip_prompt", "no_strip_prompt"],
    )
    def test_send_configs_from_file(self, conn, device_type, transport, strip_prompt, update):
        file = self.test_cases[device_type]["send_configs_from_file"]["file"]
        teardown_configs = self.test_cases[device_type]["send_config"]["teardown_configs"]
        sanitize_response = self.test_cases[device_type]["sanitize_response"]

        response = conn.send_configs_from_file(file=file)
        if isinstance(teardown_configs, list):
            conn.send_configs(configs=teardown_configs)
        else:
            conn.send_config(config=teardown_configs)

        actual = sanitize_response(response.result)

        if update:
            write_expected(f=__file__, result=actual)

        assert actual == get_expected(f=__file__)

    def test_send_configs_stop_on_failed(self, conn, device_type, transport):
        if self.test_cases[device_type]["send_configs_error"] is None:
            pytest.skip(
                f"test_send_configs_stop_on_failed for device type {device_type} not tested yet, need to overhaul privilege levels..."
            )

        configs = self.test_cases[device_type]["send_configs_error"]["configs"]
        teardown_configs = self.test_cases[device_type]["send_configs_error"]["teardown_configs"]
        responses = conn.send_configs(configs=configs, stop_on_failed=True)

        assert len(responses) == 2
        assert responses[0].failed is False
        assert responses[1].failed is True
        if isinstance(teardown_configs, list):
            conn.send_configs(configs=teardown_configs)
        else:
            conn.send_config(config=teardown_configs)

    def test_isalive_and_close(self, conn, device_type, transport):
        assert conn.isalive() is True
        conn.close()
        # unsure why but w/out a tiny sleep pytest just plows ahead and the connection doesnt
        # close in time for the next assert
        time.sleep(0.5)
        assert conn.isalive() is False


def test_context_manager(test_devices_dict, device_type, transport):
    device = test_devices_dict[device_type].copy()
    driver = device.pop("driver")
    device.pop("base_config")
    device.pop("async_driver")

    port = device.pop("port", 22)
    if transport == "telnet":
        port = port + 1

    device["port"] = port
    device["transport"] = transport
    # nxos running on macos is crazy slow....
    device["timeout_socket"] = 30
    device["timeout_transport"] = 30
    device["timeout_ops"] = 30

    with driver(**device) as conn:
        assert conn.isalive() is True
    # unsure why but w/out a tiny sleep pytest just plows ahead and the connection doesnt
    # close in time for the next assert
    time.sleep(0.5)
    assert conn.isalive() is False


def test_public_key_auth(test_devices_dict, real_valid_ssh_key_path, device_type, transport):
    if device_type != "cisco_iosxe" or transport == "telnet":
        pytest.skip("public key auth only tested against iosxe at the moment, and never on telnet!")

    device = test_devices_dict[device_type].copy()
    driver = device.pop("driver")
    device.pop("base_config")
    device.pop("async_driver")

    device["transport"] = transport
    device["timeout_socket"] = 5
    device["timeout_transport"] = 5
    device["timeout_ops"] = 5
    device["auth_private_key"] = real_valid_ssh_key_path

    with driver(**device) as conn:
        assert conn.isalive() is True
    # unsure why but w/out a tiny sleep pytest just plows ahead and the connection doesnt
    # close in time for the next assert
    time.sleep(0.2)
    assert conn.isalive() is False


def test_public_key_auth_failure(
    test_devices_dict, real_invalid_ssh_key_path, device_type, transport
):
    if device_type != "cisco_iosxe" or transport == "telnet":
        pytest.skip("public key auth only tested against iosxe at the moment, and never on telnet!")

    if device_type != "cisco_iosxe" or transport == "system":
        pytest.skip(
            "systemssh raises a different exception as it cant distinguish between auth types as well as the other transports!"
        )

    device = test_devices_dict[device_type].copy()
    driver = device.pop("driver")
    device.pop("base_config")
    device.pop("async_driver")

    device["transport"] = transport
    device["timeout_socket"] = 5
    device["timeout_transport"] = 5
    device["timeout_ops"] = 5
    device["auth_private_key"] = real_invalid_ssh_key_path
    device.pop("auth_password")
    conn = driver(**device)

    with pytest.raises(ScrapliAuthenticationFailed) as exc:
        conn.open()
    assert str(exc.value) == (
        f"Failed to authenticate to host {device['host']} with private key `{real_invalid_ssh_key_path}`."
        " Unable to continue authentication, missing username, password, or both."
    )


def test_public_key_auth_failure_systemssh(
    test_devices_dict, real_invalid_ssh_key_path, device_type, transport
):
    if device_type != "cisco_iosxe" or transport != "system":
        pytest.skip(
            "systemssh raises a different exception as it cant distinguish between auth types as well as the other transports!"
        )

    device = test_devices_dict[device_type].copy()
    driver = device.pop("driver")
    device.pop("base_config")
    device.pop("async_driver")

    device["transport"] = transport
    device["timeout_socket"] = 5
    device["timeout_transport"] = 5
    device["timeout_ops"] = 5
    device["auth_private_key"] = real_invalid_ssh_key_path
    device.pop("auth_password")
    conn = driver(**device)

    with pytest.raises(ScrapliAuthenticationFailed) as exc:
        conn.open()
    assert "auth failed" in str(exc.value)
