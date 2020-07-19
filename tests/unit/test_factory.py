import pytest

from scrapli.driver.core import EOSDriver, IOSXEDriver, IOSXRDriver, JunosDriver, NXOSDriver
from scrapli.exceptions import ScrapliException
from scrapli.factory import Scrapli, _get_core_driver


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


def test_sync_factory_async_transport_exception():
    with pytest.raises(ScrapliException) as exc:
        Scrapli(transport="asyncssh")
    assert str(exc.value) == "Use `AsyncScrapli` if using an async transport!"


def test_sync_factory_community_driver_exception():
    with pytest.raises(ScrapliException) as exc:
        Scrapli(platform="tacocat")
    assert str(exc.value) == "Community platform support/factory coming soon!"


def test_sync_factory_no_platform_argument():
    with pytest.raises(ScrapliException) as exc:
        Scrapli()
    assert str(exc.value) == "Argument `platform` must be provided when using `Scrapli` factory!"


def test_sync_factory_platform_bad_type():
    with pytest.raises(ScrapliException) as exc:
        Scrapli(platform=True)
    assert str(exc.value) == "Argument `platform` must be `str` got `<class 'bool'>`"


def test_get_core_driver_failure():
    with pytest.raises(ScrapliException) as exc:
        _get_core_driver(driver="tacocat")
    assert (
        str(exc.value)
        == "Error importing core driver `tacocat`; exception: `module 'scrapli.driver.core' has no attribute 'tacocat'`"
    )
