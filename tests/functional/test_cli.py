import pytest

from scrapli import (
    AuthOptions,
    Cli,
    LookupKeyValue,
    ReadCallback,
    SessionOptions,
    TransportBinOptions,
    TransportSsh2Options,
)

GET_PROMPT_ARGNAMES = (
    "platform",
    "transport",
)
GET_PROMPT_ARGVALUES = (
    (
        "arista_eos",
        "bin",
    ),
    (
        "arista_eos",
        "ssh2",
    ),
    (
        "arista_eos",
        "telnet",
    ),
    (
        "nokia_srl",
        "bin",
    ),
    (
        "nokia_srl",
        "ssh2",
    ),
)
GET_PROMPT_IDS = (
    "arista-eos-bin",
    "arista-eos-ssh2",
    "arista-eos-telnet",
    "nokia_srl-bin",
    "nokia_srl-ssh2",
)


@pytest.mark.parametrize(
    argnames=GET_PROMPT_ARGNAMES,
    argvalues=GET_PROMPT_ARGVALUES,
    ids=GET_PROMPT_IDS,
)
def test_get_prompt(cli, cli_assert_result):
    with cli as c:
        cli_assert_result(actual=c.get_prompt())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=GET_PROMPT_ARGNAMES,
    argvalues=GET_PROMPT_ARGVALUES,
    ids=GET_PROMPT_IDS,
)
async def test_get_prompt_async(cli, cli_assert_result):
    async with cli as c:
        actual = await c.get_prompt_async()

        cli_assert_result(actual=actual)


ENTER_MODE_ARGNAMES = (
    "requested_mode",
    "post_open_requested_mode",
    "platform",
    "transport",
)
ENTER_MODE_ARGVALUES = (
    (
        "privileged_exec",
        None,
        "arista_eos",
        "bin",
    ),
    (
        "privileged_exec",
        None,
        "arista_eos",
        "ssh2",
    ),
    (
        "privileged_exec",
        None,
        "arista_eos",
        "telnet",
    ),
    (
        "privileged_exec",
        "exec",
        "arista_eos",
        "bin",
    ),
    (
        "privileged_exec",
        "exec",
        "arista_eos",
        "ssh2",
    ),
    (
        "privileged_exec",
        "exec",
        "arista_eos",
        "telnet",
    ),
    (
        "configuration",
        "exec",
        "arista_eos",
        "bin",
    ),
    (
        "configuration",
        "exec",
        "arista_eos",
        "ssh2",
    ),
    (
        "configuration",
        "exec",
        "arista_eos",
        "telnet",
    ),
    (
        "privileged_exec",
        "configuration",
        "arista_eos",
        "bin",
    ),
    (
        "privileged_exec",
        "configuration",
        "arista_eos",
        "ssh2",
    ),
    (
        "privileged_exec",
        "configuration",
        "arista_eos",
        "telnet",
    ),
    (
        "exec",
        None,
        "nokia_srl",
        "bin",
    ),
    (
        "exec",
        None,
        "nokia_srl",
        "ssh2",
    ),
    (
        "configuration",
        None,
        "nokia_srl",
        "bin",
    ),
    (
        "configuration",
        None,
        "nokia_srl",
        "ssh2",
    ),
)
ENTER_MODE_IDS = (
    "arista-eos-bin-no-change",
    "arista-eos-ssh2-no-change",
    "arista-eos-telnet-no-change",
    "arista-eos-bin-escalate-with-password",
    "arista-eos-ssh2-escalate-with-password",
    "arista-eos-telnet-escalate-with-password",
    "arista-eos-bin-multi-escalate-with-password",
    "arista-eos-ssh2-multi-escalate-with-password",
    "arista-eos-telnet-multi-escalate-with-password",
    "arista-eos-bin-deescalate",
    "arista-eos-ssh2-deescalate",
    "arista-eos-telnet-deescalate",
    "nokia_srl-bin-no-change",
    "nokia_srl-ssh2-no-change",
    "nokia_srl-bin-escalate",
    "nokia_srl-ssh2-escalate",
)


@pytest.mark.parametrize(
    argnames=ENTER_MODE_ARGNAMES,
    argvalues=ENTER_MODE_ARGVALUES,
    ids=ENTER_MODE_IDS,
)
def test_enter_mode(
    requested_mode,
    post_open_requested_mode,
    cli,
    cli_assert_result,
):
    with cli as c:
        if post_open_requested_mode is not None:
            c.enter_mode(requested_mode=post_open_requested_mode)

        cli_assert_result(actual=c.enter_mode(requested_mode=requested_mode))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=ENTER_MODE_ARGNAMES,
    argvalues=ENTER_MODE_ARGVALUES,
    ids=ENTER_MODE_IDS,
)
async def test_enter_mode_async(
    requested_mode,
    post_open_requested_mode,
    cli,
    cli_assert_result,
):
    async with cli as c:
        if post_open_requested_mode is not None:
            await c.enter_mode_async(requested_mode=post_open_requested_mode)

        actual = await c.enter_mode_async(requested_mode=requested_mode)

        cli_assert_result(actual=actual)


SEND_INPUT_ARGNAMES = (
    "input_",
    "requested_mode",
    "post_open_requested_mode",
    "retain_input",
    "retain_trailing_prompt",
    "platform",
    "transport",
)
SEND_INPUT_ARGVALUES = (
    (
        "show version | i Ker",
        "privileged_exec",
        None,
        False,
        False,
        "arista_eos",
        "bin",
    ),
    (
        "show version | i Ker",
        "privileged_exec",
        None,
        False,
        False,
        "arista_eos",
        "ssh2",
    ),
    (
        "show version | i Ker",
        "privileged_exec",
        None,
        False,
        False,
        "arista_eos",
        "telnet",
    ),
    (
        "show run",
        "privileged_exec",
        None,
        False,
        False,
        "arista_eos",
        "bin",
    ),
    (
        "show run",
        "privileged_exec",
        None,
        False,
        False,
        "arista_eos",
        "ssh2",
    ),
    (
        "show run",
        "privileged_exec",
        None,
        False,
        False,
        "arista_eos",
        "telnet",
    ),
    (
        "show run",
        "privileged_exec",
        "configuration",
        False,
        False,
        "arista_eos",
        "bin",
    ),
    (
        "show run",
        "privileged_exec",
        "configuration",
        False,
        False,
        "arista_eos",
        "ssh2",
    ),
    (
        "show run",
        "privileged_exec",
        "configuration",
        False,
        False,
        "arista_eos",
        "telnet",
    ),
    (
        "show run",
        "privileged_exec",
        None,
        True,
        False,
        "arista_eos",
        "bin",
    ),
    (
        "show run",
        "privileged_exec",
        None,
        True,
        False,
        "arista_eos",
        "ssh2",
    ),
    (
        "show run",
        "privileged_exec",
        None,
        True,
        False,
        "arista_eos",
        "telnet",
    ),
    (
        "show run",
        "privileged_exec",
        None,
        False,
        True,
        "arista_eos",
        "bin",
    ),
    (
        "show run",
        "privileged_exec",
        None,
        False,
        True,
        "arista_eos",
        "ssh2",
    ),
    (
        "show run",
        "privileged_exec",
        None,
        False,
        True,
        "arista_eos",
        "telnet",
    ),
    (
        "show run",
        "privileged_exec",
        None,
        True,
        True,
        "arista_eos",
        "bin",
    ),
    (
        "show run",
        "privileged_exec",
        None,
        True,
        True,
        "arista_eos",
        "ssh2",
    ),
    (
        "show run",
        "privileged_exec",
        None,
        True,
        True,
        "arista_eos",
        "telnet",
    ),
    (
        "info system",
        "exec",
        None,
        False,
        False,
        "nokia_srl",
        "bin",
    ),
    (
        "info system",
        "exec",
        None,
        False,
        False,
        "nokia_srl",
        "ssh2",
    ),
    (
        "info",
        "exec",
        None,
        False,
        False,
        "nokia_srl",
        "bin",
    ),
    (
        "info",
        "exec",
        None,
        False,
        False,
        "nokia_srl",
        "ssh2",
    ),
    (
        "info from state",
        "exec",
        None,
        False,
        False,
        "nokia_srl",
        "bin",
    ),
    (
        "info from state",
        "exec",
        None,
        False,
        False,
        "nokia_srl",
        "ssh2",
    ),
)
SEND_INPUT_IDS = (
    "arista-eos-bin-same-mode-no-pagination",
    "arista-eos-ssh2-same-mode-no-pagination",
    "arista-eos-telnet-same-mode-no-pagination",
    "arista-eos-bin-same-mode-pagination",
    "arista-eos-ssh2-same-mode-pagination",
    "arista-eos-telnet-same-mode-pagination",
    "arista-eos-bin-change-mode-pagination",
    "arista-eos-ssh2-change-mode-pagination",
    "arista-eos-telnet-change-mode-pagination",
    "arista-eos-bin-same-mode-pagination-retain-input",
    "arista-eos-ssh2-same-mode-pagination-retain-input",
    "arista-eos-telnet-same-mode-pagination-retain-input",
    "arista-eos-bin-same-mode-pagination-retain-trailing-prompt",
    "arista-eos-ssh2-same-mode-pagination-retain-trailing-prompt",
    "arista-eos-telnet-same-mode-pagination-retain-trailing-prompt",
    "arista-eos-bin-same-mode-pagination-retain-input-and-trailing-prompt",
    "arista-eos-ssh2-same-mode-pagination-retain-input-and-trailing-prompt",
    "arista-eos-telnet-same-mode-pagination-retain-input-and-trailing-prompt",
    "nokia-srl-bin-simple",
    "nokia-srl-ssh2-simple",
    "nokia-srl-bin-big-output",
    "nokia-srl-ssh2-big-output",
    "nokia-srl-bin-enormous-output",
    "nokia-srl-ssh2-enormous-output",
)


@pytest.mark.parametrize(
    argnames=SEND_INPUT_ARGNAMES,
    argvalues=SEND_INPUT_ARGVALUES,
    ids=SEND_INPUT_IDS,
)
def test_send_input(
    input_,
    requested_mode,
    post_open_requested_mode,
    retain_input,
    retain_trailing_prompt,
    cli,
    cli_assert_result,
    request,
    slow_tests,
):
    if request.config.getoption("--skip-slow") and request.node.name in slow_tests:
        pytest.skip("skipping huge output test due to skip-slow flag")

    with cli as c:
        if post_open_requested_mode is not None:
            c.enter_mode(requested_mode=post_open_requested_mode)

        actual = c.send_input(
            input_=input_,
            requested_mode=requested_mode,
            retain_input=retain_input,
            retain_trailing_prompt=retain_trailing_prompt,
        )

        cli_assert_result(actual=actual)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=SEND_INPUT_ARGNAMES,
    argvalues=SEND_INPUT_ARGVALUES,
    ids=SEND_INPUT_IDS,
)
async def test_send_input_async(
    input_,
    requested_mode,
    post_open_requested_mode,
    retain_input,
    retain_trailing_prompt,
    cli,
    cli_assert_result,
    request,
    slow_tests,
):
    if request.config.getoption("--skip-slow") and request.node.name in slow_tests:
        pytest.skip("skipping huge output test due to skip-slow flag")

    async with cli as c:
        if post_open_requested_mode is not None:
            await c.enter_mode_async(requested_mode=post_open_requested_mode)

        actual = await c.send_input_async(
            input_=input_,
            requested_mode=requested_mode,
            retain_input=retain_input,
            retain_trailing_prompt=retain_trailing_prompt,
        )

        cli_assert_result(actual=actual)


SEND_INPUTS_ARGNAMES = (
    "inputs",
    "platform",
    "transport",
)
SEND_INPUTS_ARGVALUES = (
    (
        ("show version | i Kern",),
        "arista_eos",
        "bin",
    ),
    (
        ("show version | i Kern",),
        "arista_eos",
        "ssh2",
    ),
    (
        ("show version | i Kern", "show run"),
        "arista_eos",
        "bin",
    ),
    (
        ("show version | i Kern", "show run"),
        "arista_eos",
        "ssh2",
    ),
    (
        ("info system", "info"),
        "nokia_srl",
        "bin",
    ),
    (
        ("info system", "info"),
        "nokia_srl",
        "ssh2",
    ),
)
SEND_INPUTS_IDS = (
    "arista-eos-bin-same-mode-single-input",
    "arista-eos-ssh2-same-mode-single-input",
    "arista-eos-bin-same-mode-multi-input",
    "arista-eos-ssh2-same-mode-multi-input",
    "nokia-srl-bin-same-mode-multi-input",
    "nokia-srl-ssh2-same-mode-multi-input",
)


@pytest.mark.parametrize(
    argnames=SEND_INPUTS_ARGNAMES,
    argvalues=SEND_INPUTS_ARGVALUES,
    ids=SEND_INPUTS_IDS,
)
def test_send_inputs(inputs, cli, cli_assert_result):
    with cli as c:
        cli_assert_result(actual=c.send_inputs(inputs=inputs))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=SEND_INPUTS_ARGNAMES,
    argvalues=SEND_INPUTS_ARGVALUES,
    ids=SEND_INPUTS_IDS,
)
async def test_send_inputs_async(inputs, cli, cli_assert_result):
    async with cli as c:
        actual = await c.send_inputs_async(inputs=inputs)

        cli_assert_result(actual=actual)


SEND_PROMPTED_INPUT_ARGNAMES = (
    "input_",
    "prompt",
    "response",
    "requested_mode",
    "platform",
    "transport",
)
SEND_PROMPTED_INPUT_ARGVALUES = (
    (
        'read -p "Will you prompt me plz? " answer',
        "Will you prompt me plz?",
        "nou",
        "bash",
        "arista_eos",
        "bin",
    ),
    (
        'read -p "Will you prompt me plz? " answer',
        "Will you prompt me plz?",
        "nou",
        "bash",
        "arista_eos",
        "ssh2",
    ),
)
SEND_PROMPTED_INPUT_IDS = (
    "arista-eos-bin",
    "arista-eos-ssh2",
)


@pytest.mark.parametrize(
    argnames=SEND_PROMPTED_INPUT_ARGNAMES,
    argvalues=SEND_PROMPTED_INPUT_ARGVALUES,
    ids=SEND_PROMPTED_INPUT_IDS,
)
def test_send_prompted_input(
    input_,
    prompt,
    response,
    requested_mode,
    cli,
    cli_assert_result,
):
    with cli as c:
        cli_assert_result(
            actual=c.send_prompted_input(
                input_=input_,
                prompt=prompt,
                prompt_pattern="",
                requested_mode=requested_mode,
                response=response,
            )
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=SEND_PROMPTED_INPUT_ARGNAMES,
    argvalues=SEND_PROMPTED_INPUT_ARGVALUES,
    ids=SEND_PROMPTED_INPUT_IDS,
)
async def test_send_prompted_input_async(
    input_,
    prompt,
    response,
    requested_mode,
    cli,
    cli_assert_result,
):
    async with cli as c:
        actual = await c.send_prompted_input_async(
            input_=input_,
            prompt=prompt,
            prompt_pattern="",
            requested_mode=requested_mode,
            response=response,
        )

        cli_assert_result(actual=actual)


def eos_cb1(c: Cli, _: str, __: str) -> None:
    c.write_and_return("show version | i Kernel")


def eos_cb2(c: Cli, _: str, __: str) -> None:
    return


def srl_cb1(c: Cli, _: str, __: str) -> None:
    c.write_and_return("show version | grep OS")


def srl_cb2(c: Cli, _: str, __: str) -> None:
    return


READ_WITH_CALLBACKS_ARGNAMES = (
    "initial_input",
    "callbacks",
    "platform",
    "transport",
)
READ_WITH_CALLBACKS_ARGVALUES = (
    (
        "show version | i Kernel",
        [
            ReadCallback(
                name="cb1",
                contains="eos1#",
                callback=eos_cb1,
                once=True,
            ),
            ReadCallback(
                name="cb2",
                contains="eos1#",
                callback=eos_cb2,
                completes=True,
            ),
        ],
        "arista_eos",
        "bin",
    ),
    (
        "show version | i Kernel",
        [
            ReadCallback(
                name="cb1",
                contains="eos1#",
                callback=eos_cb1,
                once=True,
            ),
            ReadCallback(
                name="cb2",
                contains="eos1#",
                callback=eos_cb2,
                completes=True,
            ),
        ],
        "arista_eos",
        "ssh2",
    ),
    (
        "show version | grep OS",
        [
            ReadCallback(
                name="cb1",
                contains="A:srl#",
                callback=srl_cb1,
                once=True,
            ),
            ReadCallback(
                name="cb2",
                contains="A:srl#",
                callback=srl_cb2,
                completes=True,
            ),
        ],
        "nokia_srl",
        "bin",
    ),
    (
        "show version | grep OS",
        [
            ReadCallback(
                name="cb1",
                contains="A:srl#",
                callback=srl_cb1,
                once=True,
            ),
            ReadCallback(
                name="cb2",
                contains="A:srl#",
                callback=srl_cb2,
                completes=True,
            ),
        ],
        "nokia_srl",
        "ssh2",
    ),
)
READ_WITH_CALLBACKS_IDS = (
    "arista-eos-bin",
    "arista-eos-ssh2",
    "nokia-srl-bin",
    "nokia-srl-ssh2",
)


async def a_eos_cb1(c: Cli, _: str, __: str) -> None:
    c.write_and_return("show version | i Kernel")


async def a_eos_cb2(c: Cli, _: str, __: str) -> None:
    return


async def a_srl_cb1(c: Cli, _: str, __: str) -> None:
    c.write_and_return("show version | grep OS")


async def a_srl_cb2(c: Cli, _: str, __: str) -> None:
    return


@pytest.mark.parametrize(
    argnames=READ_WITH_CALLBACKS_ARGNAMES,
    argvalues=READ_WITH_CALLBACKS_ARGVALUES,
    ids=READ_WITH_CALLBACKS_IDS,
)
def test_read_with_callbacks(initial_input, callbacks, cli, cli_assert_result):
    with cli as c:
        cli_assert_result(
            actual=c.read_with_callbacks(
                initial_input=initial_input,
                callbacks=callbacks,
            )
        )


ASYNC_READ_WITH_CALLBACKS_ARGNAMES = (
    "initial_input",
    "callbacks",
    "platform",
    "transport",
)
ASYNC_READ_WITH_CALLBACKS_ARGVALUES = (
    (
        "show version | i Kernel",
        [
            ReadCallback(
                name="cb1",
                contains="eos1#",
                callback_async=a_eos_cb1,
                once=True,
            ),
            ReadCallback(
                name="cb2",
                contains="eos1#",
                callback_async=a_eos_cb2,
                completes=True,
            ),
        ],
        "arista_eos",
        "bin",
    ),
    (
        "show version | i Kernel",
        [
            ReadCallback(
                name="cb1",
                contains="eos1#",
                callback_async=a_eos_cb1,
                once=True,
            ),
            ReadCallback(
                name="cb2",
                contains="eos1#",
                callback_async=a_eos_cb2,
                completes=True,
            ),
        ],
        "arista_eos",
        "ssh2",
    ),
    (
        "show version | grep OS",
        [
            ReadCallback(
                name="cb1",
                contains="A:srl#",
                callback_async=a_srl_cb1,
                once=True,
            ),
            ReadCallback(
                name="cb2",
                contains="A:srl#",
                callback_async=a_srl_cb2,
                completes=True,
            ),
        ],
        "nokia_srl",
        "bin",
    ),
    (
        "show version | grep OS",
        [
            ReadCallback(
                name="cb1",
                contains="A:srl#",
                callback_async=a_srl_cb1,
                once=True,
            ),
            ReadCallback(
                name="cb2",
                contains="A:srl#",
                callback_async=a_srl_cb2,
                completes=True,
            ),
        ],
        "nokia_srl",
        "ssh2",
    ),
)
ASYNC_READ_WITH_CALLBACKS_IDS = (
    "arista-eos-bin",
    "arista-eos-ssh2",
    "nokia-srl-bin",
    "nokia-srl-ssh2",
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=ASYNC_READ_WITH_CALLBACKS_ARGNAMES,
    argvalues=ASYNC_READ_WITH_CALLBACKS_ARGVALUES,
    ids=ASYNC_READ_WITH_CALLBACKS_IDS,
)
async def test_read_with_callbacks_async(initial_input, callbacks, cli, cli_assert_result):
    async with cli as c:
        actual = await c.read_with_callbacks_async(
            initial_input=initial_input,
            callbacks=callbacks,
        )

        cli_assert_result(actual=actual)


OPEN_WITH_KEY_ARGNAMES = (
    "auth_options",
    "transport_options",
)
OPEN_WITH_KEY_ARGVALUES = (
    (
        AuthOptions(
            username="admin-sshkey",
            private_key_path="tests/functional/fixtures/libscrapli_test_ssh_key",
            lookups=[LookupKeyValue(key="enable", value="libscrapli")],
        ),
        TransportBinOptions(),
    ),
    (
        AuthOptions(
            username="admin-sshkey",
            private_key_path="tests/functional/fixtures/libscrapli_test_ssh_key",
            lookups=[LookupKeyValue(key="enable", value="libscrapli")],
        ),
        TransportSsh2Options(),
    ),
    (
        AuthOptions(
            username="admin-sshkey-passphrase",
            private_key_path="tests/functional/fixtures/libscrapli_test_ssh_key_passphrase",
            private_key_passphrase="libscrapli",
            lookups=[LookupKeyValue(key="enable", value="libscrapli")],
        ),
        TransportBinOptions(),
    ),
    (
        AuthOptions(
            username="admin-sshkey-passphrase",
            private_key_path="tests/functional/fixtures/libscrapli_test_ssh_key_passphrase",
            private_key_passphrase="libscrapli",
            lookups=[LookupKeyValue(key="enable", value="libscrapli")],
        ),
        TransportSsh2Options(),
    ),
)
OPEN_WITH_KEY_IDS = (
    "arista-eos-bin",
    "arista-eos-ssh2",
    "arista-eos-bin-passhrase",
    "arista-eos-ssh2-passhrase",
)


@pytest.mark.parametrize(
    argnames=OPEN_WITH_KEY_ARGNAMES,
    argvalues=OPEN_WITH_KEY_ARGVALUES,
    ids=OPEN_WITH_KEY_IDS,
)
def test_open_with_key(eos_available, is_darwin, auth_options, transport_options):
    if eos_available is False:
        # because we cant have this publicly in ci afaik
        pytest.skip("eos not available, skipping...")

    cli = Cli(
        definition_file_or_name="arista_eos",
        host="localhost" if is_darwin else "172.20.20.17",
        port=22022 if is_darwin else 22,
        auth_options=auth_options,
        session_options=SessionOptions(),
        transport_options=transport_options,
    )

    with cli as c:
        c.get_prompt()
