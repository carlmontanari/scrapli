from scrapli.driver.core import JunosDriver


def test_junos_driver_init_telnet():
    conn = JunosDriver(host="myhost", transport="telnet")
    assert conn.transport.username_prompt == "login:"
