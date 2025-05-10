import pytest

GET_PROMPT_ARGNAMES = ("platform", "transport")
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
