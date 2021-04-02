"""scrapli.driver.base.base_driver"""
import importlib
from dataclasses import fields
from io import BytesIO
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict, Optional, Tuple, Type, Union

from scrapli.channel.base_channel import BaseChannelArgs
from scrapli.exceptions import ScrapliTransportPluginError, ScrapliTypeError, ScrapliValueError
from scrapli.helper import format_user_warning, resolve_file
from scrapli.logging import get_instance_logger
from scrapli.ssh_config import SSHConfig
from scrapli.transport import CORE_TRANSPORTS
from scrapli.transport.base import BasePluginTransportArgs, BaseTransportArgs


class BaseDriver:
    def __init__(
        self,
        host: str,
        port: int = 22,
        auth_username: str = "",
        auth_password: str = "",
        auth_private_key: str = "",
        auth_private_key_passphrase: str = "",
        auth_strict_key: bool = True,
        auth_bypass: bool = False,
        timeout_socket: float = 15.0,
        timeout_transport: float = 30.0,
        timeout_ops: float = 30.0,
        comms_prompt_pattern: str = r"^[a-z0-9.\-@()/:]{1,48}[#>$]\s*$",
        comms_return_char: str = "\n",
        comms_ansi: bool = False,
        ssh_config_file: Union[str, bool] = False,
        ssh_known_hosts_file: Union[str, bool] = False,
        on_init: Optional[Callable[..., Any]] = None,
        on_open: Optional[Callable[..., Any]] = None,
        on_close: Optional[Callable[..., Any]] = None,
        transport: str = "system",
        transport_options: Optional[Dict[str, Any]] = None,
        channel_log: Union[str, bool, BytesIO] = False,
        channel_log_mode: str = "write",
        channel_lock: bool = False,
        logging_uid: str = "",
    ) -> None:
        r"""
        BaseDriver Object

        BaseDriver is the root for all Scrapli driver classes. The synchronous and asyncio driver
        base driver classes can be used to provide a semi-pexpect like experience over top of
        whatever transport a user prefers. Generally, however, the base driver classes should not be
        used directly. It is best to use the GenericDriver (or AsyncGenericDriver) or NetworkDriver
        (or AsyncNetworkDriver) sub-classes of the base drivers.

        Args:
            host: host ip/name to connect to
            port: port to connect to
            auth_username: username for authentication
            auth_private_key: path to private key for authentication
            auth_private_key_passphrase: passphrase for decrypting ssh key if necessary
            auth_password: password for authentication
            auth_strict_key: strict host checking or not
            auth_bypass: bypass "in channel" authentication -- only supported with telnet,
                asynctelnet, and system transport plugins
            timeout_socket: timeout for establishing socket/initial connection in seconds
            timeout_transport: timeout for ssh|telnet transport in seconds
            timeout_ops: timeout for ssh channel operations
            comms_prompt_pattern: raw string regex pattern -- preferably use `^` and `$` anchors!
                this is the single most important attribute here! if this does not match a prompt,
                scrapli will not work!
                IMPORTANT: regex search uses multi-line + case insensitive flags. multi-line allows
                for highly reliably matching for prompts however we do NOT strip trailing whitespace
                for each line, so be sure to add '\\s?' or similar if your device needs that. This
                should be mostly sorted for you if using network drivers (i.e. `IOSXEDriver`).
                Lastly, the case insensitive is just a convenience factor so i can be lazy.
            comms_return_char: character to use to send returns to host
            comms_ansi: True/False strip comms_ansi characters from output, generally the default
                value of False should be fine
            ssh_config_file: string to path for ssh config file, True to use default ssh config file
                or False to ignore default ssh config file
            ssh_known_hosts_file: string to path for ssh known hosts file, True to use default known
                file locations. Only applicable/needed if `auth_strict_key` is set to True
            on_init: callable that accepts the class instance as its only argument. this callable,
                if provided, is executed as the last step of object instantiation -- its purpose is
                primarily to provide a mechanism for scrapli community platforms to have an easy way
                to modify initialization arguments/object attributes without needing to create a
                class that extends the driver, instead allowing the community platforms to simply
                build from the GenericDriver or NetworkDriver classes, and pass this callable to do
                things such as appending to a username (looking at you RouterOS!!). Note that this
                is *always* a synchronous function (even for asyncio drivers)!
            on_open: callable that accepts the class instance as its only argument. this callable,
                if provided, is executed immediately after authentication is completed. Common use
                cases for this callable would be to disable paging or accept any kind of banner
                message that prompts a user upon connection
            on_close: callable that accepts the class instance as its only argument. this callable,
                if provided, is executed immediately prior to closing the underlying transport.
                Common use cases for this callable would be to save configurations prior to exiting,
                or to logout properly to free up vtys or similar
            transport: name of the transport plugin to use for the actual telnet/ssh/netconf
                connection. Available "core" transports are:
                    - system
                    - telnet
                    - asynctelnet
                    - ssh2
                    - paramiko
                    - asyncssh
                Please see relevant transport plugin section for details. Additionally third party
                transport plugins may be available.
            transport_options: dictionary of options to pass to selected transport class; see
                docs for given transport class for details of what to pass here
            channel_lock: True/False to lock the channel (threading.Lock/asyncio.Lock) during
                any channel operations, defaults to False
            channel_log: True/False or a string path to a file of where to write out channel logs --
                these are not "logs" in the normal logging module sense, but only the output that is
                read from the channel. In other words, the output of the channel log should look
                similar to what you would see as a human connecting to a device
            channel_log_mode: "write"|"append", all other values will raise ValueError,
                does what it sounds like it should by setting the channel log to the provided mode
            logging_uid: unique identifier (string) to associate to log messages; useful if you have
                multiple connections to the same device (i.e. one console, one ssh, or one to each
                supervisor module, etc.)

        Returns:
            None

        Raises:
            N/A

        """
        self.logger = get_instance_logger(
            instance_name="scrapli.driver", host=host, port=port, uid=logging_uid
        )

        self._base_channel_args = BaseChannelArgs(
            comms_prompt_pattern=comms_prompt_pattern,
            comms_return_char=comms_return_char,
            comms_ansi=comms_ansi,
            timeout_ops=timeout_ops,
            channel_log=channel_log,
            channel_log_mode=channel_log_mode,
            channel_lock=channel_lock,
        )

        # transport options is unused in most transport plugins, but when used will be a dict of
        # user provided arguments, defaults to None to not be mutable argument, so if its still
        # None at this point turn it into an empty dict to pass into the transports
        transport_options = transport_options or {}
        self._base_transport_args = BaseTransportArgs(
            transport_options=transport_options,
            host=host,
            port=port,
            timeout_socket=timeout_socket,
            timeout_transport=timeout_transport,
            logging_uid=logging_uid,
        )

        self.host, self.port = self._setup_host(host=host, port=port)

        self.auth_username = auth_username
        self.auth_password = auth_password
        self.auth_private_key_passphrase = auth_private_key_passphrase
        self.auth_private_key, self.auth_strict_key, self.auth_bypass = self._setup_auth(
            auth_private_key=auth_private_key,
            auth_strict_key=auth_strict_key,
            auth_bypass=auth_bypass,
        )

        self.ssh_config_file, self.ssh_known_hosts_file = self._setup_ssh_file_args(
            transport=transport,
            ssh_config_file=ssh_config_file,
            ssh_known_hosts_file=ssh_known_hosts_file,
        )

        self._setup_callables(on_init=on_init, on_open=on_open, on_close=on_close)

        self.transport_name = transport
        if self.transport_name in ("asyncssh", "ssh2", "paramiko"):
            # for mostly(?) historical reasons these transports use the `ssh_config` module to get
            # port/username/key file. asyncssh may not need this at all anymore as asyncssh core
            # has added ssh config file support since scrapli's inception
            self._update_ssh_args_from_ssh_config()

        transport_class, self._plugin_transport_args = self._transport_factory()

        self.transport = transport_class(
            base_transport_args=self._base_transport_args,
            plugin_transport_args=self._plugin_transport_args,
        )

        if self.on_init:
            self.on_init(self)

    def __str__(self) -> str:
        """
        Magic str method for Scrape

        Args:
            N/A

        Returns:
            str: str representation of object

        Raises:
            N/A

        """
        return f"Scrapli Driver {self.host}:{self.port}"

    def __repr__(self) -> str:
        """
        Magic repr method for Scrape

        Args:
            N/A

        Returns:
            str: repr for class object

        Raises:
            N/A

        """
        password = "REDACTED" if self.auth_password else ""
        passphrase = "REDACTED" if self.auth_private_key_passphrase else ""

        return (
            f"{self.__class__.__name__}("
            f"host={self.host!r}, "
            f"port={self.port!r}, "
            f"auth_username={self.auth_username!r}, "
            f"auth_password={password!r}, "
            f"auth_private_key={self.auth_private_key!r}, "
            f"auth_private_key_passphrase={passphrase!r}, "
            f"auth_strict_key={self.auth_strict_key!r}, "
            f"auth_bypass={self.auth_bypass!r}, "
            f"timeout_socket={self._base_transport_args.timeout_socket!r}, "
            f"timeout_transport={self._base_transport_args.timeout_transport!r}, "
            f"timeout_ops={self._base_channel_args.timeout_ops!r}, "
            f"comms_prompt_pattern={self._base_channel_args.comms_prompt_pattern!r}, "
            f"comms_return_char={self._base_channel_args.comms_return_char!r}, "
            f"comms_ansi={self._base_channel_args.comms_ansi!r}, "
            f"ssh_config_file={self.ssh_config_file!r}, "
            f"ssh_known_hosts_file={self.ssh_known_hosts_file!r}, "
            f"on_init={self.on_init!r}, "
            f"on_open={self.on_open!r}, "
            f"on_close={self.on_close!r}, "
            f"transport={self.transport_name!r}, "
            f"transport_options={self._base_transport_args.transport_options!r})"
            f"channel_log={self._base_channel_args.channel_log!r}, "
            f"channel_lock={self._base_channel_args.channel_lock!r})"
        )

    @staticmethod
    def _setup_host(host: str, port: int) -> Tuple[str, int]:
        """
        Parse and setup host attributes

        Args:
            host: host to parse/set
            port: port to parse/set

        Returns:
            tuple: host, port -- host is stripped to ensure no weird whitespace floating around

        Raises:
            ScrapliValueError: if host is not provided
            ScrapliTypeError: if port is not an integer

        """
        if not host:
            raise ScrapliValueError("`host` should be a hostname/ip address, got nothing!")
        if not isinstance(port, int):
            raise ScrapliTypeError(f"`port` should be int, got {type(port)}")

        return host.strip(), port

    @staticmethod
    def _setup_auth(
        auth_private_key: str,
        auth_strict_key: bool,
        auth_bypass: bool,
    ) -> Tuple[str, bool, bool]:
        """
        Parse and setup auth attributes

        Args:
            auth_private_key: ssh key to parse/set
            auth_strict_key: strict key to parse/set
            auth_bypass: bypass to parse/set

        Returns:
            Tuple[str, bool, bool]: string of private key path, bool for auth_strict_key, and bool
                for auth_bypass values

        Raises:
            ScrapliTypeError: if auth_strict_key is not a bool
            ScrapliTypeError: if auth_bypass is not a bool

        """
        if not isinstance(auth_strict_key, bool):
            raise ScrapliTypeError(f"`auth_strict_key` should be bool, got {type(auth_strict_key)}")
        if not isinstance(auth_bypass, bool):
            raise ScrapliTypeError(f"`auth_bypass` should be bool, got {type(auth_bypass)}")

        if auth_private_key:
            auth_private_key_path = resolve_file(file=auth_private_key)
        else:
            auth_private_key_path = ""

        return auth_private_key_path, auth_strict_key, auth_bypass

    def _setup_ssh_file_args(
        self,
        transport: str,
        ssh_config_file: Union[str, bool],
        ssh_known_hosts_file: Union[str, bool],
    ) -> Tuple[str, str]:
        """
        Parse and setup ssh related arguments

        Args:
            transport: string name of selected transport (so we can ignore this if transport
                contains "telnet" in the name)
            ssh_config_file: string to path for ssh config file, True to use default ssh config file
                or False to ignore default ssh config file
            ssh_known_hosts_file: string to path for ssh known hosts file, True to use default known
                file locations. Only applicable/needed if `auth_strict_key` is set to True

        Returns:
            Tuple[str, str]: string path to config file, string path to known hosts file

        Raises:
            ScrapliTypeError: if invalid config file or known hosts file value provided

        """
        if "telnet" in transport:
            self.logger.debug("telnet-based transport selected, ignoring ssh file arguments")
            # the word "telnet" should occur in all telnet drivers, always. so this should be safe!
            return "", ""

        if not isinstance(ssh_config_file, (str, bool)):
            raise ScrapliTypeError(
                f"`ssh_config_file` must be str or bool, got {type(ssh_config_file)}"
            )
        if not isinstance(ssh_known_hosts_file, (str, bool)):
            raise ScrapliTypeError(
                "`ssh_known_hosts_file` must be str or bool, got " f"{type(ssh_known_hosts_file)}"
            )

        if ssh_config_file is not False:
            if isinstance(ssh_config_file, bool):
                cfg = ""
            else:
                cfg = ssh_config_file
            resolved_ssh_config_file = self._resolve_ssh_config(cfg)
        else:
            resolved_ssh_config_file = ""

        if ssh_known_hosts_file is not False:
            if isinstance(ssh_known_hosts_file, bool):
                known_hosts = ""
            else:
                known_hosts = ssh_known_hosts_file
            resolved_ssh_known_hosts_file = self._resolve_ssh_known_hosts(known_hosts)
        else:
            resolved_ssh_known_hosts_file = ""

        return resolved_ssh_config_file, resolved_ssh_known_hosts_file

    def _update_ssh_args_from_ssh_config(self) -> None:
        """
        Update ssh args based on ssh config file data

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        ssh = SSHConfig(self.ssh_config_file)
        host_config = ssh.lookup(self.host)

        if host_config.port:
            self.logger.info(
                f"found port for host in ssh configuration file, using this value "
                f"'{host_config.port}' for port!"
            )
            # perhaps this should not override already set port because we dont know if the user
            # provided the port or we just are accepting the default port value... in any case for
            # port, if it is in the ssh config file we will override whatever we currently have
            self.port = host_config.port
        if host_config.user and not self.auth_username:
            self.logger.info(
                f"found username for host in ssh configuration file, using this value "
                f"'{host_config.user}' for auth_username!"
            )
            # only override auth_username if it is not truthy
            self.auth_username = host_config.user
        if host_config.identity_file and not self.auth_private_key:
            self.logger.info(
                f"found identity file for host in ssh configuration file, using this value "
                f"'{host_config.identity_file}' for auth_private_key!"
            )
            # only override auth_private_key if it is not truthy
            self.auth_private_key = host_config.identity_file

    def _setup_callables(
        self,
        on_init: Optional[Callable[..., Any]],
        on_open: Optional[Callable[..., Any]],
        on_close: Optional[Callable[..., Any]],
    ) -> None:
        """
        Parse and setup callables (on_init/on_open/on_close)

        Args:
            on_init: on_init to parse/set
            on_open: on_open to parse/set
            on_close: on_close to parse/set

        Returns:
            None

        Raises:
            ScrapliTypeError: if any of the on_* methods are not callables (or None)

        """
        if on_init is not None and not callable(on_init):
            raise ScrapliTypeError(f"`on_init` must be a callable, got {type(on_init)}")
        if on_open is not None and not callable(on_open):
            raise ScrapliTypeError(f"`on_open` must be a callable, got {type(on_open)}")
        if on_close is not None and not callable(on_close):
            raise ScrapliTypeError(f"`on_close` must be a callable, got {type(on_close)}")

        self.on_init = on_init
        self.on_open = on_open
        self.on_close = on_close

    def _transport_factory(self) -> Tuple[Callable[..., Any], object]:
        """
        Determine proper transport class and necessary arguments to initialize that class

        Args:
            N/A

        Returns:
            Tuple[Callable[..., Any], object]: tuple of transport class and dataclass of transport
                class specific arguments

        Raises:
            N/A

        """
        if self.transport_name in CORE_TRANSPORTS:
            transport_class, _plugin_transport_args_class = self._load_core_transport_plugin()
        else:
            transport_class, _plugin_transport_args_class = self._load_non_core_transport_plugin()

        _plugin_transport_args = {
            field.name: getattr(self, field.name) for field in fields(_plugin_transport_args_class)
        }

        # ignore type as we are typing it as the base class to make life simple, because of this
        # mypy thinks we are passing too many args
        plugin_transport_args = _plugin_transport_args_class(  # type: ignore
            **_plugin_transport_args
        )

        return transport_class, plugin_transport_args

    def _load_transport_plugin_common(
        self, transport_plugin_module: ModuleType
    ) -> Tuple[Any, Type[BasePluginTransportArgs]]:
        """
        Given transport plugin module, load transport class and transport args

        Args:
            transport_plugin_module: loaded importlib module for the given transport

        Returns:
            Tuple[Any, Type[BasePluginTransportArgs]]: transport class class and TransportArgs
                dataclass

        Raises:
            N/A

        """
        transport_class = getattr(
            transport_plugin_module, f"{self.transport_name.capitalize()}Transport"
        )
        plugin_transport_args = getattr(transport_plugin_module, "PluginTransportArgs")

        return transport_class, plugin_transport_args

    def _load_core_transport_plugin(
        self,
    ) -> Tuple[Any, Type[BasePluginTransportArgs]]:
        """
        Find non-core transport plugins and required plugin arguments

        Args:
            N/A

        Returns:
            Tuple[Any, Type[BasePluginTransportArgs]]: transport class class and TransportArgs \
                dataclass

        Raises:
            ScrapliTransportPluginError: if the transport plugin is unable to be loaded

        """
        self.logger.debug("load core transport requested")

        try:
            transport_plugin_module = importlib.import_module(
                f"scrapli.transport.plugins.{self.transport_name}.transport"
            )
        except ModuleNotFoundError as exc:
            title = "Transport Plugin Extra Not Installed!"
            message = (
                f"Optional transport plugin '{self.transport_name}' is not installed!\n"
                f"To resolve this issue, install the transport plugin. You can do this in one of "
                "the following ways:\n"
                f"1: 'pip install -r requirements-{self.transport_name}.txt'\n"
                f"2: 'pip install scrapli[{self.transport_name}]'"
            )
            exception_message = format_user_warning(title=title, message=message)
            raise ScrapliTransportPluginError(exception_message) from exc

        transport_class, plugin_transport_args = self._load_transport_plugin_common(
            transport_plugin_module=transport_plugin_module
        )

        self.logger.debug(f"core transport '{self.transport_name}' loaded successfully")

        return transport_class, plugin_transport_args

    def _load_non_core_transport_plugin(self) -> Tuple[Any, Type[BasePluginTransportArgs]]:
        """
        Find non-core transport plugins and required plugin arguments

        Args:
            N/A

        Returns:
            Tuple[Any, Type[BasePluginTransportArgs]]: transport class class and TransportArgs
                dataclass

        Raises:
            ScrapliTransportPluginError: if non-core transport library is not importable

        """
        try:
            transport_plugin_module = importlib.import_module(
                f"scrapli_{self.transport_name}.transport"
            )
        except ModuleNotFoundError as exc:
            title = "Transport Plugin Extra Not Installed!"
            message = (
                f"Optional third party transport plugin '{self.transport_name}' is not installed!\n"
                f"To resolve this issue, install the transport plugin. You can do this in one of "
                "the following ways:\n"
                f"1: 'pip install -r requirements-{self.transport_name}.txt'\n"
                f"2: 'pip install scrapli[{self.transport_name}]'"
            )
            exception_message = format_user_warning(title=title, message=message)
            raise ScrapliTransportPluginError(exception_message) from exc

        transport_class, plugin_transport_args = self._load_transport_plugin_common(
            transport_plugin_module=transport_plugin_module
        )

        self.logger.debug(f"non-core transport '{self.transport_name}' loaded successfully")

        return transport_class, plugin_transport_args

    def _resolve_ssh_config(self, ssh_config_file: str) -> str:
        """
        Resolve ssh configuration file from provided string

        If provided string is empty (`""`) try to resolve system ssh config files located at
        `~/.ssh/config` or `/etc/ssh/ssh_config`.

        Args:
            ssh_config_file: string representation of ssh config file to try to use

        Returns:
            str: string path to ssh config file or an empty string

        Raises:
            N/A

        """
        self.logger.debug("attempting to resolve 'ssh_config_file' file")

        resolved_ssh_config_file = ""

        if Path(ssh_config_file).is_file():
            resolved_ssh_config_file = str(Path(ssh_config_file))
        elif Path("~/.ssh/config").expanduser().is_file():
            resolved_ssh_config_file = str(Path("~/.ssh/config").expanduser())
        elif Path("/etc/ssh/ssh_config").is_file():
            resolved_ssh_config_file = str(Path("/etc/ssh/ssh_config"))

        if resolved_ssh_config_file:
            self.logger.debug(
                f"using '{resolved_ssh_config_file}' as resolved 'ssh_config_file' file'"
            )
        else:
            self.logger.debug("unable to resolve 'ssh_config_file' file")

        return resolved_ssh_config_file

    def _resolve_ssh_known_hosts(self, ssh_known_hosts: str) -> str:
        """
        Resolve ssh known hosts file from provided string

        If provided string is empty (`""`) try to resolve system known hosts files located at
        `~/.ssh/known_hosts` or `/etc/ssh/ssh_known_hosts`.

        Args:
            ssh_known_hosts: string representation of ssh config file to try to use

        Returns:
            str: string path to ssh known hosts file or an empty string

        Raises:
            N/A

        """
        self.logger.debug("attempting to resolve 'ssh_known_hosts file'")

        resolved_ssh_known_hosts = ""

        if Path(ssh_known_hosts).is_file():
            resolved_ssh_known_hosts = str(Path(ssh_known_hosts))
        elif Path("~/.ssh/known_hosts").expanduser().is_file():
            resolved_ssh_known_hosts = str(Path("~/.ssh/known_hosts").expanduser())
        elif Path("/etc/ssh/ssh_known_hosts").is_file():
            resolved_ssh_known_hosts = str(Path("/etc/ssh/ssh_known_hosts"))

        if resolved_ssh_known_hosts:
            self.logger.debug(
                f"using '{resolved_ssh_known_hosts}' as resolved 'ssh_known_hosts' file'"
            )
        else:
            self.logger.debug("unable to resolve 'ssh_known_hosts' file")

        return resolved_ssh_known_hosts

    @property
    def comms_prompt_pattern(self) -> str:
        """
        Getter for `comms_prompt_pattern` attribute

        Args:
            N/A

        Returns:
            str: comms_prompt_pattern string

        Raises:
            N/A

        """
        return self._base_channel_args.comms_prompt_pattern

    @comms_prompt_pattern.setter
    def comms_prompt_pattern(self, value: str) -> None:
        """
        Setter for `comms_prompt_pattern` attribute

        Args:
            value: str value for comms_prompt_pattern

        Returns:
            None

        Raises:
            ScrapliTypeError: if value is not of type str

        """
        self.logger.debug(f"setting 'comms_prompt_pattern' value to '{value}'")

        if not isinstance(value, str):
            raise ScrapliTypeError

        self._base_channel_args.comms_prompt_pattern = value

    @property
    def comms_return_char(self) -> str:
        """
        Getter for `comms_return_char` attribute

        Args:
            N/A

        Returns:
            str: comms_return_char string

        Raises:
            N/A

        """
        return self._base_channel_args.comms_return_char

    @comms_return_char.setter
    def comms_return_char(self, value: str) -> None:
        """
        Setter for `comms_return_char` attribute

        Args:
            value: str value for comms_return_char

        Returns:
            None

        Raises:
            ScrapliTypeError: if value is not of type str

        """
        self.logger.debug(f"setting 'comms_return_char' value to {repr(value)}")

        if not isinstance(value, str):
            raise ScrapliTypeError

        self._base_channel_args.comms_return_char = value

    @property
    def comms_ansi(self) -> bool:
        """
        Getter for `comms_ansi` attribute

        Args:
            N/A

        Returns:
            bool: comms_ansi bool

        Raises:
            N/A

        """
        return self._base_channel_args.comms_ansi

    @comms_ansi.setter
    def comms_ansi(self, value: bool) -> None:
        """
        Setter for `comms_ansi` attribute

        Args:
            value: bool value for comms_ansi

        Returns:
            None

        Raises:
            ScrapliTypeError: if value is not of type bool

        """
        self.logger.debug(f"setting 'comms_ansi' value to '{value}'")

        if not isinstance(value, bool):
            raise ScrapliTypeError

        self._base_channel_args.comms_ansi = value

    @property
    def timeout_socket(self) -> float:
        """
        Getter for `timeout_socket` attribute

        Args:
            N/A

        Returns:
            float: timeout_socket value

        Raises:
            N/A

        """
        return self._base_transport_args.timeout_socket

    @timeout_socket.setter
    def timeout_socket(self, value: float) -> None:
        """
        Setter for `timeout_socket` attribute

        Args:
            value: float value for timeout_socket

        Returns:
            None

        Raises:
            ScrapliTypeError: if value is not of type int/float

        """
        self.logger.debug(f"setting 'timeout_socket' value to '{value}'")

        if not isinstance(value, (int, float)):
            raise ScrapliTypeError

        self._base_transport_args.timeout_socket = value

    @property
    def timeout_transport(self) -> float:
        """
        Getter for `timeout_transport` attribute

        Args:
            N/A

        Returns:
            float: timeout_transport value

        Raises:
            N/A

        """
        return self._base_transport_args.timeout_transport

    @timeout_transport.setter
    def timeout_transport(self, value: float) -> None:
        """
        Setter for `timeout_transport` attribute

        Args:
            value: float value for timeout_transport

        Returns:
            None

        Raises:
            ScrapliTypeError: if value is not of type int/float

        """
        self.logger.debug(f"setting 'timeout_transport' value to '{value}'")

        if not isinstance(value, (int, float)):
            raise ScrapliTypeError

        if value == 0:
            self.logger.debug("'timeout_transport' value is 0, this will disable timeout decorator")

        self._base_transport_args.timeout_transport = value

        if hasattr(self.transport, "_set_timeout"):
            # transports such as paramiko/ssh2 we have to set the transport in the session
            # object, just updating the _base_transport_args value wont update the session!
            self.transport._set_timeout(value)  # pylint: disable=W0212

    @property
    def timeout_ops(self) -> float:
        """
        Getter for `timeout_ops` attribute

        Args:
            N/A

        Returns:
            float: timeout_ops value

        Raises:
            N/A

        """
        return self._base_channel_args.timeout_ops

    @timeout_ops.setter
    def timeout_ops(self, value: float) -> None:
        """
        Setter for `timeout_ops` attribute

        Args:
            value: float value for timeout_ops

        Returns:
            None

        Raises:
            ScrapliTypeError: if value is not of type int/float

        """
        self.logger.debug(f"setting 'timeout_ops' value to '{value}'")

        if not isinstance(value, (int, float)):
            raise ScrapliTypeError

        if value == 0:
            self.logger.debug("'timeout_ops' value is 0, this will disable timeout decorator")

        self._base_channel_args.timeout_ops = value

    def isalive(self) -> bool:
        """
        Check if underlying transport is "alive"

        Args:
            N/A

        Returns:
            bool: True/False if transport is alive

        Raises:
            N/A

        """
        alive: bool = self.transport.isalive()
        return alive

    def _pre_open_closing_log(self, closing: bool = False) -> None:
        """
        Emit "pre open" log message for consistency between sync/async drivers

        Args:
            closing: bool indicating if message is for closing not opening

        Returns:
            None

        Raises:
            N/A

        """
        operation = "closing" if closing else "opening"

        self.logger.info(f"{operation} connection to '{self.host}' on port '{self.port}'")

    def _post_open_closing_log(self, closing: bool = False) -> None:
        """
        Emit "post open" log message for consistency between sync/async drivers

        Args:
            closing: bool indicating if message is for closing not opening

        Returns:
            None

        Raises:
            N/A

        """
        operation = "closed" if closing else "opened"

        self.logger.info(
            f"connection to '{self.host}' on port '{self.port}' {operation} successfully"
        )
