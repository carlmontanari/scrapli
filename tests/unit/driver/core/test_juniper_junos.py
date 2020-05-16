import re

import pytest

from scrapli.driver.core.juniper_junos.driver import PRIVS


@pytest.mark.parametrize(
    "priv_pattern",
    [("exec", "vrnetlab> "), ("configuration", "vrnetlab# ")],
    ids=["exec", "configuration"],
)
def test_prompt_patterns(priv_pattern):
    priv_level_name = priv_pattern[0]
    prompt = priv_pattern[1]
    prompt_pattern = PRIVS.get(priv_level_name).pattern
    match = re.search(pattern=prompt_pattern, string=prompt)
    assert match


def test_on_open_on_close(mocked_junos_driver):
    channel_input_1 = "\n"
    channel_output_1 = "\nvrnetlab> "
    channel_input_2 = "set cli complete-on-space off"
    channel_output_2 = "\nvrnetlab> "
    channel_input_3 = "set cli screen-length 0"
    channel_output_3 = "\nvrnetlab> "
    channel_input_4 = "set cli screen-width 511"
    channel_output_4 = "\nvrnetlab> "
    channel_input_5 = "\n"
    channel_output_5 = "\nvrnetlab> "
    channel_input_6 = "exit"
    channel_output_6 = ""
    test_operations = [
        (channel_input_1, channel_output_1),
        (channel_input_2, channel_output_2),
        (channel_input_3, channel_output_3),
        (channel_input_4, channel_output_4),
        (channel_input_5, channel_output_5),
        (channel_input_6, channel_output_6),
    ]
    # mocked junos driver already calls `.open()` so we are just testing that the open commands
    # for both of these methods get sent/read back from the channel... this is mostly to ensure
    # that any change to the open/close methods are noticed and also for vanity coverage :)
    conn = mocked_junos_driver(test_operations)
    conn.close()
