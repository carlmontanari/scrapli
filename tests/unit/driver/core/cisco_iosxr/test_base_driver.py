import re

import pytest

from scrapli.driver.core.cisco_iosxr.driver import PRIVS


@pytest.mark.parametrize(
    "priv_pattern",
    [
        ("privilege_exec", r"RP/0/RP0/CPU0:ios#"),
        ("configuration", r"RP/0/RP0/CPU0:ios(config)#"),
        ("configuration", r"RP/0/RP0/CPU0:i_o_s(config)#"),
    ],
    ids=["privilege_exec", "configuration", "privilege_exec_underscore"],
)
def test_prompt_patterns(priv_pattern):
    priv_level_name = priv_pattern[0]
    prompt = priv_pattern[1]
    prompt_pattern = PRIVS.get(priv_level_name).pattern
    match = re.search(pattern=prompt_pattern, string=prompt, flags=re.M | re.I)
    assert match
