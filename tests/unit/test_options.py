"""tests.unit.test_options"""

from ctypes import pointer

import pytest

from scrapli.auth import Options as AuthOptions
from scrapli.ffi_options import DriverOptions
from scrapli.transport import BinOptions, Ssh2Options


@pytest.fixture()
def driver_options():
    opts = DriverOptions()
    return pointer(opts)


class TestAuthOptionsPrivateKey:
    def test_apply_sets_private_key(self, driver_options):
        auth = AuthOptions(private_key="-----BEGIN OPENSSH PRIVATE KEY-----\nfake\n-----END OPENSSH PRIVATE KEY-----")
        auth.apply(options=driver_options)

        assert driver_options.contents.auth.private_key is not None
        assert driver_options.contents.auth.private_key_len > 0

    def test_apply_does_not_set_private_key_when_none(self, driver_options):
        auth = AuthOptions(username="admin")
        auth.apply(options=driver_options)

        assert driver_options.contents.auth.private_key_len == 0

    def test_apply_sets_both_private_key_and_path(self, driver_options):
        auth = AuthOptions(
            private_key="key-content",
            private_key_path="/home/user/.ssh/id_rsa",
        )
        auth.apply(options=driver_options)

        assert driver_options.contents.auth.private_key_len > 0
        assert driver_options.contents.auth.private_key_path_len > 0


class TestBinOptionsKnownHosts:
    def test_apply_sets_known_hosts(self, driver_options):
        transport = BinOptions(known_hosts="host.example.com ssh-rsa AAAA...")
        transport.apply(options=driver_options)

        assert driver_options.contents.transport.bin.known_hosts is not None
        assert driver_options.contents.transport.bin.known_hosts_len > 0

    def test_apply_does_not_set_known_hosts_when_none(self, driver_options):
        transport = BinOptions()
        transport.apply(options=driver_options)

        assert driver_options.contents.transport.bin.known_hosts_len == 0

    def test_apply_sets_both_known_hosts_and_path(self, driver_options):
        transport = BinOptions(
            known_hosts="host.example.com ssh-rsa AAAA...",
            known_hosts_path="/home/user/.ssh/known_hosts",
        )
        transport.apply(options=driver_options)

        assert driver_options.contents.transport.bin.known_hosts_len > 0
        assert driver_options.contents.transport.bin.known_hosts_path_len > 0


class TestSsh2OptionsKnownHosts:
    def test_apply_sets_known_hosts(self, driver_options):
        transport = Ssh2Options(known_hosts="host.example.com ssh-rsa AAAA...")
        transport.apply(options=driver_options)

        assert driver_options.contents.transport.ssh2.known_hosts is not None
        assert driver_options.contents.transport.ssh2.known_hosts_len > 0

    def test_apply_does_not_set_known_hosts_when_none(self, driver_options):
        transport = Ssh2Options()
        transport.apply(options=driver_options)

        assert driver_options.contents.transport.ssh2.known_hosts_len == 0

    def test_apply_sets_both_known_hosts_and_path(self, driver_options):
        transport = Ssh2Options(
            known_hosts="host.example.com ssh-rsa AAAA...",
            known_hosts_path="/home/user/.ssh/known_hosts",
        )
        transport.apply(options=driver_options)

        assert driver_options.contents.transport.ssh2.known_hosts_len > 0
        assert driver_options.contents.transport.ssh2.known_hosts_path_len > 0
