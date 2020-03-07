from scrapli.driver.core.cisco_iosxe.driver import IOSXEDriver


def test_init():
    conn = IOSXEDriver(auth_secondary="enable-pass")
    assert conn.auth_secondary == "enable-pass"
