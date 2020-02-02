import os

import pytest

from nssh import NSSH
from nssh.transport import MikoTransport, SSH2Transport, SystemSSHTransport


def test__str():
    conn = NSSH(host="myhost")
    assert str(conn) == "NSSH Object for host myhost"


def test__repr():
    conn = NSSH(host="myhost")
    assert (
        repr(conn)
        == "NSSH {'host': 'myhost', 'port': 22, 'auth_username': '', 'auth_password': '********', 'auth_strict_key': True, 'auth_public_key': b'', 'timeout_socket': 5, 'timeout_ssh': 5000, 'timeout_ops': 10, 'comms_prompt_pattern': '^[a-z0-9.\\\\-@()/:]{1,32}[#>$]$', 'comms_return_char': '\\n', 'comms_ansi': False, 'session_pre_login_handler': None, 'session_disable_paging': 'terminal length 0', 'ssh_config_file': True, 'transport_class': <class 'nssh.transport.systemssh.SystemSSHTransport'>, 'transport_args': {'host': 'myhost', 'port': 22, 'timeout_socket': 5, 'timeout_ssh': 5000, 'auth_username': '', 'auth_public_key': b'', 'auth_password': '', 'auth_strict_key': True, 'comms_return_char': '\\n', 'ssh_config_file': True}, 'channel_args': {'comms_prompt_pattern': '^[a-z0-9.\\\\-@()/:]{1,32}[#>$]$', 'comms_return_char': '\\n', 'comms_ansi': False, 'timeout_ops': 10}}"
    )


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
    with pytest.raises(TypeError) as e:
        NSSH(port="notint")
    assert str(e.value) == "port should be int, got <class 'str'>"


def test_user():
    conn = NSSH(auth_username="nssh")
    assert conn.auth_username == "nssh"


def test_user_strip():
    conn = NSSH(auth_username=" nssh ")
    assert conn.auth_username == "nssh"


def test_user_invalid():
    with pytest.raises(AttributeError):
        NSSH(auth_username=1234)


def test_system_driver():
    conn = NSSH()
    assert conn.transport_class == SystemSSHTransport


def test_ssh2_driver():
    conn = NSSH(driver="ssh2")
    assert conn.transport_class == SSH2Transport


def test_paramiko_driver():
    conn = NSSH(driver="paramiko")
    assert conn.transport_class == MikoTransport


def test_invalid_driver():
    with pytest.raises(ValueError) as e:
        NSSH(driver="notreal")
    assert str(e.value) == "transport should be one of ssh2|paramiko|system, got notreal"


def test_auth_ssh_key_strip():
    conn = NSSH(auth_public_key="~/some_neat_path ")
    user_path = os.path.expanduser("~/")
    assert conn.auth_public_key == f"{user_path}some_neat_path".encode()


def test_auth_password_strip():
    conn = NSSH(auth_password=" password ")
    assert conn.auth_password == "password"


def test_auth_strict_key_invalid():
    with pytest.raises(TypeError) as e:
        NSSH(auth_strict_key="notreal")
    assert str(e.value) == "auth_strict_key should be bool, got <class 'str'>"


def test_valid_comms_return_char():
    conn = NSSH(comms_return_char="\rn")
    assert conn.comms_return_char == "\rn"


def test_invalid_comms_return_char():
    with pytest.raises(TypeError) as e:
        NSSH(comms_return_char=False)
    assert str(e.value) == "comms_return_char should be str, got <class 'bool'>"


def test_valid_comms_ansi():
    conn = NSSH(comms_ansi=True)
    assert conn.comms_ansi is True


def test_invalid_comms_ansi():
    with pytest.raises(TypeError) as e:
        NSSH(comms_ansi=123)
    assert str(e.value) == "comms_ansi should be bool, got <class 'int'>"


def test_valid_comms_prompt_pattern():
    conn = NSSH(comms_prompt_pattern="somestr")
    assert conn.comms_prompt_pattern == "somestr"


def test_invalid_comms_prompt_pattern():
    with pytest.raises(TypeError):
        NSSH(comms_prompt_pattern=123)


def test_valid_session_pre_login_handler_func():
    def pre_login_handler_func():
        pass

    login_handler = pre_login_handler_func
    conn = NSSH(session_pre_login_handler=login_handler)
    assert callable(conn.session_pre_login_handler)


def test_valid_session_pre_login_handler_ext_func():
    conn = NSSH(
        session_pre_login_handler="tests.unit.driver.ext_test_funcs.some_pre_login_handler_func"
    )
    assert callable(conn.session_pre_login_handler)


def test_invalid_session_pre_login_handler():
    with pytest.raises(TypeError) as e:
        NSSH(session_pre_login_handler="not.valid.func")
    assert (
        str(e.value)
        == "not.valid.func is an invalid session_pre_login_handler function or path to a function."
    )


def test_valid_session_disable_paging_default():
    conn = NSSH()
    assert conn.session_disable_paging == "terminal length 0"


def test_valid_session_disable_paging_func():
    def disable_paging_func():
        pass

    disable_paging = disable_paging_func
    conn = NSSH(session_disable_paging=disable_paging)
    assert callable(conn.session_disable_paging)


def test_valid_session_disable_paging_ext_func():
    conn = NSSH(session_disable_paging="tests.unit.driver.ext_test_funcs.some_disable_paging_func")
    assert callable(conn.session_disable_paging)


def test_valid_session_disable_paging_str():
    conn = NSSH(session_disable_paging="disable all the paging")
    assert conn.session_disable_paging == "disable all the paging"


def test_invalid_session_disable_paging_func():
    conn = NSSH(session_disable_paging="not.valid.func")
    assert conn.session_disable_paging == "not.valid.func"


def test_invalid_session_disable_paging():
    with pytest.raises(TypeError) as e:
        NSSH(session_disable_paging=123)
    assert str(e.value) == "session_disable_paging should be str or callable, got <class 'int'>"


def test_isalive(mocked_channel):
    # mocked channel always returns true so this is not a great test
    conn = mocked_channel([])
    conn.open()
    assert conn.isalive() is True
