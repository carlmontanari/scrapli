from scrapli.driver.core.cisco_iosxe.driver import IOSXEDriver


def test_init():
    conn = IOSXEDriver(host="myhost", auth_secondary="enable-pass")
    assert conn.auth_secondary == "enable-pass"
