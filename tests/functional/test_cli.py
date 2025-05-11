import pytest

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
    "arista-eos-bin-escalate-with-password",
    "arista-eos-ssh2-escalate-with-password",
    "arista-eos-bin-multi-escalate-with-password",
    "arista-eos-ssh2-multi-escalate-with-password",
    "arista-eos-bin-deescalate",
    "arista-eos-ssh2-deescalate",
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
    "arista-eos-bin-same-privilege-level-no-pagination",
    "arista-eos-ssh2-same-privilege-level-no-pagination",
    "arista-eos-bin-same-privilege-level-pagination",
    "arista-eos-ssh2-same-privilege-level-pagination",
    "arista-eos-bin-change-privilege-level-pagination",
    "arista-eos-ssh2-change-privilege-level-pagination",
    "arista-eos-bin-same-privilege-level-pagination-retain-input",
    "arista-eos-ssh2-same-privilege-level-pagination-retain-input",
    "arista-eos-bin-same-privilege-level-pagination-retain-trailing-prompt",
    "arista-eos-ssh2-same-privilege-level-pagination-retain-trailing-prompt",
    "arista-eos-bin-same-privilege-level-pagination-retain-input-and-trailing-prompt",
    "arista-eos-ssh2-same-privilege-level-pagination-retain-input-and-trailing-prompt",
    "nokia-srl-bin-simple",
    "nokia-srl-ssh2-simple",
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
):
    if request.config.getoption("--skip-slow") and input_ == "info from state":
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

        if input_ == "info from state":
            # we dont save the 40mb of output from this command, and also even if we did
            # the counters etc would change so comparing would be pointless
            assert actual.start_time != 0
            assert actual.end_time != 0
            assert actual.elapsed_time_seconds != 0
            assert len(actual.results) != 0
            assert len(actual.results_raw) != 0
            assert actual.failed is False
        else:
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
):
    if request.config.getoption("--skip-slow") and input_ == "info from state":
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

        if input_ == "info from state":
            assert actual.start_time != 0
            assert actual.end_time != 0
            assert actual.elapsed_time_seconds != 0
            assert len(actual.results) != 0
            assert len(actual.results_raw) != 0
            assert actual.failed is False
        else:
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
    "arista-eos-bin-same-privilege-level-single-input",
    "arista-eos-ssh2-same-privilege-level-single-input",
    "arista-eos-bin-same-privilege-level-multi-input",
    "arista-eos-ssh2-same-privilege-level-multi-input",
    "nokia-srl-bin-same-privilege-level-multi-input",
    "nokia-srl-ssh2-same-privilege-level-multi-input",
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
