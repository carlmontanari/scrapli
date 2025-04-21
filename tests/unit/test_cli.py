import pytest


@pytest.mark.parametrize(argnames="case", argvalues=(("eos1#",),), ids=("simple",))
def test_get_prompt(case, cli_sync, cli_assert_result):
    with cli_sync as c:
        cli_assert_result(actual=c.get_prompt())


@pytest.mark.parametrize(argnames="case", argvalues=(()), ids=("no-change", "escalate", "deescalate", "multi-stage-change-escalate", "multi-stage-change-deescalate"))
def test_enter_mode(case, cli_sync, cli_assert_result): ...


@pytest.mark.parametrize(argnames="case", argvalues=(), ids=())
def test_send_input(case): ...


@pytest.mark.parametrize(argnames="case", argvalues=(), ids=())
def test_send_inputs(case): ...


@pytest.mark.parametrize(argnames="case", argvalues=(), ids=())
def test_send_prompted_input(case): ...
