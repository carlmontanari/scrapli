import re

import pytest

from scrapli.driver.core.cisco_nxos.driver import PRIVS


@pytest.mark.parametrize(
    "priv_pattern",
    [
        ("exec", "switch>"),
        ("privilege_exec", "switch# "),
        ("configuration", "switch(config)# "),
        ("privilege_exec", "swi_tch# "),
    ],
    ids=[
        "exec",
        "privilege_exec",
        "configuration",
        "underscore_privilege_exec",
    ],
)
def test_prompt_patterns(priv_pattern):
    priv_level_name = priv_pattern[0]
    prompt = priv_pattern[1]
    prompt_pattern = PRIVS.get(priv_level_name).pattern
    match = re.search(pattern=prompt_pattern, string=prompt, flags=re.M | re.I)
    assert match
