import re

import pytest

from scrapli.driver.core.cisco_iosxr.base_driver import PRIVS


@pytest.mark.parametrize(
    "priv_pattern",
    [
        ("privilege_exec", r"RP/0/RP0/CPU0:ios#"),
        ("configuration", r"RP/0/RP0/CPU0:ios(config)#"),
        ("configuration", r"RP/0/RP0/CPU0:i_o_s(config)#"),
    ],
    ids=["privilege_exec", "configuration", "privilege_exec_underscore"],
)
def test_prompt_patterns(priv_pattern, sync_iosxr_driver):
    priv_level_name = priv_pattern[0]
    prompt = priv_pattern[1]
    prompt_pattern = PRIVS.get(priv_level_name).pattern
    match = re.search(pattern=prompt_pattern, string=prompt, flags=re.M | re.I)
    assert match

    current_priv_guesses = sync_iosxr_driver._determine_current_priv(current_prompt=prompt)
    if priv_level_name == "configuration":
        # config and config exclusive are same prompt so cant tell them apart and thus we return
        # a list of possible priv levels
        assert len(current_priv_guesses) == 2
    else:
        assert len(current_priv_guesses) == 1
