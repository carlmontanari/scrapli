def test_context_manager(sync_cisco_iosxe_conn):
    with sync_cisco_iosxe_conn as conn:
        assert conn.isalive() is True
    assert conn.isalive() is False


def test_transport_bool(sync_cisco_iosxe_conn):
    sync_cisco_iosxe_conn.open()
    assert bool(sync_cisco_iosxe_conn.transport) is True
    sync_cisco_iosxe_conn.close()
    assert bool(sync_cisco_iosxe_conn.transport) is False


def test_transport_encrypted_private_key(sync_cisco_iosxe_conn_encrypted_key):
    sync_cisco_iosxe_conn_encrypted_key.open()
    assert bool(sync_cisco_iosxe_conn_encrypted_key.transport) is True
    sync_cisco_iosxe_conn_encrypted_key.close()
    assert bool(sync_cisco_iosxe_conn_encrypted_key.transport) is False
