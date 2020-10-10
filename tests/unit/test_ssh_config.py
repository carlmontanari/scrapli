import os
import sys
from pathlib import Path

import pytest

import scrapli
from scrapli.ssh_config import Host, SSHConfig, SSHKnownHosts

TEST_DATA_DIR = f"{Path(scrapli.__file__).parents[1]}/tests/test_data"


def test_str():
    ssh_conf = SSHConfig(f"{TEST_DATA_DIR}/files/_ssh_config")
    assert str(ssh_conf) == "SSHConfig Object"


@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="not currently testing ssh file resolution on windows"
)
def test_repr():
    ssh_conf = SSHConfig(f"{TEST_DATA_DIR}/files/_ssh_config")
    assert repr(ssh_conf) == (
        f"SSHConfig {{'ssh_config_file': '{TEST_DATA_DIR}/files/_ssh_config', 'hosts': {{'1.2.3.4 someswitch1': Host {{'hosts': '1.2.3.4 someswitch1', 'hostname': 'someswitch1.bogus.com', 'port': 1234, 'user': 'carl', 'address_family': None, 'bind_address': None, 'connect_timeout': None, 'identities_only': 'yes', 'identity_file': '{os.path.expanduser('~')}/.ssh/mysshkey', 'keyboard_interactive': None, 'password_authentication': None, 'preferred_authentication': None}}, 'someswitch?': Host {{'hosts': 'someswitch?', 'hostname': 'someswitch1.bogus.com', 'port': 1234, 'user': 'notcarl', 'address_family': None, 'bind_address': None, 'connect_timeout': None, 'identities_only': 'yes', 'identity_file': '{os.path.expanduser('~')}/.ssh/mysshkey', 'keyboard_interactive': None, 'password_authentication': None, 'preferred_authentication': None}}, 'scrapli': Host {{'hosts': 'scrapli', 'hostname': None, 'port': None, 'user': 'scrapli', 'address_family': None, 'bind_address': None, 'connect_timeout': None, 'identities_only': None, 'identity_file': '{os.path.expanduser('~')}/.ssh/lastresortkey', 'keyboard_interactive': None, 'password_authentication': None, 'preferred_authentication': None}}, '*': Host {{'hosts': '*', 'hostname': None, 'port': None, 'user': 'somebodyelse', 'address_family': None, 'bind_address': None, 'connect_timeout': None, 'identities_only': None, 'identity_file': '{os.path.expanduser('~')}/.ssh/lastresortkey', 'keyboard_interactive': None, 'password_authentication': None, 'preferred_authentication': None}}}}}}"
    )


def test_bool_true():
    ssh_conf = SSHConfig(f"{TEST_DATA_DIR}/files/_ssh_config")
    assert bool(ssh_conf) is True


def test_bool_false():
    ssh_conf = SSHConfig(f"{TEST_DATA_DIR}/files/__init__.py")
    assert bool(ssh_conf) is False


def test_host__str():
    host = Host()
    assert str(host) == "Host: "


@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="not currently testing ssh file resolution on windows"
)
def test_host__repr():
    ssh_conf = SSHConfig(f"{TEST_DATA_DIR}/files/_ssh_config")
    assert repr(ssh_conf.hosts["1.2.3.4 someswitch1"]) == (
        "Host {'hosts': '1.2.3.4 someswitch1', 'hostname': 'someswitch1.bogus.com', 'port': "
        "1234, 'user': 'carl', 'address_family': None, 'bind_address': None, 'connect_timeout': "
        f"None, 'identities_only': 'yes', 'identity_file': '{os.path.expanduser('~')}/.ssh/mysshkey', "
        "'keyboard_interactive': None, 'password_authentication': None, 'preferred_authentication': "
        "None}"
    )


def test_init_ssh_config_invalid_config():
    with pytest.raises(TypeError) as exc:
        SSHConfig(None)
    assert str(exc.value) == "`ssh_config_file` expected str, got <class 'NoneType'>"


def test_init_ssh_config_file_explicit():
    ssh_conf = SSHConfig(f"{TEST_DATA_DIR}/files/_ssh_config")
    with open(f"{TEST_DATA_DIR}/files/_ssh_config", "r") as f:
        ssh_config_file = f.read()
    assert ssh_conf.ssh_config == ssh_config_file


def test_init_ssh_config_file_no_config_file(fs):
    ssh_conf = SSHConfig("")
    # should only have a single splat host w/ all values set to None/empty
    assert ["*"] == list(ssh_conf.hosts.keys())
    assert ssh_conf.hosts["*"].hosts == "*"
    assert ssh_conf.hosts["*"].hostname is None
    assert ssh_conf.hosts["*"].port is None
    assert ssh_conf.hosts["*"].user == ""
    assert ssh_conf.hosts["*"].address_family is None
    assert ssh_conf.hosts["*"].bind_address is None
    assert ssh_conf.hosts["*"].connect_timeout is None
    assert ssh_conf.hosts["*"].identities_only is None
    assert ssh_conf.hosts["*"].identity_file is None
    assert ssh_conf.hosts["*"].keyboard_interactive is None
    assert ssh_conf.hosts["*"].password_authentication is None
    assert ssh_conf.hosts["*"].preferred_authentication is None


def test_init_ssh_config_file_no_hosts():
    ssh_conf = SSHConfig(f"{TEST_DATA_DIR}/files/__init__.py")
    assert ["*"] == list(ssh_conf.hosts.keys())
    assert ssh_conf.hosts["*"].hosts == "*"
    assert ssh_conf.hosts["*"].hostname is None
    assert ssh_conf.hosts["*"].port is None
    assert ssh_conf.hosts["*"].user == ""
    assert ssh_conf.hosts["*"].address_family is None
    assert ssh_conf.hosts["*"].bind_address is None
    assert ssh_conf.hosts["*"].connect_timeout is None
    assert ssh_conf.hosts["*"].identities_only is None
    assert ssh_conf.hosts["*"].identity_file is None
    assert ssh_conf.hosts["*"].keyboard_interactive is None
    assert ssh_conf.hosts["*"].password_authentication is None
    assert ssh_conf.hosts["*"].preferred_authentication is None


@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="not currently testing ssh file resolution on windows"
)
def test_host_lookup_exact_host():
    ssh_conf = SSHConfig(f"{TEST_DATA_DIR}/files/_ssh_config")
    host = ssh_conf.lookup("1.2.3.4 someswitch1")
    assert repr(host) == (
        "Host {'hosts': '1.2.3.4 someswitch1', 'hostname': 'someswitch1.bogus.com', 'port': "
        "1234, 'user': 'carl', 'address_family': None, 'bind_address': None, 'connect_timeout': "
        f"None, 'identities_only': 'yes', 'identity_file': '{os.path.expanduser('~')}/.ssh/mysshkey', "
        "'keyboard_interactive': None, 'password_authentication': None, 'preferred_authentication':"
        " None}"
    )


@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="not currently testing ssh file resolution on windows"
)
def test_host_lookup_exact_host_in_list():
    ssh_conf = SSHConfig(f"{TEST_DATA_DIR}/files/_ssh_config")
    host = ssh_conf.lookup("someswitch1")
    assert repr(host) == (
        "Host {'hosts': '1.2.3.4 someswitch1', 'hostname': 'someswitch1.bogus.com', 'port': "
        "1234, 'user': 'carl', 'address_family': None, 'bind_address': None, 'connect_timeout': "
        f"None, 'identities_only': 'yes', 'identity_file': '{os.path.expanduser('~')}/.ssh/mysshkey', "
        "'keyboard_interactive': None, 'password_authentication': None, 'preferred_authentication':"
        " None}"
    )


@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="not currently testing ssh file resolution on windows"
)
def test_host_lookup_host_fuzzy():
    ssh_conf = SSHConfig(f"{TEST_DATA_DIR}/files/_ssh_config")
    host = ssh_conf.lookup("someswitch2")
    assert repr(host) == (
        "Host {'hosts': 'someswitch?', 'hostname': 'someswitch1.bogus.com', 'port': "
        "1234, 'user': 'notcarl', 'address_family': None, 'bind_address': None, 'connect_timeout': "
        f"None, 'identities_only': 'yes', 'identity_file': '{os.path.expanduser('~')}/.ssh/mysshkey', "
        "'keyboard_interactive': None, 'password_authentication': None, 'preferred_authentication': "
        "None}"
    )


@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="not currently testing ssh file resolution on windows"
)
def test_host_lookup_host_fuzzy_multi_match():
    ssh_conf = SSHConfig(f"{TEST_DATA_DIR}/files/_ssh_config")
    host = ssh_conf.lookup("someswitch9999")
    assert repr(host) == (
        "Host {'hosts': 'someswitch?', 'hostname': 'someswitch1.bogus.com', 'port': "
        "1234, 'user': 'notcarl', 'address_family': None, 'bind_address': None, 'connect_timeout': "
        f"None, 'identities_only': 'yes', 'identity_file': '{os.path.expanduser('~')}/.ssh/mysshkey', "
        "'keyboard_interactive': None, 'password_authentication': None, 'preferred_authentication': "
        "None}"
    )


@pytest.mark.skipif(
    sys.platform.startswith("win"), reason="not currently testing ssh file resolution on windows"
)
def test_host_lookup_merged_data():
    ssh_conf = SSHConfig(f"{TEST_DATA_DIR}/files/_ssh_config")
    host = ssh_conf.lookup("scrapli")
    assert repr(host) == (
        "Host {'hosts': 'scrapli', 'hostname': None, 'port': None, 'user': 'scrapli', 'address_family': None, "
        "'bind_address': None, 'connect_timeout': None, 'identities_only': None, 'identity_file': "
        f"'{os.path.expanduser('~')}/.ssh/lastresortkey', 'keyboard_interactive': None, 'password_authentication': None, "
        "'preferred_authentication': None}"
    )


def test_init_ssh_known_hosts_file_explicit():
    known_hosts = SSHKnownHosts(f"{TEST_DATA_DIR}/files/_ssh_known_hosts")
    with open(f"{TEST_DATA_DIR}/files/_ssh_known_hosts", "r") as f:
        ssh_known_hosts = f.read()
    assert known_hosts.ssh_known_hosts == ssh_known_hosts


def test_init_ssh_known_hosts_file_no_config_file(fs):
    known_hosts = SSHKnownHosts("")
    assert known_hosts.hosts == {}


def test_init_ssh_known_hosts_file_no_hosts():
    known_hosts = SSHKnownHosts(f"{TEST_DATA_DIR}/files/__init__.py")
    assert known_hosts.hosts == {}
