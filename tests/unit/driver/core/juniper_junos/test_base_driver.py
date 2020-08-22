import re

import pytest

from scrapli.driver.core.juniper_junos.driver import PRIVS


@pytest.mark.parametrize(
    "priv_pattern",
    [("exec", "vrnetlab> "), ("configuration", "vrnetlab# "), ("exec", "vrn_etlab> ")],
    ids=["exec", "configuration", "exec_underscore"],
)
def test_prompt_patterns(priv_pattern):
    priv_level_name = priv_pattern[0]
    prompt = priv_pattern[1]
    prompt_pattern = PRIVS.get(priv_level_name).pattern
    match = re.search(pattern=prompt_pattern, string=prompt, flags=re.M | re.I)
    assert match
