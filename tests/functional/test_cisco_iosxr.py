def test_configuration_exclusive(iosxr_conn):
    iosxr_conn.acquire_priv("configuration_exclusive")
    result = iosxr_conn.send_configs(["do show configuration sessions"])
    iosxr_conn.close()
    # last character should be an asterisk indicating configuration is locked
    assert result[0].result[-1:] == "*"
