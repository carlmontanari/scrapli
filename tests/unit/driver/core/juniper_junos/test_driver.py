import time

from scrapli.driver.core import JunosDriver


def test_junos_driver_init_telnet():
    conn = JunosDriver(host="myhost", transport="telnet")
    assert conn.transport.username_prompt == "login:"


def test_junos_open_close(sync_juniper_junos_conn):
    # short sleeps seem to fix some weird issues w/ the mock server just not "waking" up or w/e
    time.sleep(1)
    sync_juniper_junos_conn.open()
    time.sleep(1)
    assert sync_juniper_junos_conn.get_prompt() == "vrnetlab>"
    time.sleep(1)
    # "more" will show up if we haven't sent terminal length 0 to the mock nxos server
    assert "more" not in sync_juniper_junos_conn.send_command(command="show version").result.lower()
    sync_juniper_junos_conn.close()
