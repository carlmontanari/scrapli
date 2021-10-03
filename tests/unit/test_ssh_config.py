import os

import pytest

from scrapli.exceptions import ScrapliTypeError
from scrapli.ssh_config import Host, SSHConfig, SSHKnownHosts, ssh_config_factory


def test_str(real_ssh_config_file_path):
    ssh_conf = SSHConfig(real_ssh_config_file_path)
    assert str(ssh_conf) == "SSHConfig Object"


def test_repr(real_ssh_config_file_path):
    ssh_conf = SSHConfig(real_ssh_config_file_path)
    assert repr(ssh_conf) == (
        f"SSHConfig {{'ssh_config_file': '{real_ssh_config_file_path}', 'hosts': {{'1.2.3.4 someswitch1': Host {{'hosts': '1.2.3.4 someswitch1', 'hostname': 'someswitch1.bogus.com', 'port': 1234, 'user': 'carl', 'address_family': None, 'bind_address': None, 'connect_timeout': None, 'identities_only': 'yes', 'identity_file': '{os.path.expanduser('~')}/.ssh/mysshkey', 'keyboard_interactive': None, 'password_authentication': None, 'preferred_authentication': None}}, 'someswitch?': Host {{'hosts': 'someswitch?', 'hostname': 'someswitch1.bogus.com', 'port': 1234, 'user': 'notcarl', 'address_family': None, 'bind_address': None, 'connect_timeout': None, 'identities_only': 'yes', 'identity_file': '{os.path.expanduser('~')}/.ssh/mysshkey', 'keyboard_interactive': None, 'password_authentication': None, 'preferred_authentication': None}}, 'scrapli': Host {{'hosts': 'scrapli', 'hostname': None, 'port': None, 'user': 'scrapli', 'address_family': None, 'bind_address': None, 'connect_timeout': None, 'identities_only': None, 'identity_file': '{os.path.expanduser('~')}/.ssh/lastresortkey', 'keyboard_interactive': None, 'password_authentication': None, 'preferred_authentication': None}}, '*': Host {{'hosts': '*', 'hostname': None, 'port': None, 'user': 'somebodyelse', 'address_family': None, 'bind_address': None, 'connect_timeout': None, 'identities_only': None, 'identity_file': '{os.path.expanduser('~')}/.ssh/lastresortkey', 'keyboard_interactive': None, 'password_authentication': None, 'preferred_authentication': None}}}}}}"
    )


def test_bool_true(real_ssh_config_file_path):
    ssh_conf = SSHConfig(real_ssh_config_file_path)
    assert bool(ssh_conf) is True


def test_bool_false(test_data_path):
    ssh_conf = SSHConfig(f"{test_data_path}/files/__init__.py")
    assert bool(ssh_conf) is False


def test_host__str():
    host = Host()
    assert str(host) == "Host: "


def test_host__repr(real_ssh_config_file_path):
    ssh_conf = SSHConfig(real_ssh_config_file_path)
    assert repr(ssh_conf.hosts["1.2.3.4 someswitch1"]) == (
        "Host {'hosts': '1.2.3.4 someswitch1', 'hostname': 'someswitch1.bogus.com', 'port': "
        "1234, 'user': 'carl', 'address_family': None, 'bind_address': None, 'connect_timeout': "
        f"None, 'identities_only': 'yes', 'identity_file': '{os.path.expanduser('~')}/.ssh/mysshkey', "
        "'keyboard_interactive': None, 'password_authentication': None, 'preferred_authentication': "
        "None}"
    )


def test_init_ssh_config_invalid_config():
    with pytest.raises(ScrapliTypeError) as exc:
        SSHConfig(None)
    assert str(exc.value) == "`ssh_config_file` expected str, got <class 'NoneType'>"


def test_init_ssh_config_file_explicit(real_ssh_config_file_path):
    ssh_conf = SSHConfig(real_ssh_config_file_path)
    with open(real_ssh_config_file_path, "r") as f:
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


def test_init_ssh_config_file_no_hosts(test_data_path):
    ssh_conf = SSHConfig(f"{test_data_path}/files/__init__.py")
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


def test_host_lookup_exact_host(real_ssh_config_file_path):
    ssh_conf = SSHConfig(real_ssh_config_file_path)
    host = ssh_conf.lookup("1.2.3.4 someswitch1")
    assert repr(host) == (
        "Host {'hosts': '1.2.3.4 someswitch1', 'hostname': 'someswitch1.bogus.com', 'port': "
        "1234, 'user': 'carl', 'address_family': None, 'bind_address': None, 'connect_timeout': "
        f"None, 'identities_only': 'yes', 'identity_file': '{os.path.expanduser('~')}/.ssh/mysshkey', "
        "'keyboard_interactive': None, 'password_authentication': None, 'preferred_authentication':"
        " None}"
    )


def test_host_lookup_exact_host_in_list(real_ssh_config_file_path):
    ssh_conf = SSHConfig(real_ssh_config_file_path)
    host = ssh_conf.lookup("someswitch1")
    assert repr(host) == (
        "Host {'hosts': '1.2.3.4 someswitch1', 'hostname': 'someswitch1.bogus.com', 'port': "
        "1234, 'user': 'carl', 'address_family': None, 'bind_address': None, 'connect_timeout': "
        f"None, 'identities_only': 'yes', 'identity_file': '{os.path.expanduser('~')}/.ssh/mysshkey', "
        "'keyboard_interactive': None, 'password_authentication': None, 'preferred_authentication':"
        " None}"
    )


def test_host_lookup_host_fuzzy(real_ssh_config_file_path):
    ssh_conf = SSHConfig(real_ssh_config_file_path)
    host = ssh_conf.lookup("someswitch2")
    assert repr(host) == (
        "Host {'hosts': 'someswitch?', 'hostname': 'someswitch1.bogus.com', 'port': "
        "1234, 'user': 'notcarl', 'address_family': None, 'bind_address': None, 'connect_timeout': "
        f"None, 'identities_only': 'yes', 'identity_file': '{os.path.expanduser('~')}/.ssh/mysshkey', "
        "'keyboard_interactive': None, 'password_authentication': None, 'preferred_authentication': "
        "None}"
    )


def test_host_lookup_host_fuzzy_multi_match(real_ssh_config_file_path):
    ssh_conf = SSHConfig(real_ssh_config_file_path)
    host = ssh_conf.lookup("someswitch9999")
    assert repr(host) == (
        "Host {'hosts': 'someswitch?', 'hostname': 'someswitch1.bogus.com', 'port': "
        "1234, 'user': 'notcarl', 'address_family': None, 'bind_address': None, 'connect_timeout': "
        f"None, 'identities_only': 'yes', 'identity_file': '{os.path.expanduser('~')}/.ssh/mysshkey', "
        "'keyboard_interactive': None, 'password_authentication': None, 'preferred_authentication': "
        "None}"
    )


def test_host_lookup_merged_data(real_ssh_config_file_path):
    ssh_conf = SSHConfig(real_ssh_config_file_path)
    host = ssh_conf.lookup("scrapli")
    assert repr(host) == (
        "Host {'hosts': 'scrapli', 'hostname': None, 'port': None, 'user': 'scrapli', 'address_family': None, "
        "'bind_address': None, 'connect_timeout': None, 'identities_only': None, 'identity_file': "
        f"'{os.path.expanduser('~')}/.ssh/lastresortkey', 'keyboard_interactive': None, 'password_authentication': None, "
        "'preferred_authentication': None}"
    )


def test_init_ssh_known_hosts_file_exceptions():
    with pytest.raises(TypeError) as exc:
        SSHKnownHosts(None)
    assert str(exc.value) == "`ssh_known_hosts_file` expected str, got <class 'NoneType'>"


def test_init_ssh_known_hosts_file_explicit(real_ssh_known_hosts_file_path):
    known_hosts = SSHKnownHosts(real_ssh_known_hosts_file_path)
    with open(real_ssh_known_hosts_file_path, "r") as f:
        ssh_known_hosts = f.read()
    assert known_hosts.ssh_known_hosts == ssh_known_hosts


def test_init_ssh_known_hosts_file_no_config_file(fs):
    known_hosts = SSHKnownHosts("")
    assert known_hosts.hosts == {}


def test_init_ssh_known_hosts_file_no_hosts(test_data_path):
    known_hosts = SSHKnownHosts(f"{test_data_path}/files/__init__.py")
    assert known_hosts.hosts == {}


def test_known_host_lookup_exact_host(real_ssh_known_hosts_file_path):
    known_hosts = SSHKnownHosts(real_ssh_known_hosts_file_path)
    assert known_hosts.lookup("172.18.0.11") != {}


def test_known_host_lookup_exact_host_hashed(real_ssh_known_hosts_file_path):
    known_hosts = SSHKnownHosts(real_ssh_known_hosts_file_path)
    # remove the non-hashed known host entry in the loaded dict, leaving only the hashed entry
    del known_hosts.hosts["172.18.0.11"]
    assert known_hosts.lookup("172.18.0.11") != {}


def test_known_host_lookup_bad_host(real_ssh_known_hosts_file_path):
    known_hosts = SSHKnownHosts(real_ssh_known_hosts_file_path)
    assert known_hosts.lookup("bad.host") == {}


def test_ssh_config_factory(real_ssh_config_file_path):
    # *probably* the ssh config file is already in the loaded dict, so we'll empty it before testing
    SSHConfig._config_files = {}
    assert not SSHConfig._config_files
    _ = ssh_config_factory(ssh_config_file=real_ssh_config_file_path)
    assert real_ssh_config_file_path in SSHConfig._config_files
