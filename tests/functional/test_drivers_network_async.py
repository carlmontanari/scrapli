import time

import pytest
from expected import get_expected, write_expected


class TestAsyncNetworkDevice:
    @pytest.fixture(autouse=True)
    def __setup(self, test_cases):
        self.test_cases = test_cases

    @pytest.mark.parametrize(
        "priv_level",
        ["exec", "privilege_exec", "configuration"],
        ids=["exec", "privilege_exec", "configuration"],
    )
    async def test_get_prompt_and_acquire_priv(self, async_conn, priv_level, device_type, update):
        if (device_type in ("cisco_nxos", "cisco_iosxr") and priv_level == "exec") or (
            device_type == "juniper_junos" and priv_level == "privilege_exec"
        ):
            pytest.skip(f"Priv level {priv_level} for device type {device_type} not tested")

        await async_conn.acquire_priv(priv_level)
        actual = await async_conn.get_prompt()

        if update:
            write_expected(f=__file__, result=actual)

        assert actual == get_expected(f=__file__)

    @pytest.mark.parametrize(
        "strip_prompt",
        [True, False],
        ids=["strip_prompt", "no_strip_prompt"],
    )
    async def test_send_command_short(self, async_conn, device_type, strip_prompt, update):
        command = self.test_cases[device_type]["send_command_short"]["command"]
        sanitize_response = self.test_cases[device_type]["sanitize_response"]

        response = await async_conn.send_command(command=command, strip_prompt=strip_prompt)

        actual = sanitize_response(response.result)

        if update:
            write_expected(f=__file__, result=actual)

        assert actual == get_expected(f=__file__)

    @pytest.mark.parametrize(
        "strip_prompt",
        [True, False],
        ids=["strip_prompt", "no_strip_prompt"],
    )
    async def test_send_command_long(self, async_conn, device_type, strip_prompt, update):
        command = self.test_cases[device_type]["send_command_long"]["command"]
        sanitize_response = self.test_cases[device_type]["sanitize_response"]

        response = await async_conn.send_command(command=command, strip_prompt=strip_prompt)

        actual = sanitize_response(response.result)

        if update:
            write_expected(f=__file__, result=actual)

        assert actual == get_expected(f=__file__)

    @pytest.mark.parametrize(
        "strip_prompt",
        [True, False],
        ids=["strip_prompt", "no_strip_prompt"],
    )
    async def test_send_commands(self, async_conn, device_type, strip_prompt, update):
        commands = [
            self.test_cases[device_type]["send_command_short"]["command"],
            self.test_cases[device_type]["send_command_long"]["command"],
        ]
        sanitize_response = self.test_cases[device_type]["sanitize_response"]

        response = await async_conn.send_commands(commands=commands, strip_prompt=strip_prompt)

        actual = sanitize_response(response.result)

        if update:
            write_expected(f=__file__, result=actual)

        assert actual == get_expected(f=__file__)

    @pytest.mark.parametrize(
        "strip_prompt",
        [True, False],
        ids=["strip_prompt", "no_strip_prompt"],
    )
    async def test_send_commands_from_file(self, async_conn, device_type, strip_prompt, update):
        file = self.test_cases[device_type]["send_commands_from_file"]["file"]
        sanitize_response = self.test_cases[device_type]["sanitize_response"]

        response = await async_conn.send_commands_from_file(file=file, strip_prompt=strip_prompt)

        actual = sanitize_response(response.result)

        if update:
            write_expected(f=__file__, result=actual)

        assert actual == get_expected(f=__file__)

    async def test_send_commands_stop_on_failed(self, async_conn, device_type):
        commands = self.test_cases[device_type]["send_commands_error"]["commands"]

        responses = await async_conn.send_commands(commands=commands, stop_on_failed=True)

        assert len(responses) == 2
        assert responses[0].failed is False
        assert responses[1].failed is True

    async def test_send_interactive_normal_response(self, async_conn, device_type, update):
        if self.test_cases[device_type]["send_interactive_normal_response"] is None:
            pytest.skip(
                f"send_interactive_normal_response for device type {device_type} not tested"
            )
        interact = self.test_cases[device_type]["send_interactive_normal_response"]["command"]

        response = await async_conn.send_interactive(interact_events=interact)

        actual = response.result

        if update:
            write_expected(f=__file__, result=actual)

        assert actual == get_expected(f=__file__)

    @pytest.mark.parametrize(
        "strip_prompt",
        [True, False],
        ids=["strip_prompt", "no_strip_prompt"],
    )
    async def test_send_config(self, async_conn, device_type, strip_prompt, update):
        config = self.test_cases[device_type]["send_config"]["configs"]
        teardown_configs = self.test_cases[device_type]["send_config"]["teardown_configs"]
        sanitize_response = self.test_cases[device_type]["sanitize_response"]

        response = await async_conn.send_config(config=config)
        if isinstance(teardown_configs, list):
            await async_conn.send_configs(configs=teardown_configs)
        else:
            await async_conn.send_config(config=teardown_configs)

        actual = sanitize_response(response.result)

        if update:
            write_expected(f=__file__, result=actual)

        assert actual == get_expected(f=__file__)

    @pytest.mark.parametrize(
        "strip_prompt",
        [True, False],
        ids=["strip_prompt", "no_strip_prompt"],
    )
    async def test_send_configs(self, async_conn, device_type, strip_prompt, update):
        configs = self.test_cases[device_type]["send_configs"]["configs"]
        teardown_configs = self.test_cases[device_type]["send_config"]["teardown_configs"]
        sanitize_response = self.test_cases[device_type]["sanitize_response"]

        response = await async_conn.send_configs(configs=configs)
        if isinstance(teardown_configs, list):
            await async_conn.send_configs(configs=teardown_configs)
        else:
            await async_conn.send_config(config=teardown_configs)

        actual = sanitize_response(response.result)

        if update:
            write_expected(f=__file__, result=actual)

        assert actual == get_expected(f=__file__)

    @pytest.mark.parametrize(
        "strip_prompt",
        [True, False],
        ids=["strip_prompt", "no_strip_prompt"],
    )
    async def test_send_configs_from_file(self, async_conn, device_type, strip_prompt, update):
        file = self.test_cases[device_type]["send_configs_from_file"]["file"]
        teardown_configs = self.test_cases[device_type]["send_config"]["teardown_configs"]
        sanitize_response = self.test_cases[device_type]["sanitize_response"]

        response = await async_conn.send_configs_from_file(file=file)
        if isinstance(teardown_configs, list):
            await async_conn.send_configs(configs=teardown_configs)
        else:
            await async_conn.send_config(config=teardown_configs)

        actual = sanitize_response(response.result)

        if update:
            write_expected(f=__file__, result=actual)

        assert actual == get_expected(f=__file__)

    async def test_send_configs_stop_on_failed(self, async_conn, device_type):
        if self.test_cases[device_type]["send_configs_error"] is None:
            pytest.skip(
                f"test_send_configs_stop_on_failed for device type {device_type} not tested yet, need to overhaul privilege levels..."
            )

        configs = self.test_cases[device_type]["send_configs_error"]["configs"]
        teardown_configs = self.test_cases[device_type]["send_configs_error"]["teardown_configs"]
        responses = await async_conn.send_configs(configs=configs, stop_on_failed=True)

        assert len(responses) == 2
        assert responses[0].failed is False
        assert responses[1].failed is True
        if isinstance(teardown_configs, list):
            await async_conn.send_configs(configs=teardown_configs)
        else:
            await async_conn.send_config(config=teardown_configs)

    async def test_isalive_and_close(self, async_conn, device_type):
        assert async_conn.isalive() is True
        await async_conn.close()
        # unsure why but w/out a tiny sleep pytest just plows ahead and the connection doesnt
        # close in time for the next assert
        time.sleep(0.5)
        assert async_conn.isalive() is False
