from scrapli.driver.core import NXOSDriver


def test_nxos_driver_init_telnet():
    conn = NXOSDriver(host="myhost", transport="telnet")
    assert conn.transport.username_prompt == "login:"
