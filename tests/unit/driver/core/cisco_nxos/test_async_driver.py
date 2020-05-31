from scrapli.driver.core import AsyncNXOSDriver


def test_nxos_async_driver_init_telnet():
    conn = AsyncNXOSDriver(host="myhost", transport="telnet")
    assert conn.transport.username_prompt == "login:"
