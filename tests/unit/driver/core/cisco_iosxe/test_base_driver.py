import re

import pytest

from scrapli.driver.core.cisco_iosxe.driver import PRIVS


@pytest.mark.parametrize(
    "priv_pattern",
    [("configuration", "csr1000v(config)#"), ("configuration", "csr1000v(conf-ssh-pubkey-data)#")],
    ids=["base_prompt", "ssh_key_prompt"],
)
def test_prompt_patterns(priv_pattern):
    priv_level_name = priv_pattern[0]
    prompt = priv_pattern[1]
    prompt_pattern = PRIVS.get(priv_level_name).pattern
    match = re.search(pattern=prompt_pattern, string=prompt)
    assert match
