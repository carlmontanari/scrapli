import importlib

import pytest

from scrapli.driver import AsyncNetworkDriver, NetworkDriver
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
from scrapli.driver.network.base_driver import PrivilegeLevel
from scrapli.exceptions import ScrapliModuleNotFound, ScrapliTypeError, ScrapliValueError
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
    "test_data",
    [
        ("cisco_iosxe", IOSXEDriver),
        ("cisco_iosxr", IOSXRDriver),
        ("cisco_nxos", NXOSDriver),
        ("arista_eos", EOSDriver),
        ("juniper_junos", JunosDriver),
    ],
    ids=["cisco_iosxe", "cisco_iosxr", "cisco_nxos", "arista_eos", "juniper_junos"],
)
def test_sync_factory(test_data):
    platform, expected_platform_class = test_data
    driver = Scrapli(platform=platform, host="localhost", transport="system")
    assert isinstance(driver, expected_platform_class)


@pytest.mark.parametrize(
    "test_data",
    [
        ("cisco_iosxe", AsyncIOSXEDriver),
        ("cisco_iosxr", AsyncIOSXRDriver),
        ("cisco_nxos", AsyncNXOSDriver),
        ("arista_eos", AsyncEOSDriver),
        ("juniper_junos", AsyncJunosDriver),
    ],
    ids=["cisco_iosxe", "cisco_iosxr", "cisco_nxos", "arista_eos", "juniper_junos"],
)
def test_async_factory(test_data):
    platform, expected_platform_class = test_data
    driver = AsyncScrapli(platform=platform, host="localhost", transport="asynctelnet")
    assert isinstance(driver, expected_platform_class)


def test_sync_factory_async_transport_exception():
    with pytest.raises(ScrapliValueError) as exc:
        Scrapli(platform="cisco_iosxe", host="localhost", transport="asyncssh")
    assert str(exc.value) == "Use 'AsyncScrapli' if using an async transport!"


def test_async_factory_sync_transport_exception():
    with pytest.raises(ScrapliValueError) as exc:
        AsyncScrapli(platform="cisco_iosxe", host="localhost", transport="system")
    assert str(exc.value) == "Use 'Scrapli' if using a synchronous transport!"


@pytest.mark.parametrize(
    "test_data",
    [(Scrapli, "system"), (AsyncScrapli, "asyncssh")],
    ids=["sync_factory", "async_factory"],
)
def test_factory_platform_bad_type(test_data):
    Factory, transport = test_data
    with pytest.raises(ScrapliTypeError) as exc:
        Factory(platform=True, host="localhost", transport=transport)
    assert str(exc.value) == "Argument 'platform' must be 'str' got '<class 'bool'>'"


@pytest.mark.parametrize(
    "test_data",
    [(Scrapli, "system", NetworkDriver), (AsyncScrapli, "asyncssh", AsyncNetworkDriver)],
    ids=["sync_factory", "async_factory"],
)
def test_factory_community_platform_defaults(test_data):
    Factory, transport, expected_driver = test_data
    driver = Factory(platform="scrapli_networkdriver", host="localhost", transport=transport)
    assert isinstance(driver, expected_driver)
    assert driver.transport_name == transport
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
        assert actual_priv_level.name == expected_priv_level.name
        assert actual_priv_level.pattern == expected_priv_level.pattern


@pytest.mark.parametrize(
    "test_data",
    [(Scrapli, "system", NetworkDriver), (AsyncScrapli, "asyncssh", AsyncNetworkDriver)],
    ids=["sync_factory", "async_factory"],
)
def test_factory_community_platform_variant(test_data):
    Factory, transport, expected_driver = test_data
    driver = Factory(
        platform="scrapli_networkdriver",
        host="localhost",
        variant="test_variant1",
        transport=transport,
    )
    assert isinstance(driver, expected_driver)
    assert driver.transport_name == transport
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
        assert actual_priv_level.name == expected_priv_level.name
        assert actual_priv_level.pattern == expected_priv_level.pattern


@pytest.mark.parametrize(
    "test_data",
    [
        (Scrapli, "system", "ScrapliNetworkDriverWithMethods"),
        (AsyncScrapli, "asyncssh", "AsyncScrapliNetworkDriverWithMethods"),
    ],
    ids=["sync_factory", "async_factory"],
)
def test_factory_community_platform_variant_driver_type(test_data):
    Factory, transport, expected_driver = test_data
    driver = Factory(
        platform="scrapli_networkdriver",
        host="localhost",
        variant="test_variant2",
        transport=transport,
    )
    assert type(driver).__name__ == expected_driver
    assert driver.transport_name == transport
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
        assert actual_priv_level.name == expected_priv_level.name
        assert actual_priv_level.pattern == expected_priv_level.pattern


def test_factory_no_scrapli_community(monkeypatch):
    def mock_import_module(name):
        raise ModuleNotFoundError

    monkeypatch.setattr(importlib, "import_module", mock_import_module)

    with pytest.raises(ScrapliModuleNotFound) as exc:
        _get_community_platform_details(community_platform_name="blah")
    assert "Module not found!" in str(exc.value)


def test_factory_no_scrapli_community_platform():
    with pytest.raises(ScrapliModuleNotFound) as exc:
        _get_community_platform_details(community_platform_name="blah")
    assert "Scrapli Community platform 'blah` not found!" in str(exc.value)
