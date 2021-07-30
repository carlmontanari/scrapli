import re

import pytest

from scrapli.driver.core.juniper_junos.base_driver import PRIVS


@pytest.mark.parametrize(
    "priv_pattern",
    [("exec", "boxen> "), ("configuration", "boxen# "), ("exec", "box_en> ")],
    ids=["exec", "configuration", "exec_underscore"],
)
def test_prompt_patterns(priv_pattern, sync_junos_driver):
    priv_level_name = priv_pattern[0]
    prompt = priv_pattern[1]
    prompt_pattern = PRIVS.get(priv_level_name).pattern
    match = re.search(pattern=prompt_pattern, string=prompt, flags=re.M | re.I)
    assert match

    current_priv_guesses = sync_junos_driver._determine_current_priv(current_prompt=prompt)
    if priv_level_name == "configuration":
        # config, config exclusive, and config private are same prompt so cant tell them apart and
        # thus we return a list of possible priv levels
        assert len(current_priv_guesses) == 3
    else:
        assert len(current_priv_guesses) == 1
