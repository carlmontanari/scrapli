from scrapli.driver.core import AsyncJunosDriver


def test_junos_async_driver_init_telnet():
    conn = AsyncJunosDriver(host="myhost", transport="telnet")
    assert conn.transport.username_prompt == "login:"
