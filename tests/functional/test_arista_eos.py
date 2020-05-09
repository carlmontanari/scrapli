def test_configuration_session(eos_conn):
    eos_conn.register_configuration_session(session_name="scrapli_test_session1")
    result = eos_conn.send_configs(
        configs=["interface ethernet 1", "show configuration sessions"],
        privilege_level="scrapli_test_session1",
    )
    eos_conn.close()
    # pop the config session out
    eos_conn.privilege_levels.pop("scrapli_test_session1")
    assert "* scrapli_test_session" in result[1].result


def test_configuration_session_abort(eos_conn):
    eos_conn.register_configuration_session(session_name="scrapli_test_session2")
    result = eos_conn.send_configs(
        configs=["tacocat", "show configuration sessions"],
        privilege_level="scrapli_test_session2",
        stop_on_failed=True,
    )
    current_prompt = eos_conn.get_prompt()
    eos_conn.close()
    # pop the config session out
    eos_conn.privilege_levels.pop("scrapli_test_session2")
    # assert config session was aborted at first sign of failed config
    assert len(result) == 1
    # assert that session aborted and we are back at priv exec
    assert current_prompt == "localhost#"
