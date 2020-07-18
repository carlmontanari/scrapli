import pytest

from scrapli.driver.core import EOSDriver, IOSXEDriver, IOSXRDriver, JunosDriver, NXOSDriver
from scrapli.exceptions import ScrapliException
from scrapli.factory import Scrapli


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


def test_sync_factory_community_driver_exception():
    with pytest.raises(ScrapliException) as exc:
        Scrapli(platform="tacocat")
    assert str(exc.value) == "Community platform support/factory coming soon!"
