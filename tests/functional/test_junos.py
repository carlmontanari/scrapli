def test_configuration_exclusive(junos_conn):
    junos_conn.acquire_priv("configuration_exclusive")
    result = junos_conn.send_configs(["status"])
    junos_conn.close()
    assert "exclusive" in result[0].result


def test_configuration_private(junos_conn):
    junos_conn.acquire_priv("configuration_private")
    result = junos_conn.send_configs(["status"])
    junos_conn.close()
    assert "private" in result[0].result
