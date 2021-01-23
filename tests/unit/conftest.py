from copy import deepcopy
from pathlib import Path

import pytest

import scrapli
from scrapli.channel.async_channel import AsyncChannel
from scrapli.channel.base_channel import BaseChannel, BaseChannelArgs
from scrapli.channel.sync_channel import Channel
from scrapli.driver.base.async_driver import AsyncDriver
from scrapli.driver.base.base_driver import BaseDriver
from scrapli.driver.base.sync_driver import Driver
from scrapli.driver.core.arista_eos.async_driver import AsyncEOSDriver
from scrapli.driver.core.arista_eos.base_driver import PRIVS as EOS_PRIVS
from scrapli.driver.core.arista_eos.sync_driver import EOSDriver
from scrapli.driver.core.cisco_iosxe.async_driver import PRIVS as IOSXE_PRIVS
from scrapli.driver.core.cisco_iosxe.async_driver import AsyncIOSXEDriver
from scrapli.driver.core.cisco_iosxe.sync_driver import IOSXEDriver
from scrapli.driver.core.cisco_iosxr.async_driver import PRIVS as IOSXR_PRIVS
from scrapli.driver.core.cisco_iosxr.async_driver import AsyncIOSXRDriver
from scrapli.driver.core.cisco_iosxr.sync_driver import IOSXRDriver
from scrapli.driver.core.cisco_nxos.async_driver import PRIVS as NXOS_PRIVS
from scrapli.driver.core.cisco_nxos.async_driver import AsyncNXOSDriver
from scrapli.driver.core.cisco_nxos.sync_driver import NXOSDriver
from scrapli.driver.core.juniper_junos.async_driver import PRIVS as JUNOS_PRIVS
from scrapli.driver.core.juniper_junos.async_driver import AsyncJunosDriver
from scrapli.driver.core.juniper_junos.sync_driver import JunosDriver
from scrapli.driver.generic.async_driver import AsyncGenericDriver
from scrapli.driver.generic.base_driver import BaseGenericDriver
from scrapli.driver.generic.sync_driver import GenericDriver
from scrapli.driver.network.async_driver import AsyncNetworkDriver
from scrapli.driver.network.base_driver import PrivilegeLevel
from scrapli.driver.network.sync_driver import NetworkDriver
from scrapli.transport.base.async_transport import AsyncTransport
from scrapli.transport.base.base_socket import Socket
from scrapli.transport.base.base_transport import BaseTransport, BaseTransportArgs
from scrapli.transport.base.sync_transport import Transport
from scrapli.transport.plugins.asyncssh.transport import AsyncsshTransport
from scrapli.transport.plugins.asyncssh.transport import (
    PluginTransportArgs as AsyncsshPluginTransportArgs,
)
from scrapli.transport.plugins.asynctelnet.transport import AsynctelnetTransport
from scrapli.transport.plugins.asynctelnet.transport import (
    PluginTransportArgs as AsynctelnetPluginTransportArgs,
)
from scrapli.transport.plugins.paramiko.transport import ParamikoTransport
from scrapli.transport.plugins.paramiko.transport import (
    PluginTransportArgs as ParamikoPluginTransportArgs,
)
from scrapli.transport.plugins.ssh2.transport import PluginTransportArgs as Ssh2PluginTransportArgs
from scrapli.transport.plugins.ssh2.transport import Ssh2Transport
from scrapli.transport.plugins.system.transport import (
    PluginTransportArgs as SystemPluginTransportArgs,
)
from scrapli.transport.plugins.system.transport import SystemTransport
from scrapli.transport.plugins.telnet.transport import (
    PluginTransportArgs as TelnetPluginTransportArgs,
)
from scrapli.transport.plugins.telnet.transport import TelnetTransport

# misc fixtures


@pytest.fixture(scope="session")
def unit_test_data_path():
    """Fixture to provide path to unit test data files"""
    return f"{Path(scrapli.__file__).parents[1]}/tests/test_data"


@pytest.fixture(scope="session")
def real_ssh_config_file_path(unit_test_data_path):
    return f"{unit_test_data_path}/files/_ssh_config"


@pytest.fixture(scope="session")
def real_ssh_known_hosts_file_path(unit_test_data_path):
    return f"{unit_test_data_path}/files/_ssh_known_hosts"


@pytest.fixture(scope="session")
def real_ssh_commands_file_path(unit_test_data_path):
    return f"{unit_test_data_path}/files/cisco_iosxe_commands"


# transport fixtures


@pytest.fixture(scope="function")
def base_transport_args():
    """Fixture to provide base transport args"""
    base_transport_args = BaseTransportArgs(
        transport_options={}, host="localhost", port=22, timeout_socket=10.0, timeout_transport=30.0
    )
    return base_transport_args


@pytest.fixture(scope="function")
def base_transport_no_abc(base_transport_args):
    """Fixture to provide BaseTransport instance w/ abstractmethods 'cleared'"""
    BaseTransport.__abstractmethods__ = set()
    return BaseTransport(base_transport_args=base_transport_args)


@pytest.fixture(scope="function")
def sync_transport_no_abc(base_transport_args):
    """Fixture to provide Transport instance w/ abstractmethods 'cleared'"""
    Transport.__abstractmethods__ = set()
    return Transport(base_transport_args=base_transport_args)


@pytest.fixture(scope="function")
def async_transport_no_abc(base_transport_args):
    """Fixture to provide AsyncTransport instance w/ abstractmethods 'cleared'"""
    AsyncTransport.__abstractmethods__ = set()
    return AsyncTransport(base_transport_args=base_transport_args)


@pytest.fixture(scope="function")
def socket_transport():
    """Fixture to provide Socket instance"""
    return Socket(host="localhost", port=22, timeout=10.0)


@pytest.fixture(scope="function")
def system_transport_plugin_args():
    """Fixture to provide system transport plugin args instance"""
    plugin_args = SystemPluginTransportArgs(
        auth_username="scrapli",
        auth_private_key="",
        auth_strict_key=True,
        ssh_config_file="",
        ssh_known_hosts_file="",
    )
    return plugin_args


@pytest.fixture(scope="function")
def system_transport(base_transport_args, system_transport_plugin_args):
    """Fixture to provide system transport instance"""
    system_transport = SystemTransport(
        base_transport_args=base_transport_args, plugin_transport_args=system_transport_plugin_args
    )
    return system_transport


@pytest.fixture(scope="function")
def telnet_transport_plugin_args():
    """Fixture to provide telnet transport plugin args instance"""
    plugin_args = TelnetPluginTransportArgs()
    return plugin_args


@pytest.fixture(scope="function")
def telnet_transport(base_transport_args, telnet_transport_plugin_args):
    """Fixture to provide telnet transport instance"""
    base_transport_args.port = 23
    telnet_transport = TelnetTransport(
        base_transport_args=base_transport_args, plugin_transport_args=telnet_transport_plugin_args
    )
    return telnet_transport


@pytest.fixture(scope="function")
def asyncssh_transport_plugin_args():
    """Fixture to provide asyncssh transport plugin args instance"""
    plugin_args = AsyncsshPluginTransportArgs(auth_username="scrapli", auth_password="scrapli")
    return plugin_args


@pytest.fixture(scope="function")
def asyncssh_transport(base_transport_args, asyncssh_transport_plugin_args):
    """Fixture to provide asyncssh transport instance"""
    asyncssh_transport = AsyncsshTransport(
        base_transport_args=base_transport_args,
        plugin_transport_args=asyncssh_transport_plugin_args,
    )
    return asyncssh_transport


@pytest.fixture(scope="function")
def asynctelnet_transport_plugin_args():
    """Fixture to provide asynctelnet transport plugin args instance"""
    plugin_args = AsynctelnetPluginTransportArgs()
    return plugin_args


@pytest.fixture(scope="function")
def asynctelnet_transport(base_transport_args, asynctelnet_transport_plugin_args):
    """Fixture to provide asynctelnet transport instance"""
    asynctelnet_transport = AsynctelnetTransport(
        base_transport_args=base_transport_args,
        plugin_transport_args=asynctelnet_transport_plugin_args,
    )
    return asynctelnet_transport


@pytest.fixture(scope="function")
def paramiko_transport_plugin_args():
    """Fixture to provide paramiko transport plugin args instance"""
    plugin_args = ParamikoPluginTransportArgs(auth_username="scrapli", auth_password="scrapli")
    return plugin_args


@pytest.fixture(scope="function")
def paramiko_transport(base_transport_args, paramiko_transport_plugin_args):
    """Fixture to provide paramiko transport instance"""
    paramiko_transport = ParamikoTransport(
        base_transport_args=base_transport_args,
        plugin_transport_args=paramiko_transport_plugin_args,
    )
    return paramiko_transport


@pytest.fixture(scope="function")
def ssh2_transport_plugin_args():
    """Fixture to provide ssh2 transport plugin args instance"""
    plugin_args = Ssh2PluginTransportArgs(auth_username="scrapli", auth_password="scrapli")
    return plugin_args


@pytest.fixture(scope="function")
def ssh2_transport(base_transport_args, ssh2_transport_plugin_args):
    """Fixture to provide ssh2 transport instance"""
    ssh2_transport = Ssh2Transport(
        base_transport_args=base_transport_args,
        plugin_transport_args=ssh2_transport_plugin_args,
    )
    return ssh2_transport


# Channel related fixtures


@pytest.fixture(scope="function")
def base_channel_args():
    base_channel_args = BaseChannelArgs()
    return base_channel_args


@pytest.fixture(scope="function")
def base_channel(base_transport_no_abc, base_channel_args):
    """Fixture to provide base channel instance"""
    base_channel = BaseChannel(transport=base_transport_no_abc, base_channel_args=base_channel_args)
    return base_channel


@pytest.fixture(scope="function")
def sync_channel(sync_transport_no_abc, base_channel_args):
    sync_channel = Channel(transport=sync_transport_no_abc, base_channel_args=base_channel_args)
    return sync_channel


@pytest.fixture(scope="function")
def async_channel(async_transport_no_abc, base_channel_args):
    async_channel = AsyncChannel(
        transport=async_transport_no_abc, base_channel_args=base_channel_args
    )
    return async_channel


# base driver fixtures


@pytest.fixture(scope="function")
def base_driver():
    """Fixture to provide base driver instance"""
    base_driver = BaseDriver(host="localhost", auth_username="scrapli")
    return base_driver


@pytest.fixture(scope="function", params=["sync", "async"])
def base_drivers(request, sync_driver, async_driver):
    """Fixture to provide both sync and async driver instances"""
    if request.param == "sync":
        yield sync_driver
    else:
        yield async_driver


@pytest.fixture(scope="function")
def sync_driver():
    """Fixture to provide sync driver instance"""
    sync_driver = Driver(host="localhost", auth_username="scrapli")
    return sync_driver


@pytest.fixture(scope="function")
def sync_driver_telnet():
    """Fixture to provide sync driver instance"""
    sync_driver_telnet = Driver(host="localhost", auth_username="scrapli", transport="telnet")
    return sync_driver_telnet


@pytest.fixture(scope="function")
def async_driver():
    """Fixture to provide async driver instance"""
    async_driver = AsyncDriver(host="localhost", auth_username="scrapli", transport="asynctelnet")
    return async_driver


# generic driver fixtures


@pytest.fixture(scope="function")
def base_generic_driver():
    """Fixture to provide generic driver instance"""
    base_generic_driver = BaseGenericDriver()
    return base_generic_driver


@pytest.fixture(scope="function")
def sync_generic_driver():
    """Fixture to provide generic driver instance"""
    sync_generic_driver = GenericDriver(host="localhost")
    return sync_generic_driver


@pytest.fixture(scope="function")
def async_generic_driver():
    """Fixture to provide generic driver instance"""
    async_generic_driver = AsyncGenericDriver(host="localhost", transport="asynctelnet")
    return async_generic_driver


# network driver fixtures

PRIVS = {
    "exec": (
        PrivilegeLevel(
            pattern=r"^[a-z0-9.\-_@()/:]{1,63}>$",
            name="exec",
            previous_priv="",
            deescalate="",
            escalate="",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
    "privilege_exec": (
        PrivilegeLevel(
            pattern=r"^[a-z0-9.\-_@/:]{1,63}#$",
            name="privilege_exec",
            previous_priv="exec",
            deescalate="disable",
            escalate="enable",
            escalate_auth=True,
            escalate_prompt=r"^(?:enable\s){0,1}password:\s?$",
        )
    ),
    "configuration": (
        PrivilegeLevel(
            pattern=r"^[a-z0-9.\-_@/:]{1,63}\((?!tcl)[a-z0-9.\-@/:\+]{0,32}\)#$",
            name="configuration",
            previous_priv="privilege_exec",
            deescalate="end",
            escalate="configure terminal",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
    "tclsh": (
        PrivilegeLevel(
            pattern=r"(^[a-z0-9.\-_@/:]{1,63}\(tcl\)#$)|(^\+>$)",
            name="tclsh",
            previous_priv="privilege_exec",
            deescalate="tclquit",
            escalate="tclsh",
            escalate_auth=False,
            escalate_prompt="",
        )
    ),
}


@pytest.fixture(scope="function")
def base_network_driver():
    """Fixture to provide base network driver instance"""
    # even though we are testing the "base" driver, need the driver so that we get the logger
    # in the instance (mixins are weird!)
    base_network_driver = NetworkDriver(
        host="localhost",
        privilege_levels=deepcopy(PRIVS),
        auth_secondary="scrapli",
        default_desired_privilege_level="privilege_exec",
    )
    base_network_driver.auth_secondary = "scrapli"
    base_network_driver.failed_when_contains = []
    base_network_driver.textfsm_platform = "cisco_iosxe"
    base_network_driver.genie_platform = "cisco_iosxe"
    base_network_driver.privilege_levels = deepcopy(PRIVS)
    base_network_driver.comms_prompt_pattern = r"^\S{0,48}[#>$~@:\]]\s*$"
    base_network_driver._priv_graph = None
    return base_network_driver


@pytest.fixture(scope="function")
def sync_network_driver():
    """Fixture to provide sync network driver instance"""
    sync_network_driver = NetworkDriver(
        host="localhost",
        privilege_levels=deepcopy(PRIVS),
        auth_secondary="scrapli",
        default_desired_privilege_level="privilege_exec",
    )
    sync_network_driver.textfsm_platform = "cisco_iosxe"
    sync_network_driver.genie_platform = "cisco_iosxe"
    return sync_network_driver


@pytest.fixture(scope="function")
def async_network_driver():
    """Fixture to provide async network driver instance"""
    async_network_driver = AsyncNetworkDriver(
        host="localhost",
        privilege_levels=deepcopy(PRIVS),
        auth_secondary="scrapli",
        default_desired_privilege_level="privilege_exec",
        transport="asynctelnet",
    )
    async_network_driver.textfsm_platform = "cisco_iosxe"
    async_network_driver.genie_platform = "cisco_iosxe"
    return async_network_driver


# core driver fixtures


@pytest.fixture(scope="function")
def sync_eos_driver():
    """Fixture to provide sync eos driver instance"""
    sync_eos_driver = EOSDriver(
        host="localhost",
        privilege_levels=deepcopy(EOS_PRIVS),
        auth_secondary="scrapli",
        default_desired_privilege_level="privilege_exec",
    )
    sync_eos_driver.textfsm_platform = "arista_eos"
    sync_eos_driver.genie_platform = ""
    return sync_eos_driver


@pytest.fixture(scope="function")
def async_eos_driver():
    """Fixture to provide async eos driver instance"""
    async_eos_driver = AsyncEOSDriver(
        host="localhost",
        privilege_levels=deepcopy(EOS_PRIVS),
        auth_secondary="scrapli",
        default_desired_privilege_level="privilege_exec",
        transport="asynctelnet",
    )
    async_eos_driver.textfsm_platform = "arista_eos"
    async_eos_driver.genie_platform = ""
    return async_eos_driver


@pytest.fixture(scope="function")
def sync_iosxe_driver():
    """Fixture to provide sync iosxe driver instance"""
    sync_iosxe_driver = IOSXEDriver(
        host="localhost",
        privilege_levels=deepcopy(IOSXE_PRIVS),
        auth_secondary="scrapli",
        default_desired_privilege_level="privilege_exec",
    )
    sync_iosxe_driver.textfsm_platform = "cisco_iosxe"
    sync_iosxe_driver.genie_platform = "cisco_iosxe"
    return sync_iosxe_driver


@pytest.fixture(scope="function")
def async_iosxe_driver():
    """Fixture to provide async iosxe driver instance"""
    async_iosxe_driver = AsyncIOSXEDriver(
        host="localhost",
        privilege_levels=deepcopy(IOSXE_PRIVS),
        auth_secondary="scrapli",
        default_desired_privilege_level="privilege_exec",
        transport="asynctelnet",
    )
    async_iosxe_driver.textfsm_platform = "cisco_iosxe"
    async_iosxe_driver.genie_platform = "cisco_iosxe"
    return async_iosxe_driver


@pytest.fixture(scope="function")
def sync_iosxr_driver():
    """Fixture to provide sync iosxr driver instance"""
    sync_iosxe_driver = IOSXRDriver(
        host="localhost",
        privilege_levels=deepcopy(IOSXR_PRIVS),
        auth_secondary="scrapli",
        default_desired_privilege_level="privilege_exec",
    )
    sync_iosxe_driver.textfsm_platform = "cisco_iosxr"
    sync_iosxe_driver.genie_platform = "cisco_iosxr"
    return sync_iosxe_driver


@pytest.fixture(scope="function")
def async_iosxr_driver():
    """Fixture to provide async iosxr driver instance"""
    async_iosxr_driver = AsyncIOSXRDriver(
        host="localhost",
        privilege_levels=deepcopy(IOSXR_PRIVS),
        auth_secondary="scrapli",
        default_desired_privilege_level="privilege_exec",
        transport="asynctelnet",
    )
    async_iosxr_driver.textfsm_platform = "cisco_iosxr"
    async_iosxr_driver.genie_platform = "cisco_iosxr"
    return async_iosxr_driver


@pytest.fixture(scope="function")
def sync_nxos_driver():
    """Fixture to provide sync nxos driver instance"""
    sync_nxos_driver = NXOSDriver(
        host="localhost",
        privilege_levels=deepcopy(NXOS_PRIVS),
        auth_secondary="scrapli",
        default_desired_privilege_level="privilege_exec",
    )
    sync_nxos_driver.textfsm_platform = "cisco_nxos"
    sync_nxos_driver.genie_platform = "cisco_nxos"
    return sync_nxos_driver


@pytest.fixture(scope="function")
def async_nxos_driver():
    """Fixture to provide async nxos driver instance"""
    async_nxos_driver = AsyncNXOSDriver(
        host="localhost",
        privilege_levels=deepcopy(NXOS_PRIVS),
        auth_secondary="scrapli",
        default_desired_privilege_level="privilege_exec",
        transport="asynctelnet",
    )
    async_nxos_driver.textfsm_platform = "cisco_nxos"
    async_nxos_driver.genie_platform = "cisco_nxos"
    return async_nxos_driver


@pytest.fixture(scope="function")
def sync_junos_driver():
    """Fixture to provide sync junos driver instance"""
    sync_junos_driver = JunosDriver(
        host="localhost",
        privilege_levels=deepcopy(JUNOS_PRIVS),
        auth_secondary="scrapli",
        default_desired_privilege_level="exec",
    )
    sync_junos_driver.textfsm_platform = "exec"
    sync_junos_driver.genie_platform = ""
    return sync_junos_driver


@pytest.fixture(scope="function")
def async_junos_driver():
    """Fixture to provide async junos driver instance"""
    async_junos_driver = AsyncJunosDriver(
        host="localhost",
        privilege_levels=deepcopy(JUNOS_PRIVS),
        auth_secondary="scrapli",
        default_desired_privilege_level="exec",
        transport="asynctelnet",
    )
    async_junos_driver.textfsm_platform = "juniper_junos"
    async_junos_driver.genie_platform = ""
    return async_junos_driver
