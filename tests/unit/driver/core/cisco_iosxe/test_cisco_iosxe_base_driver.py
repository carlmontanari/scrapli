import re

import pytest

from scrapli.driver.core.cisco_iosxe.base_driver import PRIVS


@pytest.mark.parametrize(
    "priv_pattern",
    [
        ("exec", "csr1000v>"),
        ("privilege_exec", "csr1000v#"),
        ("privilege_exec", "csr_1000v#"),
        ("configuration", "csr1000v(config)#"),
        ("configuration", "csr1000v(conf-ssh-pubkey-data)#"),
        ("configuration", "csr1000v(config-sg-tacacs+)#"),
        ("configuration", "819HGW(ipsec-profile)#"),
        ("tclsh", "819HGW(tcl)#"),
        ("tclsh", "+>"),
        ("tclsh", "+>(tcl)#"),
    ],
    ids=[
        "base_prompt_exec",
        "base_prompt_privilege_exec",
        "underscore_privilege_exec",
        "base_prompt_configuration",
        "ssh_key_prompt",
        "tacacs_configuration",
        "ipsec_profile",
        "tclsh",
        "tclsh_command_mode",
        "tclsh_command_mode_17+",
    ],
)
def test_prompt_patterns(priv_pattern, sync_iosxe_driver):
    priv_level_name = priv_pattern[0]
    prompt = priv_pattern[1]
    prompt_pattern = PRIVS.get(priv_level_name).pattern
    match = re.search(pattern=prompt_pattern, string=prompt, flags=re.M | re.I)
    assert match

    current_priv_guesses = sync_iosxe_driver._determine_current_priv(current_prompt=prompt)
    assert len(current_priv_guesses) == 1


@pytest.mark.parametrize(
    "prompt",
    [
        "password:",
        "Password:",
        "Enable password:",
    ],
    ids=["password:", "Password:", "Enable password:"],
)
def test_privilege_exec_escalation_prompt_patterns(prompt):
    escalation_pattern = PRIVS.get("privilege_exec").escalate_prompt
    match = re.search(pattern=escalation_pattern, string=prompt, flags=re.M | re.I)
    assert match
