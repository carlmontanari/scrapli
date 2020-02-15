import pytest

from scrapli import Scrape
from scrapli.driver import NetworkDriver
from scrapli.driver.core import IOSXEDriver


@pytest.fixture(scope="module")
def base_driver():
    def _base_driver(
        host,
        port=22,
        auth_username="",
        auth_password="",
        auth_public_key="",
        timeout_socket=5,
        timeout_transport=5000,
        timeout_ops=5,
        comms_prompt_pattern=r"^[a-z0-9.\-@()/:]{1,32}[#>$]$",
        comms_ansi=False,
        session_pre_login_handler="",
        session_disable_paging="terminal length 0",
        transport="system",
    ):
        conn = Scrape(
            host=host,
            port=port,
            auth_username=auth_username,
            auth_password=auth_password,
            auth_public_key=auth_public_key,
            auth_strict_key=False,
            timeout_socket=timeout_socket,
            timeout_transport=timeout_transport,
            timeout_ops=timeout_ops,
            comms_prompt_pattern=comms_prompt_pattern,
            comms_ansi=comms_ansi,
            session_pre_login_handler=session_pre_login_handler,
            session_disable_paging=session_disable_paging,
            transport=transport,
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
        timeout_transport=5000,
        timeout_ops=5,
        comms_prompt_pattern=r"^[a-z0-9.\-@()/:]{1,32}[#>$]$",
        comms_ansi=False,
        session_pre_login_handler="",
        session_disable_paging="terminal length 0",
        transport="system",
    ):
        conn = NetworkDriver(
            host=host,
            port=port,
            auth_username=auth_username,
            auth_password=auth_password,
            auth_public_key=auth_public_key,
            auth_strict_key=False,
            timeout_socket=timeout_socket,
            timeout_transport=timeout_transport,
            timeout_ops=timeout_ops,
            comms_prompt_pattern=comms_prompt_pattern,
            comms_ansi=comms_ansi,
            session_pre_login_handler=session_pre_login_handler,
            session_disable_paging=session_disable_paging,
            transport=transport,
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
        timeout_transport=5000,
        timeout_ops=5,
        comms_prompt_pattern=r"^[a-z0-9.\-@()/:]{1,32}[#>$]$",
        comms_ansi=False,
        session_pre_login_handler="",
        session_disable_paging="terminal length 0",
        transport="system",
    ):
        conn = IOSXEDriver(
            host=host,
            port=port,
            auth_username=auth_username,
            auth_password=auth_password,
            auth_public_key=auth_public_key,
            auth_strict_key=False,
            timeout_socket=timeout_socket,
            timeout_transport=timeout_transport,
            timeout_ops=timeout_ops,
            comms_prompt_pattern=comms_prompt_pattern,
            comms_ansi=comms_ansi,
            session_pre_login_handler=session_pre_login_handler,
            session_disable_paging=session_disable_paging,
            transport=transport,
        )
        conn.open()
        return conn

    return _cisco_iosxe_driver
