def test_configuration_session(nxos_conn):
    nxos_conn.register_configuration_session(session_name="scrapli_test_session")
    result = nxos_conn.send_configs(
        configs=["interface mgmt0", "show configuration session scrapli_test_session"],
        privilege_level="session_scrapli_test_session",
    )
    nxos_conn.close()
    assert "config session name scrapli_test_session" in result[1].result
