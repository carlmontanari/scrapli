import pytest


def test_get_prompt(cli, cli_assert_result):
    with cli as c:
        cli_assert_result(actual=c.get_prompt())


@pytest.mark.asyncio
async def test_get_prompt_async(cli, cli_assert_result):
    async with cli as c:
        actual = await c.get_prompt_async()

        cli_assert_result(actual=actual)


ENTER_MODE_ARGNAMES = (
    "requested_mode",
    "post_open_requested_mode",  # acquire this before "doing" the test
)
ENTER_MODE_ARGVALUES = (
    (
        "privileged_exec",
        None,
    ),
    (
        "configuration",
        None,
    ),
    (
        "exec",
        None,
    ),
    (
        "configuration",
        "exec",
    ),
    (
        "exec",
        "configuration",
    ),
)
ENTER_MODE_IDS = (
    "no-change",
    "escalate",
    "deescalate",
    "multi-stage-change-escalate",
    "multi-stage-change-deescalate",
)


@pytest.mark.parametrize(
    argnames=ENTER_MODE_ARGNAMES,
    argvalues=ENTER_MODE_ARGVALUES,
    ids=ENTER_MODE_IDS,
)
def test_enter_mode(requested_mode, post_open_requested_mode, cli, cli_assert_result):
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
async def test_enter_mode_async(requested_mode, post_open_requested_mode, cli, cli_assert_result):
    async with cli as c:
        if post_open_requested_mode is not None:
            c.enter_mode(requested_mode=post_open_requested_mode)

        actual = await c.enter_mode_async(requested_mode=requested_mode)

        cli_assert_result(actual=actual)


SEND_INPUT_ARGNAMES = (
    "input_",
    "requested_mode",  # mode to send the input at
    "post_open_requested_mode",  # acquire this before "doing" the test
)
SEND_INPUT_ARGVALUES = (
    (
        "show version | i Kern",
        "privileged_exec",
        None,
    ),
    (
        "show running-config all | include snmp",
        "privileged_exec",
        None,
    ),
    (
        "do show version | i Kern",
        "configuration",
        "configuration",
    ),
    (
        "do show version | i Kern",
        "configuration",
        None,
    ),
)
SEND_INPUT_IDS = (
    "simple",
    "simple-requires-pagination",
    "simple-already-in-non-default-mode",
    "simple-acquire-non-default-mode",
)


@pytest.mark.parametrize(
    argnames=SEND_INPUT_ARGNAMES,
    argvalues=SEND_INPUT_ARGVALUES,
    ids=SEND_INPUT_IDS,
)
def test_send_input(input_, requested_mode, post_open_requested_mode, cli, cli_assert_result):
    with cli as c:
        if post_open_requested_mode is not None:
            c.enter_mode(requested_mode=post_open_requested_mode)

        cli_assert_result(actual=c.send_input(input_=input_, requested_mode=requested_mode))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=SEND_INPUT_ARGNAMES,
    argvalues=SEND_INPUT_ARGVALUES,
    ids=SEND_INPUT_IDS,
)
async def test_send_input_async(
    input_, requested_mode, post_open_requested_mode, cli, cli_assert_result
):
    async with cli as c:
        if post_open_requested_mode is not None:
            await c.enter_mode_async(requested_mode=post_open_requested_mode)

        actual = await c.send_input_async(input_=input_, requested_mode=requested_mode)

        cli_assert_result(actual=actual)


SEND_INPUTS_ARGNAMES = ("inputs",)
SEND_INPUTS_ARGVALUES = (
    (("show version | i Kern",),),
    (("show version | i Kern", "show version | i Kern"),),
)
SEND_INPUTS_IDS = (
    "send-single-input",
    "send-multi-input",
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


SEND_PROMPTED_INPUTS_ARGNAMES = ("input_", "prompt", "prompt_pattern", "response", "requested_mode")
SEND_PROMPTED_INPUTS_ARGVALUES = (
    ('read -p "Will you prompt me plz?"', "Will you prompt me plz?", "", "nou", "bash"),
)
SEND_PROMPTED_INPUTS_IDS = ("simple",)


@pytest.mark.parametrize(
    argnames=SEND_PROMPTED_INPUTS_ARGNAMES,
    argvalues=SEND_PROMPTED_INPUTS_ARGVALUES,
    ids=SEND_PROMPTED_INPUTS_IDS,
)
def test_send_prompted_input(
    input_, prompt, prompt_pattern, response, requested_mode, cli, cli_assert_result
):
    with cli as c:
        cli_assert_result(
            actual=c.send_prompted_input(
                input_=input_,
                prompt=prompt,
                prompt_pattern=prompt_pattern,
                response=response,
                requested_mode=requested_mode,
            )
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=SEND_PROMPTED_INPUTS_ARGNAMES,
    argvalues=SEND_PROMPTED_INPUTS_ARGVALUES,
    ids=SEND_PROMPTED_INPUTS_IDS,
)
async def test_send_prompted_input_async(
    input_, prompt, prompt_pattern, response, requested_mode, cli, cli_assert_result
):
    async with cli as c:
        actual = await c.send_prompted_input(
            input_=input_,
            prompt=prompt,
            prompt_pattern=prompt_pattern,
            response=response,
            requested_mode=requested_mode,
        )

        cli_assert_result(actual=actual)
