import re

import pytest

from scrapli.driver.core.cisco_nxos.driver import PRIVS


@pytest.mark.parametrize(
    "priv_pattern",
    [("privilege_exec", "switch# "), ("configuration", "switch(config)# ")],
    ids=["privilege_exec", "configuration"],
)
def test_prompt_patterns(priv_pattern):
    priv_level_name = priv_pattern[0]
    prompt = priv_pattern[1]
    prompt_pattern = PRIVS.get(priv_level_name).pattern
    match = re.search(pattern=prompt_pattern, string=prompt)
    assert match
