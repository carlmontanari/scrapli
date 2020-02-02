import pytest

from nssh import NSSH
from nssh.driver import NetworkDriver
from nssh.driver.core import IOSXEDriver


@pytest.fixture(scope="module")
def base_driver():
    def _base_driver(
        host,
        port=22,
        auth_username="",
        auth_password="",
        auth_public_key="",
        timeout_socket=5,
        timeout_ssh=1000,
        timeout_ops=2,
        comms_prompt_pattern=r"^[a-z0-9.\-@()/:]{1,32}[#>$]$",
        comms_ansi=False,
        session_pre_login_handler="",
        session_disable_paging="terminal length 0",
        driver="system",
    ):
        conn = NSSH(
            host=host,
            port=port,
            auth_username=auth_username,
            auth_password=auth_password,
            auth_public_key=auth_public_key,
            timeout_socket=timeout_socket,
            timeout_ssh=timeout_ssh,
            timeout_ops=timeout_ops,
            comms_prompt_pattern=comms_prompt_pattern,
            comms_ansi=comms_ansi,
            session_pre_login_handler=session_pre_login_handler,
            session_disable_paging=session_disable_paging,
            driver=driver,
        )
        conn.open()
        return conn

    return _base_driver


@pytest.fixture(scope="module")
def network_driver():
    def _network_driver(
        host,
        port=22,
        auth_username="",
        auth_password="",
        auth_public_key="",
        timeout_socket=5,
        timeout_ssh=1000,
        timeout_ops=2,
        comms_prompt_pattern=r"^[a-z0-9.\-@()/:]{1,32}[#>$]$",
        comms_ansi=False,
        session_pre_login_handler="",
        session_disable_paging="terminal length 0",
        driver="system",
    ):
        conn = NetworkDriver(
            host=host,
            port=port,
            auth_username=auth_username,
            auth_password=auth_password,
            auth_public_key=auth_public_key,
            timeout_socket=timeout_socket,
            timeout_ssh=timeout_ssh,
            timeout_ops=timeout_ops,
            comms_prompt_pattern=comms_prompt_pattern,
            comms_ansi=comms_ansi,
            session_pre_login_handler=session_pre_login_handler,
            session_disable_paging=session_disable_paging,
            driver=driver,
        )
        conn.open()
        return conn

    return _network_driver


@pytest.fixture(scope="module")
def cisco_iosxe_driver():
    def _cisco_iosxe_driver(
        host,
        port=22,
        auth_username="",
        auth_password="",
        auth_public_key="",
        timeout_socket=5,
        timeout_ssh=1000,
        timeout_ops=2,
        comms_prompt_pattern=r"^[a-z0-9.\-@()/:]{1,32}[#>$]$",
        comms_ansi=False,
        session_pre_login_handler="",
        session_disable_paging="terminal length 0",
        driver="system",
    ):
        conn = IOSXEDriver(
            host=host,
            port=port,
            auth_username=auth_username,
            auth_password=auth_password,
            auth_public_key=auth_public_key,
            timeout_socket=timeout_socket,
            timeout_ssh=timeout_ssh,
            timeout_ops=timeout_ops,
            comms_prompt_pattern=comms_prompt_pattern,
            comms_ansi=comms_ansi,
            session_pre_login_handler=session_pre_login_handler,
            session_disable_paging=session_disable_paging,
            driver=driver,
        )
        conn.open()
        return conn

    return _cisco_iosxe_driver
