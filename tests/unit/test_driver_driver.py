import pytest

from nssh import NSSH


def test_host():
    conn = NSSH(host="myhost")
    assert conn.host == "myhost"


def test_host_strip():
    conn = NSSH(host=" whitespace ")
    assert conn.host == "whitespace"


def test_port():
    conn = NSSH(port=123)
    assert conn.port == 123


def test_port_invalid():
    with pytest.raises(TypeError):
        NSSH(port="notint")


def test_user():
    conn = NSSH(auth_username="nssh")
    assert conn.auth_username == "nssh"


def test_user_strip():
    conn = NSSH(auth_username=" nssh ")
    assert conn.auth_username == "nssh"


def test_user_invalid():
    with pytest.raises(AttributeError):
        NSSH(auth_username=1234)