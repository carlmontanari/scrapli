import pty
from io import BytesIO

import pytest

from scrapli.exceptions import (
    ScrapliConnectionError,
    ScrapliConnectionNotOpened,
    ScrapliUnsupportedPlatform,
)
from scrapli.transport.plugins.system.ptyprocess import PtyProcess
from scrapli.transport.plugins.system.transport import SystemTransport


def test_unsupported_platform(monkeypatch, base_transport_args, system_transport_plugin_args):
    monkeypatch.setattr("sys.platform", "win")

    with pytest.raises(ScrapliUnsupportedPlatform):
        SystemTransport(
            base_transport_args=base_transport_args,
            plugin_transport_args=system_transport_plugin_args,
        )


def test_build_open_cmd(system_transport):
    system_transport.plugin_transport_args.auth_private_key = "private_key"
    system_transport.plugin_transport_args.auth_strict_key = False
    system_transport.plugin_transport_args.ssh_config_file = "ssh_config"
    system_transport._base_transport_args.transport_options = {
        "open_cmd": ["somearg", "anotherarg"]
    }
    system_transport._build_open_cmd()
    assert system_transport.open_cmd == [
        "ssh",
        "localhost",
        "-p",
        "22",
        "-o",
        "ConnectTimeout=10",
        "-o",
        "ServerAliveInterval=30",
        "-i",
        "private_key",
        "-l",
        "scrapli",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-F",
        "ssh_config",
        "somearg",
        "anotherarg",
    ]


def test_build_open_cmd_alternate_options(system_transport):
    system_transport.plugin_transport_args.auth_private_key = "private_key"
    system_transport.plugin_transport_args.auth_strict_key = True
    system_transport.plugin_transport_args.ssh_known_hosts_file = "ssh_known_hosts"
    system_transport._base_transport_args.transport_options = {"open_cmd": "additional_cmd"}
    system_transport._build_open_cmd()
    assert system_transport.open_cmd == [
        "ssh",
        "localhost",
        "-p",
        "22",
        "-o",
        "ConnectTimeout=10",
        "-o",
        "ServerAliveInterval=30",
        "-i",
        "private_key",
        "-l",
        "scrapli",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        "UserKnownHostsFile=ssh_known_hosts",
        "-F",
        "/dev/null",
        "additional_cmd",
    ]


def test_close(fs, monkeypatch, system_transport):
    def _close(cls):
        pass

    monkeypatch.setattr(
        "scrapli.transport.plugins.system.ptyprocess.PtyProcess.close",
        _close,
    )

    # giving ptyprocess a "real" (but not like... real real) fd seemed like a good idea... dunno
    # if its really necessary, but it *does* need a fd of some sort so whatever
    fs.create_file("dummy")
    dummy_file = open("dummy")
    system_transport.session = PtyProcess(pid=0, fd=dummy_file.fileno())
    system_transport.close()

    assert system_transport.session is None


def test_isalive_no_session(system_transport):
    assert system_transport.isalive() is False


def test_isalive(fs, system_transport):
    # lie and pretend the session is already assigned
    # giving ptyprocess a "real" (but not like... real real) fd seemed like a good idea... dunno
    # if its really necessary, but it *does* need a fd of some sort so whatever; also give it a
    # forked pid so that the isalive method works... obviously this is sorta cheating to force it
    # to work but we really only care that scrapli does the right thing... we have faith that
    # ptyprocess will be doing the right thing "below" scrapli
    dummy_pid, fd = pty.fork()
    fs.create_file("dummy")
    dummy_file = open("dummy")
    system_transport.session = PtyProcess(pid=dummy_pid, fd=dummy_file.fileno())
    assert system_transport.isalive() is True


def test_read(fs, monkeypatch, system_transport):
    def _read(cls, _):
        return b"somebytes"

    monkeypatch.setattr(
        "scrapli.transport.plugins.system.ptyprocess.PtyProcess.read",
        _read,
    )

    # lie and pretend the session is already assigned
    # giving ptyprocess a "real" (but not like... real real) fd seemed like a good idea... dunno
    # if its really necessary, but it *does* need a fd of some sort so whatever
    dummy_pid, fd = pty.fork()
    fs.create_file("dummy")
    dummy_file = open("dummy")
    system_transport.session = PtyProcess(pid=dummy_pid, fd=dummy_file.fileno())

    assert system_transport.read() == b"somebytes"


def test_read_exception_not_open(system_transport):
    with pytest.raises(ScrapliConnectionNotOpened):
        system_transport.read()


def test_read_exception_eof(fs, monkeypatch, system_transport):
    def _read(cls, _):
        raise EOFError

    monkeypatch.setattr(
        "scrapli.transport.plugins.system.ptyprocess.PtyProcess.read",
        _read,
    )

    # lie and pretend the session is already assigned
    # giving ptyprocess a "real" (but not like... real real) fd seemed like a good idea... dunno
    # if its really necessary, but it *does* need a fd of some sort so whatever
    fs.create_file("dummy")
    dummy_file = open("dummy")
    system_transport.session = PtyProcess(pid=0, fd=dummy_file.fileno())

    with pytest.raises(ScrapliConnectionError):
        system_transport.read()


def test_write(system_transport):
    system_transport.session = BytesIO()
    system_transport.write(b"blah")
    system_transport.session.seek(0)
    assert system_transport.session.read() == b"blah"


def test_write_exception(system_transport):
    with pytest.raises(ScrapliConnectionNotOpened):
        system_transport.write("blah")
