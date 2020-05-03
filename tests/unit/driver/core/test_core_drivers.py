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


def test_juniper_driver_init_telnet():
    conn = JunosDriver(host="myhost", transport="telnet")
    assert conn.transport.username_prompt == "login:"


def test_nxos_driver_init_telnet():
    conn = NXOSDriver(host="myhost", transport="telnet")
    assert conn.transport.username_prompt == "login:"


@pytest.mark.parametrize(
    "session_data",
    [
        (NXOSDriver, "mysession", r"^[a-z0-9.\-@/:]{1,32}\(config\-s[a-z0-9.\-@/:]{0,32}\)#\s?$"),
        (
            EOSDriver,
            "my-session",
            r"^[a-z0-9.\-@/:]{1,32}\(config\-s\-my\-ses[a-z0-9_.\-@/:]{0,32}\)#\s?$",
        ),
    ],
    ids=["nxos", "eos"],
)
def test_driver_register_configuration_session(session_data):
    driver = session_data[0]
    session_name = session_data[1]
    session_pattern = session_data[2]
    conn = driver(host="myhost")
    conn.register_configuration_session(session_name=session_name)
    assert conn.privilege_levels[session_name].pattern == session_pattern


@pytest.mark.parametrize(
    "session_data",
    [(NXOSDriver, "configuration",), (EOSDriver, "configuration",),],
    ids=["nxos", "eos"],
)
def test_driver_register_configuration_session_duplicate_name(session_data):
    driver = session_data[0]
    session_name = session_data[1]
    conn = driver(host="myhost")
    with pytest.raises(ValueError) as exc:
        conn.register_configuration_session(session_name=session_name)
    assert (
        str(exc.value)
        == f"session name `{session_name}` already registered as a privilege level, chose a unique session name"
    )
