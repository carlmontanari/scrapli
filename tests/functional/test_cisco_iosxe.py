def test_non_standard_default_desired_privilege_level(iosxe_conn):
    # purpose of this test is to ensure that when a user sets a non-standard default desired priv
    # level, that there is nothing in genericdriver/networkdriver that will prevent that from
    # actually being set as the default desired priv level
    iosxe_conn.close()
    iosxe_conn.default_desired_privilege_level = "configuration"
    iosxe_conn.open()
    current_prompt = iosxe_conn.get_prompt()
    assert current_prompt == "csr1000v(config)#"
    iosxe_conn.close()
