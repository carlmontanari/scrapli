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


@pytest.mark.parametrize(argnames="case", argvalues=(), ids=())
def test_send_input(case): ...


@pytest.mark.parametrize(argnames="case", argvalues=(), ids=())
def test_send_inputs(case): ...


@pytest.mark.parametrize(argnames="case", argvalues=(), ids=())
def test_send_prompted_input(case): ...
