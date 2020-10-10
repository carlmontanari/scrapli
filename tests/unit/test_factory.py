import importlib

import pytest

from scrapli.driver import AsyncNetworkDriver, NetworkDriver
from scrapli.driver.base_network_driver import PrivilegeLevel
from scrapli.driver.core import (
    AsyncEOSDriver,
    AsyncIOSXEDriver,
    AsyncIOSXRDriver,
    AsyncJunosDriver,
    AsyncNXOSDriver,
    EOSDriver,
    IOSXEDriver,
    IOSXRDriver,
    JunosDriver,
    NXOSDriver,
)
from scrapli.exceptions import ScrapliException
from scrapli.factory import AsyncScrapli, Scrapli, _get_community_platform_details

TEST_COMMUNITY_PRIV_LEVELS = {
    "exec": (
        PrivilegeLevel(
            pattern=r"^[a-z0-9.\-_@()/:]{1,63}>$",
            name="exec",
            previous_priv="",
            deescalate="",
            escalate="",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
    "privilege_exec": (
        PrivilegeLevel(
            pattern=r"^[a-z0-9.\-_@/:]{1,63}#$",
            name="privilege_exec",
            previous_priv="exec",
            deescalate="disable",
            escalate="enable",
            escalate_auth=True,
            escalate_prompt=r"^[pP]assword:\s?$",
        )
    ),
    "configuration": (
        PrivilegeLevel(
            pattern=r"^[a-z0-9.\-_@/:]{1,63}\(conf[a-z0-9.\-@/:\+]{0,32}\)#$",
            name="configuration",
            previous_priv="privilege_exec",
            deescalate="end",
            escalate="configure terminal",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
}


@pytest.mark.parametrize(
    "platform",
    [
        ("cisco_iosxe", IOSXEDriver),
        ("cisco_iosxr", IOSXRDriver),
        ("cisco_nxos", NXOSDriver),
        ("arista_eos", EOSDriver),
        ("juniper_junos", JunosDriver),
    ],
    ids=["cisco_iosxe", "cisco_iosxr", "cisco_nxos", "arista_eos", "juniper_junos"],
)
def test_sync_factory(platform):
    driver = Scrapli(platform=platform[0], host="localhost")
    assert isinstance(driver, platform[1])


@pytest.mark.parametrize(
    "platform",
    [
        ("cisco_iosxe", AsyncIOSXEDriver),
        ("cisco_iosxr", AsyncIOSXRDriver),
        ("cisco_nxos", AsyncNXOSDriver),
        ("arista_eos", AsyncEOSDriver),
        ("juniper_junos", AsyncJunosDriver),
    ],
    ids=["cisco_iosxe", "cisco_iosxr", "cisco_nxos", "arista_eos", "juniper_junos"],
)
def test_async_factory(platform):
    driver = AsyncScrapli(platform=platform[0], host="localhost", transport="asyncssh")
    assert isinstance(driver, platform[1])


def test_sync_factory_async_transport_exception():
    with pytest.raises(ScrapliException) as exc:
        Scrapli(platform="cisco_iosxe", transport="asyncssh")
    assert str(exc.value) == "Use `AsyncScrapli` if using an async transport!"


def test_async_factory_sync_transport_exception():
    with pytest.raises(ScrapliException) as exc:
        AsyncScrapli(platform="cisco_iosxe", transport="system")
    assert str(exc.value) == "Use `Scrapli` if using a synchronous transport!"


@pytest.mark.parametrize(
    "factory_setup",
    [(Scrapli, "system"), (AsyncScrapli, "asyncssh")],
    ids=["sync_factory", "async_factory"],
)
def test_factory_platform_bad_type(factory_setup):
    Factory = factory_setup[0]
    transport = factory_setup[1]
    with pytest.raises(ScrapliException) as exc:
        Factory(platform=True, transport=transport)
    assert str(exc.value) == "Argument `platform` must be `str` got `<class 'bool'>`"


@pytest.mark.parametrize(
    "factory_setup",
    [(Scrapli, "system", NetworkDriver), (AsyncScrapli, "asyncssh", AsyncNetworkDriver)],
    ids=["sync_factory", "async_factory"],
)
def test_factory_community_platform_defaults(factory_setup):
    Factory = factory_setup[0]
    transport = factory_setup[1]
    expected_driver = factory_setup[2]
    driver = Factory(platform="scrapli_networkdriver", host="localhost", transport=transport)
    assert isinstance(driver, expected_driver)
    assert driver._transport == transport
    assert driver.failed_when_contains == [
        "% Ambiguous command",
        "% Incomplete command",
        "% Invalid input detected",
        "% Unknown command",
    ]
    assert driver.textfsm_platform == "cisco_iosxe"
    assert driver.genie_platform == "iosxe"
    assert driver.default_desired_privilege_level == "privilege_exec"
    assert callable(driver.on_open)
    assert callable(driver.on_close)
    for actual_priv_level, expected_priv_level in zip(
        driver.privilege_levels.values(), TEST_COMMUNITY_PRIV_LEVELS.values()
    ):
        actual_priv_level.name == expected_priv_level.name
        actual_priv_level.pattern == expected_priv_level.pattern


@pytest.mark.parametrize(
    "factory_setup",
    [(Scrapli, "system", NetworkDriver), (AsyncScrapli, "asyncssh", AsyncNetworkDriver)],
    ids=["sync_factory", "async_factory"],
)
def test_factory_community_platform_variant(factory_setup):
    Factory = factory_setup[0]
    transport = factory_setup[1]
    expected_driver = factory_setup[2]
    driver = Factory(
        platform="scrapli_networkdriver",
        host="localhost",
        variant="test_variant1",
        transport=transport,
    )
    assert isinstance(driver, expected_driver)
    assert driver._transport == transport
    assert driver.failed_when_contains == [
        "% Ambiguous command",
        "% Incomplete command",
        "% Invalid input detected",
        "% Unknown command",
    ]
    assert driver.textfsm_platform == "cisco_iosxe"
    assert driver.genie_platform == "iosxe"
    assert driver.default_desired_privilege_level == "configuration"
    assert callable(driver.on_open)
    assert callable(driver.on_close)
    for actual_priv_level, expected_priv_level in zip(
        driver.privilege_levels.values(), TEST_COMMUNITY_PRIV_LEVELS.values()
    ):
        actual_priv_level.name == expected_priv_level.name
        actual_priv_level.pattern == expected_priv_level.pattern


@pytest.mark.parametrize(
    "factory_setup",
    [
        (Scrapli, "system", "ScrapliNetworkDriverWithMethods"),
        (AsyncScrapli, "asyncssh", "AsyncScrapliNetworkDriverWithMethods"),
    ],
    ids=["sync_factory", "async_factory"],
)
def test_factory_community_platform_variant_driver_type(factory_setup):
    Factory = factory_setup[0]
    transport = factory_setup[1]
    expected_driver_name = factory_setup[2]
    driver = Factory(
        platform="scrapli_networkdriver",
        host="localhost",
        variant="test_variant2",
        transport=transport,
    )
    assert type(driver).__name__ == expected_driver_name
    assert driver._transport == transport
    assert driver.failed_when_contains == [
        "% Ambiguous command",
        "% Incomplete command",
        "% Invalid input detected",
        "% Unknown command",
    ]
    assert driver.textfsm_platform == "cisco_iosxe"
    assert driver.genie_platform == "iosxe"
    assert driver.default_desired_privilege_level == "privilege_exec"
    assert callable(driver.on_open)
    assert callable(driver.on_close)
    for actual_priv_level, expected_priv_level in zip(
        driver.privilege_levels.values(), TEST_COMMUNITY_PRIV_LEVELS.values()
    ):
        actual_priv_level.name == expected_priv_level.name
        actual_priv_level.pattern == expected_priv_level.pattern


def test_factory_no_scrapli_community(monkeypatch):
    def mock_import_module(name):
        raise ModuleNotFoundError

    monkeypatch.setattr(importlib, "import_module", mock_import_module)

    with pytest.raises(ModuleNotFoundError) as exc:
        _get_community_platform_details(community_platform_name="blah")
    assert (
        str(exc.value)
        == "\n***** Module 'None' not found! ********************************************************\nTo resolve this issue, ensure you have the scrapli community package installed. You can install this with pip: `pip install scrapli_community`.\n***** Module 'None' not found! ********************************************************"
    )


def test_factory_no_scrapli_community_platform():
    with pytest.raises(ModuleNotFoundError) as exc:
        _get_community_platform_details(community_platform_name="blah")
    assert (
        str(exc.value)
        == "\n***** Platform 'blah' not found! ******************************************************\nTo resolve this issue, ensure you have the correct platform name, and that a scrapli  community platform of that name exists!\n***** Platform 'blah' not found! ******************************************************"
    )
