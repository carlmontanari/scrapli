import logging
from pathlib import Path

import pytest

from scrapli.driver.base.base_driver import BaseDriver
from scrapli.exceptions import ScrapliTransportPluginError, ScrapliTypeError, ScrapliValueError


def test_str(base_driver):
    assert str(base_driver) == "Scrapli Driver localhost:22"


def test_repr(base_driver):
    base_driver.auth_password = "scrapli"
    base_driver.auth_private_key_passphrase = "scrapli"
    actual_repr = repr(base_driver)
    assert actual_repr.count("REDACTED", 2)


@pytest.mark.parametrize("test_data", (("tacocat   ", "tacocat"),), ids=("host_strip",))
def test_setup_host(base_driver, test_data):
    input_host, expected_host = test_data
    actual_host, _ = base_driver._setup_host(host=input_host, port=22)
    assert expected_host == actual_host


@pytest.mark.parametrize(
    "test_data",
    ((None, 22, ScrapliValueError), ("localhost", None, ScrapliTypeError)),
    ids=("invalid_host", "invalid_port"),
)
def test_setup_host_exceptions(base_driver, test_data):
    host, port, expected_exception = test_data

    with pytest.raises(expected_exception):
        base_driver._setup_host(host=host, port=port)


@pytest.mark.parametrize(
    "test_data",
    (
        (("", False, False), ("", False, False)),
        ((__file__, False, False), (__file__, False, False)),
    ),
    ids=("no_private_key", "resolve_private_key"),
)
def test_setup_auth(base_driver, test_data):
    input_data, expected_outputs = test_data
    actual_outputs = base_driver._setup_auth(*input_data)
    assert expected_outputs == actual_outputs


@pytest.mark.parametrize(
    "test_data",
    (
        ("", None, False),
        ("", False, None),
    ),
    ids=("invalid_auth_strict_key", "invalid_auth_bypass"),
)
def test_setup_auth_exceptions(base_driver, test_data):
    input_data = test_data
    with pytest.raises(ScrapliTypeError):
        base_driver._setup_auth(*input_data)


@pytest.mark.parametrize(
    "test_data",
    (
        "telnet",
        "asynctelnet",
    ),
    ids=("telnet_transport", "asynctelnet_transport"),
)
def test_setup_ssh_file_args_telnet_transport(caplog, base_driver, test_data):
    """Assert ssh_args are ignored with telnet transport(s)"""
    transport_name = test_data

    caplog.set_level(logging.DEBUG, logger="scrapli.driver")

    actual_outputs = base_driver._setup_ssh_file_args(
        transport=transport_name, ssh_config_file="", ssh_known_hosts_file=""
    )
    assert ("", "") == actual_outputs

    log_record = next(iter(caplog.records))
    assert "telnet-based transport selected, ignoring ssh file arguments" == log_record.msg
    assert logging.DEBUG == log_record.levelno


def test_update_ssh_args_from_ssh_config(fs, real_ssh_config_file_path, base_driver):
    fs.add_real_file(source_path=real_ssh_config_file_path, target_path="ssh_config")
    base_driver.ssh_config_file = "ssh_config"
    base_driver.host = "1.2.3.4"
    base_driver.port = 0
    base_driver.auth_username = ""
    base_driver.auth_private_key = ""

    base_driver._update_ssh_args_from_ssh_config()

    assert base_driver.port == 1234
    assert base_driver.auth_username == "carl"
    assert base_driver.auth_private_key == str(Path("~/.ssh/mysshkey").expanduser())


@pytest.mark.parametrize(
    "test_data",
    (
        (
            True,
            True,
        ),
        (
            "blah",
            "blah",
        ),
    ),
    ids=("true", "unresolvable_path"),
)
def test_setup_ssh_file_args_resolved(fs, base_driver, test_data):
    """
    Assert we handle ssh config/known hosts inputs properly

    This does *not* need to test resolution as there is a test for that, this is just making sure
    that if given a non False bool or a string we properly try to resolve the ssh files
    """
    # using fakefs to ensure we dont resolve user/system config files
    _ = fs

    ssh_config_file_input, ssh_known_hosts_file_input = test_data

    resolved_ssh_config_file, resolved_ssh_known_hosts_file = base_driver._setup_ssh_file_args(
        transport="system",
        ssh_config_file=ssh_config_file_input,
        ssh_known_hosts_file=ssh_known_hosts_file_input,
    )

    assert resolved_ssh_config_file == ""
    assert resolved_ssh_known_hosts_file == ""


@pytest.mark.parametrize(
    "test_data",
    (("system", None, ""), ("system", "", None)),
    ids=("invalid_ssh_config_file", "invalid_ssh_known_hosts_file"),
)
def test_setup_ssh_file_args_exceptions(base_driver, test_data):
    """Assert ssh_args are ignored with telnet transport(s)"""
    input_data = test_data

    with pytest.raises(ScrapliTypeError):
        base_driver._setup_ssh_file_args(*input_data)


@pytest.mark.parametrize(
    "test_data", (((open, dir, input), (open, dir, input)),), ids=("callables",)
)
def test_setup_callables(base_driver, test_data):
    """Assert callables get assigned as provided"""
    input_data, expected_outputs = test_data
    base_driver._setup_callables(*input_data)
    assert (base_driver.on_init, base_driver.on_open, base_driver.on_close) == expected_outputs


@pytest.mark.parametrize(
    "test_data",
    (("", dir, input), (open, "", input), (open, dir, "")),
    ids=(
        "invalid_on_init",
        "invalid_on_open",
        "invalid_on_close",
    ),
)
def test_setup_callables(base_driver, test_data):
    """Assert _setup_callables raises exceptions if provided args are not callable"""
    input_data = test_data

    with pytest.raises(ScrapliTypeError):
        base_driver._setup_callables(*input_data)


def test_transport_factory_core(base_driver, system_transport_plugin_args):
    """Assert _transport_factory properly loads core transport plugin and args"""
    from scrapli.transport.plugins.system.transport import SystemTransport

    actual_transport_class, actual_transport_plugin_args = base_driver._transport_factory()

    assert actual_transport_class == SystemTransport
    assert actual_transport_plugin_args == system_transport_plugin_args


def test_load_core_transport_plugin_exception(monkeypatch):
    """Assert exception properly raised when core transport is un-importable for some reason"""

    def _import_module(_):
        raise ModuleNotFoundError

    monkeypatch.setattr("importlib.import_module", _import_module)

    with pytest.raises(ScrapliTransportPluginError) as exc:
        BaseDriver(host="localhost", transport="asyncssh")

    assert "Transport Plugin Extra Not Installed!" in str(exc.value)


def test_load_non_core_transport_plugin_exception(monkeypatch):
    """Assert exception properly raised when core transport is un-importable for some reason"""

    def _import_module(_):
        raise ModuleNotFoundError

    monkeypatch.setattr("importlib.import_module", _import_module)

    with pytest.raises(ScrapliTransportPluginError) as exc:
        BaseDriver(host="localhost", transport="notarealtransportplugin")

    assert "Transport Plugin Extra Not Installed!" in str(exc.value)


# TODO transport factory w/ non-core -- maybe just mock something so the tests dont depend on
#  anything external

# TODO test load core and non core transport plugins


@pytest.mark.parametrize(
    "test_data",
    [
        ("", "/etc/ssh/ssh_config", True, "/etc/ssh/ssh_config"),
        (
            "",
            str(Path("~/.ssh/config").expanduser()),
            True,
            str(Path("~/.ssh/config").expanduser()),
        ),
        ("/non_standard_ssh_config", "/non_standard_ssh_config", True, "/non_standard_ssh_config"),
        ("", "", False, ""),
    ],
    ids=("auto_etc", "auto_user", "manual_location", "no_config"),
)
def test_resolve_ssh_config(fs, real_ssh_config_file_path, base_driver, test_data):
    input_data, expected_output, mount_real_file, fake_fs_destination = test_data

    if mount_real_file:
        fs.add_real_file(source_path=real_ssh_config_file_path, target_path=fake_fs_destination)
    actual_output = base_driver._resolve_ssh_config(ssh_config_file=input_data)
    assert actual_output == expected_output


@pytest.mark.parametrize(
    "test_data",
    [
        ("", "/etc/ssh/ssh_known_hosts", True, "/etc/ssh/ssh_known_hosts"),
        (
            "",
            str(Path("~/.ssh/known_hosts").expanduser()),
            True,
            str(Path("~/.ssh/known_hosts").expanduser()),
        ),
        (
            "/non_standard_ssh_known_hosts",
            "/non_standard_ssh_known_hosts",
            True,
            "/non_standard_ssh_known_hosts",
        ),
        ("", "", False, ""),
    ],
    ids=("auto_etc", "auto_user", "manual_location", "no_config"),
)
def test_resolve_ssh_known_hosts(fs, real_ssh_known_hosts_file_path, base_driver, test_data):
    input_data, expected_output, mount_real_file, fake_fs_destination = test_data

    if mount_real_file:
        fs.add_real_file(
            source_path=real_ssh_known_hosts_file_path, target_path=fake_fs_destination
        )
    actual_output = base_driver._resolve_ssh_known_hosts(ssh_known_hosts=input_data)
    assert actual_output == expected_output


@pytest.mark.parametrize(
    "test_data",
    (True, False),
    ids=(
        "alive",
        "not_alive",
    ),
)
def test_isalive(monkeypatch, base_driver, test_data):
    """
    Assert base driver isalive works as intended

    Patches system transport isalive; that will need to be tested separately
    """
    monkeypatch.setattr(
        "scrapli.transport.plugins.system.transport.SystemTransport.isalive", lambda x: test_data
    )
    assert base_driver.isalive() is test_data


@pytest.mark.parametrize(
    "test_data",
    (True, False),
    ids=(
        "on_init",
        "no_on_init",
    ),
)
def test_on_init(test_data):
    """Assert on init method is executed at end of driver initialization (if provided)"""
    test_on_init = test_data
    on_init_called = False

    def _on_init(cls):
        nonlocal on_init_called
        on_init_called = True

    BaseDriver(host="localhost", on_init=_on_init if test_on_init else None)

    if test_on_init:
        assert on_init_called is True
    else:
        assert on_init_called is False


@pytest.mark.parametrize(
    "test_data",
    (
        (False, "opening connection to 'localhost' on port '22'"),
        (True, "closing connection to 'localhost' on port '22'"),
    ),
    ids=("opening", "closing"),
)
def test_pre_open_closing_log(caplog, base_driver, test_data):
    """Assert pre_open log message content and log level"""
    caplog.set_level(logging.DEBUG, logger="scrapli.driver")

    closing, expected_log_message = test_data
    base_driver._pre_open_closing_log(closing=closing)

    log_record = next(iter(caplog.records))
    assert expected_log_message == log_record.msg
    assert logging.INFO == log_record.levelno


@pytest.mark.parametrize(
    "test_data",
    (
        (False, "connection to 'localhost' on port '22' opened successfully"),
        (True, "connection to 'localhost' on port '22' closed successfully"),
    ),
    ids=("opening", "closing"),
)
def test_post_open_closing_log(caplog, base_driver, test_data):
    """Assert post_open log message content and log level"""
    caplog.set_level(logging.DEBUG, logger="scrapli.driver")

    closing, expected_log_message = test_data
    base_driver._post_open_closing_log(closing=closing)

    log_record = next(iter(caplog.records))
    assert expected_log_message == log_record.msg
    assert logging.INFO == log_record.levelno
