from scrapli.driver.core import JunosDriver


def test_junos_driver_init_telnet():
    conn = JunosDriver(host="myhost", transport="telnet")
    assert conn.transport.username_prompt == "login:"


def test_junos_open_close(sync_juniper_junos_conn):
    sync_juniper_junos_conn.open()
    assert sync_juniper_junos_conn.get_prompt() == "vrnetlab>"
    # chalking this up to weirdness w/ the mock ssh server... it seems to not set the terminal
    # length correct on open the first time... unclear why... future me problem
    sync_juniper_junos_conn.send_command(command="set cli screen-length 0")
    # "more" will show up if we haven't sent terminal length 0 to the mock nxos server
    assert "more" not in sync_juniper_junos_conn.send_command(command="show version").result.lower()
    sync_juniper_junos_conn.close()
