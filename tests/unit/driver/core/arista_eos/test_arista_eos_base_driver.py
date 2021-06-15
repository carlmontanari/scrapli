import re

import pytest

from scrapli.driver.core.arista_eos.base_driver import PRIVS
from scrapli.exceptions import ScrapliPrivilegeError, ScrapliValueError


@pytest.mark.parametrize(
    "priv_pattern",
    [
        ("exec", "localhost>"),
        ("exec", "localhost(something)>"),
        ("exec", "localhost(some thing)>"),
        ("privilege_exec", "localhost#"),
        ("privilege_exec", "localhost(something)#"),
        ("privilege_exec", "localhost(some thing)#"),
        ("configuration", "localhost(config)#"),
        ("configuration", "localhost(something)(config)#"),
        ("configuration", "localhost(some thing)(config)#"),
        ("configuration", "localhost(some thing)(config-s-tacocat)#"),
    ],
    ids=[
        "exec",
        "exec_with_parens",
        "exec_with_space",
        "privilege_exec",
        "privilege_exec_with_parens",
        "privilege_exec_with_space",
        "configuration",
        "config_with_parens",
        "config_with_space",
        "config_session",
    ],
)
def test_prompt_patterns(priv_pattern, sync_eos_driver):
    priv_level_name = priv_pattern[0]
    prompt = priv_pattern[1]
    prompt_pattern = PRIVS.get(priv_level_name).pattern
    match = re.search(pattern=prompt_pattern, string=prompt, flags=re.M | re.I)

    if "config-s" in prompt:
        # we will match by the pattern but the `not_contains` will mean that we should end up
        # with 0 matches
        with pytest.raises(ScrapliPrivilegeError):
            sync_eos_driver._determine_current_priv(current_prompt=prompt)
        return

    assert match

    current_priv_guesses = sync_eos_driver._determine_current_priv(current_prompt=prompt)
    assert len(current_priv_guesses) == 1


def test_register_duplicate_configuration_session(sync_eos_driver):
    sync_eos_driver.register_configuration_session(session_name="scrapli")
    with pytest.raises(ScrapliValueError):
        sync_eos_driver.register_configuration_session(session_name="scrapli")
