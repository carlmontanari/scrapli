import re

import pytest

from scrapli.driver.core.arista_eos.base_driver import PRIVS
from scrapli.exceptions import ScrapliValueError


@pytest.mark.parametrize(
    "priv_pattern",
    [
        ("exec", "localhost>"),
        ("privilege_exec", "localhost#"),
        ("configuration", "localhost(config)#"),
        ("exec", "localhost(something)>"),
        ("privilege_exec", "localhost(something)#"),
        ("configuration", "localhost(something)(config)#"),
        ("exec", "localhost(some thing)>"),
        ("privilege_exec", "localhost(some thing)#"),
        ("configuration", "localhost(some thing)(config)#"),
    ],
    ids=[
        "exec",
        "privilege_exec",
        "configuration",
        "exec_with_parens",
        "privilege_exec_with_parens",
        "config_with_parens",
        "exec_with_space",
        "privilege_exec_with_space",
        "config_with_space",
    ],
)
def test_prompt_patterns(priv_pattern):
    priv_level_name = priv_pattern[0]
    prompt = priv_pattern[1]
    prompt_pattern = PRIVS.get(priv_level_name).pattern
    match = re.search(pattern=prompt_pattern, string=prompt, flags=re.M | re.I)
    assert match


def test_register_duplicate_configuration_session(sync_eos_driver):
    sync_eos_driver.register_configuration_session(session_name="scrapli")
    with pytest.raises(ScrapliValueError):
        sync_eos_driver.register_configuration_session(session_name="scrapli")
