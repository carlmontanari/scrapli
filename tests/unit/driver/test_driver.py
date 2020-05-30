from scrapli.driver.core import IOSXEDriver

from ...test_data.devices import DEVICES


def test_context_manager(sync_cisco_iosxe_conn):
    device = DEVICES["mock_cisco_iosxe"].copy()
    with IOSXEDriver(transport="paramiko", **device) as conn:
        assert conn.isalive() is True
    assert conn.isalive() is False


def test_transport_bool(sync_cisco_iosxe_conn):
    sync_cisco_iosxe_conn.open()
    assert bool(sync_cisco_iosxe_conn.transport) is True
    sync_cisco_iosxe_conn.close()
    assert bool(sync_cisco_iosxe_conn.transport) is False
