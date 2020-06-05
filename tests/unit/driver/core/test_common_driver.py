import pytest

from scrapli.driver.core.arista_eos.driver import EOSDriver, eos_on_close, eos_on_open
from scrapli.driver.core.cisco_iosxe.driver import IOSXEDriver, iosxe_on_close, iosxe_on_open
from scrapli.driver.core.cisco_iosxr.driver import IOSXRDriver, iosxr_on_close, iosxr_on_open
from scrapli.driver.core.cisco_nxos.driver import NXOSDriver, nxos_on_close, nxos_on_open
from scrapli.driver.core.juniper_junos.driver import JunosDriver, junos_on_close, junos_on_open


def custom_open_close_func():
    return


@pytest.mark.parametrize(
    "attr_setup",
    [
        {"auth_secondary": "password", "on_open": None, "on_close": None},
        {
            "auth_secondary": "password",
            "on_open": custom_open_close_func,
            "on_close": custom_open_close_func,
        },
    ],
    ids=["default", "custom_open_close"],
)
@pytest.mark.parametrize(
    "platform",
    [
        (IOSXEDriver, iosxe_on_close, iosxe_on_open),
        (NXOSDriver, nxos_on_close, nxos_on_open),
        (IOSXRDriver, iosxr_on_close, iosxr_on_open),
        (EOSDriver, eos_on_close, eos_on_open),
        (JunosDriver, junos_on_close, junos_on_open),
    ],
    ids=["iosxe", "nxos", "iosxr", "eos", "junos"],
)
def test_core_driver_init(platform, attr_setup):
    driver_args = attr_setup
    driver = platform[0]
    on_close = driver_args["on_close"] or platform[1]
    on_open = driver_args["on_open"] or platform[2]
    conn = driver(host="myhost", **driver_args)
    assert conn.auth_secondary == driver_args["auth_secondary"]
    assert conn.on_open == on_open
    assert conn.on_close == on_close
