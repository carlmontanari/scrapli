import re

import pytest

from scrapli.driver.core.cisco_iosxe.driver import PRIVS


@pytest.mark.parametrize(
    "priv_pattern",
    [
        ("exec", "csr1000v>"),
        ("privilege_exec", "csr1000v#"),
        ("configuration", "csr1000v(config)#"),
        ("configuration", "csr1000v(conf-ssh-pubkey-data)#"),
        ("privilege_exec", "csr_1000v#"),
        ("configuration", "csr1000v(config-sg-tacacs+)#"),
    ],
    ids=[
        "base_prompt_exec",
        "base_prompt_privilege_exec",
        "base_prompt_configuration",
        "ssh_key_prompt",
        "underscore_privilege_exec",
        "tacacs_configuration",
    ],
)
def test_prompt_patterns(priv_pattern):
    priv_level_name = priv_pattern[0]
    prompt = priv_pattern[1]
    prompt_pattern = PRIVS.get(priv_level_name).pattern
    match = re.search(pattern=prompt_pattern, string=prompt)
    assert match
