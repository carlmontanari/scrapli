def test_configuration_exclusive(iosxr_conn):
    iosxr_conn.acquire_priv("configuration_exclusive")
    result = iosxr_conn.send_configs(
        ["do show configuration sessions"], privilege_level="configuration_exclusive"
    )
    iosxr_conn.close()
    # last character should be an asterisk indicating configuration is locked
    assert result[0].result[-1:] == "*"


def test_admin_privilege_exec(iosxr_conn):
    iosxr_conn.acquire_priv("admin_privilege_exec")
    current_prompt = iosxr_conn.get_prompt()
    iosxr_conn.close()
    assert current_prompt.endswith("(admin)#")


def test_admin_configuration(iosxr_conn):
    iosxr_conn.acquire_priv("admin_configuration")
    current_prompt = iosxr_conn.get_prompt()
    iosxr_conn.close()
    assert current_prompt.endswith("(admin-config)#")
