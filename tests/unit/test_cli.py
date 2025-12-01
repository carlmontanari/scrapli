from time import sleep

import pytest

from scrapli.cli import Cli, InputHandling, ReadCallback

READ_ARGNAMES = (
    "size",
    "input_",
)
READ_ARGVALUES = (
    (
        1_024,  # default size
        "show version | i Kern",
    ),
    (
        64,
        "show version | i Kern",
    ),
)
READ_IDS = (
    "simple",
    "user-sized",
)


@pytest.mark.parametrize(
    argnames=READ_ARGNAMES,
    argvalues=READ_ARGVALUES,
    ids=READ_IDS,
)
def test_read(size, input_, cli, cli_assert_result):
    with cli as c:
        c.write_and_return(input_=input_)

        sleep(1)

        actual = c.read(size=size)

        assert actual != b""
        assert len(actual) > 0


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
    "input_handling",
    "retain_input",
    "retain_trailing_prompt",
)
SEND_INPUT_ARGVALUES = (
    (
        "show version | i Kern",
        "privileged_exec",
        None,
        InputHandling.FUZZY,
        False,
        False,
    ),
    (
        "show running-config all | include snmp",
        "privileged_exec",
        None,
        InputHandling.FUZZY,
        False,
        False,
    ),
    (
        "do show version | i Kern",
        "configuration",
        "configuration",
        InputHandling.FUZZY,
        False,
        False,
    ),
    (
        "do show version | i Kern",
        "configuration",
        None,
        InputHandling.FUZZY,
        False,
        False,
    ),
    (
        "show version | i Kern",
        "privileged_exec",
        None,
        InputHandling.EXACT,
        False,
        False,
    ),
    (
        "show version | i Kern",
        "privileged_exec",
        None,
        InputHandling.IGNORE,
        False,
        False,
    ),
    (
        "show version | i Kern",
        "privileged_exec",
        None,
        InputHandling.FUZZY,
        True,
        False,
    ),
    (
        "show version | i Kern",
        "privileged_exec",
        None,
        InputHandling.FUZZY,
        False,
        True,
    ),
    (
        "show version | i Kern",
        "privileged_exec",
        None,
        InputHandling.FUZZY,
        True,
        True,
    ),
)
SEND_INPUT_IDS = (
    "simple",
    "simple-requires-pagination",
    "simple-already-in-non-default-mode",
    "simple-acquire-non-default-mode",
    "simple-input-handling-exact",
    "simple-input-handling-ignore",
    "simple-retain-input",
    "simple-retain-trailing-prompt",
    "simple-retain-all",
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
    input_handling,
    retain_input,
    retain_trailing_prompt,
    cli,
    cli_assert_result,
):
    with cli as c:
        if post_open_requested_mode is not None:
            c.enter_mode(requested_mode=post_open_requested_mode)

        cli_assert_result(
            actual=c.send_input(
                input_=input_,
                requested_mode=requested_mode,
                input_handling=input_handling,
                retain_input=retain_input,
                retain_trailing_prompt=retain_trailing_prompt,
            )
        )


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
    input_handling,
    retain_input,
    retain_trailing_prompt,
    cli,
    cli_assert_result,
):
    async with cli as c:
        if post_open_requested_mode is not None:
            await c.enter_mode_async(requested_mode=post_open_requested_mode)

        actual = await c.send_input_async(
            input_=input_,
            requested_mode=requested_mode,
            input_handling=input_handling,
            retain_input=retain_input,
            retain_trailing_prompt=retain_trailing_prompt,
        )

        cli_assert_result(actual=actual)


SEND_INPUTS_ARGNAMES = ("inputs",)
SEND_INPUTS_ARGVALUES = (
    (("show version | i Kern",),),
    (("show version | i Kern", "show version"),),
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


SEND_INPUTS_FROM_FILE_ARGNAMES = ("f",)
SEND_INPUTS_FROM_FILE_ARGVALUES = (
    ("tests/unit/fixtures/cli/_inputs_from_file_single",),
    ("tests/unit/fixtures/cli/_inputs_from_file_multi",),
)
SEND_INPUTS_FROM_FILE_IDS = (
    "send-single-input",
    "send-multi-input",
)


@pytest.mark.parametrize(
    argnames=SEND_INPUTS_FROM_FILE_ARGNAMES,
    argvalues=SEND_INPUTS_FROM_FILE_ARGVALUES,
    ids=SEND_INPUTS_FROM_FILE_IDS,
)
def test_send_inputs_from_file(f, cli, cli_assert_result):
    with cli as c:
        cli_assert_result(actual=c.send_inputs_from_file(f=f))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=SEND_INPUTS_FROM_FILE_ARGNAMES,
    argvalues=SEND_INPUTS_FROM_FILE_ARGVALUES,
    ids=SEND_INPUTS_FROM_FILE_IDS,
)
async def test_send_inputs_from_file_async(f, cli, cli_assert_result):
    async with cli as c:
        actual = await c.send_inputs_from_file_async(f=f)

        cli_assert_result(actual=actual)


SEND_PROMPTED_INPUT_ARGNAMES = (
    "input_",
    "prompt",
    "prompt_pattern",
    "response",
    "requested_mode",
)
SEND_PROMPTED_INPUT_ARGVALUES = (
    (
        'read -p "Will you prompt me plz? " answer',
        "Will you prompt me plz?",
        "",
        "nou",
        "bash",
    ),
)
SEND_PROMPTED_INPUT_IDS = ("simple",)


@pytest.mark.parametrize(
    argnames=SEND_PROMPTED_INPUT_ARGNAMES,
    argvalues=SEND_PROMPTED_INPUT_ARGVALUES,
    ids=SEND_PROMPTED_INPUT_IDS,
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
    argnames=SEND_PROMPTED_INPUT_ARGNAMES,
    argvalues=SEND_PROMPTED_INPUT_ARGVALUES,
    ids=SEND_PROMPTED_INPUT_IDS,
)
async def test_send_prompted_input_async(
    input_, prompt, prompt_pattern, response, requested_mode, cli, cli_assert_result
):
    async with cli as c:
        actual = await c.send_prompted_input_async(
            input_=input_,
            prompt=prompt,
            prompt_pattern=prompt_pattern,
            response=response,
            requested_mode=requested_mode,
        )

        cli_assert_result(actual=actual)


def cb1(c: Cli) -> None:
    c.write_and_return("show version")


def cb2(c: Cli) -> None:
    return


READ_WITH_CALLBACKS_ARGNAMES = (
    "initial_input",
    "callbacks",
)
READ_WITH_CALLBACKS_ARGVALUES = (
    (
        "show version",
        [
            ReadCallback(
                name="cb1",
                contains="eos1#",
                callback=cb1,
                once=True,
            ),
            ReadCallback(
                name="cb2",
                contains="eos1#",
                callback=cb2,
                completes=True,
            ),
        ],
    ),
)
READ_WITH_CALLBACKS_IDS = ("simple",)


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


@pytest.mark.asyncio
@pytest.mark.parametrize(
    argnames=READ_WITH_CALLBACKS_ARGNAMES,
    argvalues=READ_WITH_CALLBACKS_ARGVALUES,
    ids=READ_WITH_CALLBACKS_IDS,
)
async def test_read_with_callbacks_async(initial_input, callbacks, cli, cli_assert_result):
    async with cli as c:
        actual = await c.read_with_callbacks_async(
            initial_input=initial_input,
            callbacks=callbacks,
        )

        cli_assert_result(actual=actual)
