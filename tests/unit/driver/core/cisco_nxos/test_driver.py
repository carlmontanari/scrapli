from scrapli.driver.core import NXOSDriver


def test_nxos_driver_init_telnet():
    conn = NXOSDriver(host="myhost", transport="telnet")
    assert conn.transport.username_prompt == "login:"


def test_nxos_open_close(sync_cisco_nxos_conn):
    sync_cisco_nxos_conn.open()
    assert sync_cisco_nxos_conn.get_prompt() == "switch#"
    # "more" will show up if we haven't sent terminal length 0 to the mock nxos server
    assert "more" not in sync_cisco_nxos_conn.send_command(command="show version").result.lower()
    sync_cisco_nxos_conn.close()
