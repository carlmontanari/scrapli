def test_configuration_session(eos_conn):
    eos_conn.register_configuration_session(session_name="scrapli_test_session")
    result = eos_conn.send_configs(
        configs=["interface ethernet 1", "show configuration sessions"],
        privilege_level="session_scrapli_test_session",
    )
    eos_conn.close()
    assert "* scrapli_test_session" in result[1].result
