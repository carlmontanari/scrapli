import pytest

from scrapli.driver.base.sync_driver import BaseDriver
from scrapli.exceptions import ScrapliTypeError


@pytest.mark.parametrize(
    "test_data",
    (
        ("comms_prompt_pattern", "new_value"),
        ("comms_return_char", "new_value"),
        ("comms_ansi", True),
    ),
    ids=(
        "comms_prompt_pattern",
        "comms_return_char",
        "comms_ansi",
    ),
)
def test_comms_properties(base_drivers, test_data):
    """
    Assert sync driver properly sets comms property values
    """
    attribute, new_value = test_data
    original_value = getattr(base_drivers, attribute)

    assert getattr(base_drivers._base_channel_args, attribute) == original_value
    assert getattr(base_drivers.channel._base_channel_args, attribute) == original_value

    setattr(base_drivers, attribute, new_value)

    assert getattr(base_drivers, attribute) == new_value
    assert getattr(base_drivers._base_channel_args, attribute) == new_value
    assert getattr(base_drivers.channel._base_channel_args, attribute) == new_value


@pytest.mark.parametrize(
    "test_data",
    (
        ("comms_prompt_pattern", False),
        ("comms_return_char", False),
        ("comms_ansi", "new_value"),
    ),
    ids=("comms_prompt_pattern", "comms_return_char", "comms_ansi"),
)
def test_comms_properties_exception(base_drivers, test_data):
    """Assert sync driver raises an exception for invalid comms property values"""
    attribute, new_value = test_data

    with pytest.raises(ScrapliTypeError):
        setattr(base_drivers, attribute, new_value)


@pytest.mark.parametrize(
    "test_data",
    (
        ("timeout_socket", 999.99),
        ("timeout_transport", 999.99),
    ),
    ids=(
        "timeout_socket",
        "timeout_transport",
    ),
)
def test_timeout_properties_transport(base_drivers, test_data):
    """
    Assert sync driver properly sets transport related timeout values
    """
    attribute, new_value = test_data
    original_value = getattr(base_drivers, attribute)

    assert getattr(base_drivers._base_transport_args, attribute) == original_value
    assert getattr(base_drivers.transport._base_transport_args, attribute) == original_value

    setattr(base_drivers, attribute, new_value)

    assert getattr(base_drivers, attribute) == new_value
    assert getattr(base_drivers._base_transport_args, attribute) == new_value
    assert getattr(base_drivers.transport._base_transport_args, attribute) == new_value


def test_timeout_properties_transport_plugin_set_timeout(monkeypatch):
    """
    Assert sync driver properly sets transport related timeout values

    Specifically for plugins with set_timeout method -- i.e. ssh2/paramiko
    """
    monkeypatch.setattr(
        "scrapli.transport.plugins.ssh2.transport.Ssh2Transport._set_timeout",
        lambda cls, value: None,
    )

    driver = BaseDriver(host="localhost", transport="ssh2")
    assert driver.timeout_transport == 30.0
    driver.timeout_transport = 999.99
    assert driver.timeout_transport == 999.99


@pytest.mark.parametrize(
    "test_data",
    (
        ("timeout_socket", None),
        ("timeout_transport", None),
    ),
    ids=(
        "timeout_socket",
        "timeout_transport",
    ),
)
def test_timeout_properties_transport_exception(base_drivers, test_data):
    """Assert sync driver raises an exception for invalid transport timeout values"""
    attribute, new_value = test_data

    with pytest.raises(ScrapliTypeError):
        setattr(base_drivers, attribute, new_value)


@pytest.mark.parametrize(
    "test_data",
    (("timeout_ops", 999.99),),
    ids=("timeout_ops",),
)
def test_timeout_properties_channel(base_drivers, test_data):
    """
    Assert sync driver properly sets transport related timeout values
    """
    attribute, new_value = test_data
    original_value = getattr(base_drivers, attribute)

    assert getattr(base_drivers._base_channel_args, attribute) == original_value
    assert getattr(base_drivers.channel._base_channel_args, attribute) == original_value

    setattr(base_drivers, attribute, new_value)

    assert getattr(base_drivers, attribute) == new_value
    assert getattr(base_drivers._base_channel_args, attribute) == new_value
    assert getattr(base_drivers.channel._base_channel_args, attribute) == new_value


@pytest.mark.parametrize(
    "test_data",
    (("timeout_ops", None),),
    ids=("timeout_ops",),
)
def test_timeout_properties_channel_exception(base_drivers, test_data):
    """Assert sync driver raises an exception for invalid transport timeout values"""
    attribute, new_value = test_data

    with pytest.raises(ScrapliTypeError):
        setattr(base_drivers, attribute, new_value)
