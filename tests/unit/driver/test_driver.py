import pytest

from scrapli.driver.core import IOSXEDriver
from scrapli.exceptions import TransportPluginError

from ...test_data.devices import DEVICES


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


def test_non_sync_transport():
    device = DEVICES["mock_cisco_iosxe"].copy()
    with pytest.raises(TransportPluginError) as exc:
        IOSXEDriver(transport="asyncssh", **device)
    assert (
        str(exc.value)
        == "Attempting to use transport type asyncssh with a sync driver, must use a non-asyncio transport"
    )


def test_timeout_ops_property(sync_cisco_iosxe_conn):
    # note that there is "sync" and "async" version of this test as the property setter/getter lives
    # in the sync and async drivers -- didnt want to deal w/ having the property in the base driver
    # and having to deal w/ _get_timeout_ops/_set_timeout_ops methods to get overridden by the sync
    # and async drivers
    assert sync_cisco_iosxe_conn.timeout_ops == 30
    assert sync_cisco_iosxe_conn.channel.timeout_ops == 30
    sync_cisco_iosxe_conn.timeout_ops = 5
    assert sync_cisco_iosxe_conn.timeout_ops == 5
    assert sync_cisco_iosxe_conn.channel.timeout_ops == 5
