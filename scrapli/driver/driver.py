"""scrapli.driver.driver"""
import logging
import os
import re
from pathlib import Path
from types import TracebackType
from typing import Any, Callable, Dict, Optional, Tuple, Type, Union

from scrapli.channel import CHANNEL_ARGS, Channel
from scrapli.helper import resolve_ssh_config, resolve_ssh_known_hosts
from scrapli.transport import (
    MIKO_TRANSPORT_ARGS,
    SSH2_TRANSPORT_ARGS,
    SYSTEM_SSH_TRANSPORT_ARGS,
    TELNET_TRANSPORT_ARGS,
    MikoTransport,
    SSH2Transport,
    SystemSSHTransport,
    TelnetTransport,
    Transport,
)

TRANSPORT_CLASS: Dict[str, Callable[..., Transport]] = {
    "system": SystemSSHTransport,
    "ssh2": SSH2Transport,
    "paramiko": MikoTransport,
    "telnet": TelnetTransport,
}
TRANSPORT_ARGS: Dict[str, Tuple[str, ...]] = {
    "system": SYSTEM_SSH_TRANSPORT_ARGS,
    "ssh2": SSH2_TRANSPORT_ARGS,
    "paramiko": MIKO_TRANSPORT_ARGS,
    "telnet": TELNET_TRANSPORT_ARGS,
}
TRANSPORT_BASE_ARGS = (
    "host",
    "port",
    "keepalive",
    "keepalive_interval",
    "keepalive_type",
    "keepalive_pattern",
    "timeout_socket",
    "timeout_transport",
    "timeout_exit",
)
LOG = logging.getLogger("scrapli_base")


class Scrape:
    def __init__(
        self,
        host: str = "",
        port: int = 22,
        auth_username: str = "",
        auth_password: str = "",
        auth_private_key: str = "",
        auth_strict_key: bool = True,
        timeout_socket: int = 5,
        timeout_transport: int = 5,
        timeout_ops: int = 10,
        timeout_exit: bool = True,
        keepalive: bool = False,
        keepalive_interval: int = 30,
        keepalive_type: str = "network",
        keepalive_pattern: str = "\005",
        comms_prompt_pattern: str = r"^[a-z0-9.\-@()/:]{1,32}[#>$]\s*$",
        comms_return_char: str = "\n",
        comms_ansi: bool = False,
        ssh_config_file: Union[str, bool] = False,
        ssh_known_hosts_file: Union[str, bool] = False,
        on_open: Optional[Callable[..., Any]] = None,
        on_close: Optional[Callable[..., Any]] = None,
        transport: str = "system",
    ):
        """
        Scrape Object

        Scrape is the base class for NetworkDriver, and subsequent platform specific drivers (i.e.
        IOSXEDriver). Scrape can be used on its own and offers a semi-pexpect like experience in
        that it doesn't know or care about privilege levels, platform types, and things like that.

        *Note* most arguments passed to Scrape do not actually get assigned to the scrape object
        itself, but instead are used to construct the Transport and Channel classes that Scrape
        relies on, see Transport and Channel docs for details.

        Args:
            host: host ip/name to connect to
            port: port to connect to
            auth_username: username for authentication
            auth_private_key: path to private key for authentication
            auth_password: password for authentication
            auth_strict_key: strict host checking or not -- applicable for system ssh driver only
            timeout_socket: timeout for establishing socket in seconds
            timeout_transport: timeout for ssh|telnet transport in seconds
            timeout_ops: timeout for ssh channel operations
            timeout_exit: True/False close transport if timeout encountered. If False and keepalives
                are in use, keepalives will prevent program from exiting so you should be sure to
                catch Timeout exceptions and handle them appropriately
            keepalive: whether or not to try to keep session alive
            keepalive_interval: interval to use for session keepalives
            keepalive_type: network|standard -- 'network' sends actual characters over the
                transport channel. This is useful for network-y type devices that may not support
                'standard' keepalive mechanisms. 'standard' attempts to use whatever 'standard'
                keepalive mechanisms are available in the selected transport mechanism. Check the
                transport documentation for details on what is supported and/or how it is
                implemented for any given transport driver
            keepalive_pattern: pattern to send to keep network channel alive. Default is
                u'\005' which is equivalent to 'ctrl+e'. This pattern moves cursor to end of the
                line which should be an innocuous pattern. This will only be entered *if* a lock
                can be acquired. This is only applicable if using keepalives and if the keepalive
                type is 'network'
            comms_prompt_pattern: raw string regex pattern -- preferably use `^` and `$` anchors!
                this is the single most important attribute here! if this does not match a prompt,
                scrapli will not work!
                IMPORTANT: regex search uses multi-line + case insensitive flags. multi-line allows
                for highly reliably matching for prompts however we do NOT strip trailing whitespace
                for each line, so be sure to add '\\s?' or similar if your device needs that. This
                should be mostly sorted for you if using network drivers (i.e. `IOSXEDriver`).
                Lastly, the case insensitive is just a convenience factor so i can be lazy.
            comms_return_char: character to use to send returns to host
            comms_ansi: True/False strip comms_ansi characters from output
            ssh_config_file: string to path for ssh config file, True to use default ssh config file
                or False to ignore default ssh config file
            ssh_known_hosts_file: string to path for ssh known hosts file, True to use default known
                file locations. Only applicable/needed if `auth_strict_key` is set to True
            on_open: callable that accepts the class instance as its only argument. this callable,
                if provided, is executed immediately after authentication is completed. Common use
                cases for this callable would be to disable paging or accept any kind of banner
                message that prompts a user upon connection
            on_close: callable that accepts the class instance as its only argument. this callable,
                if provided, is executed immediately prior to closing the underlying transport.
                Common use cases for this callable would be to save configurations prior to exiting,
                or to logout properly to free up vtys or similar.
            transport: system|ssh2|paramiko|telnet -- type of transport to use for connection
                system uses system available ssh (/usr/bin/ssh)
                ssh2 uses ssh2-python
                paramiko uses... paramiko
                telnet uses telnetlib
                choice of driver depends on the features you need. in general system is easiest as
                it will just 'auto-magically' use your ssh config file ('~/.ssh/config' or
                '/etc/ssh/config_file'). ssh2 is very very fast as it is a thin wrapper around
                libssh2 however it is slightly feature limited. paramiko is slower than ssh2, but
                has more features built in (though scrapli does not expose/support them all).

        Returns:
            N/A  # noqa: DAR202

        Raises:
            ValueError: if transport value is invalid

        """
        # create a dict of all "initialization" args for posterity and for passing to Transport
        # and Channel objects
        self._initialization_args: Dict[str, Any] = {}

        self._setup_host(host, port)
        self._setup_auth(auth_username, auth_password, auth_private_key, auth_strict_key)
        self._setup_timeouts(timeout_socket, timeout_transport, timeout_ops, timeout_exit)
        self._setup_keepalive(keepalive, keepalive_type, keepalive_interval, keepalive_pattern)
        self._setup_comms(comms_prompt_pattern, comms_return_char, comms_ansi)
        self._setup_callables(on_open, on_close)

        if transport not in ("ssh2", "paramiko", "system", "telnet"):
            raise ValueError(
                f"`transport` should be one of ssh2|paramiko|system|telnet, got `{transport}`"
            )
        self._transport = transport

        if transport != "telnet":
            self._setup_ssh_args(ssh_config_file, ssh_known_hosts_file)

        self.transport_class, self.transport_args = self._transport_factory(transport)
        self.transport = self.transport_class(**self.transport_args)

        self.channel_args: Dict[str, Any] = {}
        for arg in CHANNEL_ARGS:
            if arg == "transport":
                continue
            self.channel_args[arg] = self._initialization_args.get(arg)
        self.channel = Channel(self.transport, **self.channel_args)

    def __enter__(self) -> "Scrape":
        """
        Enter method for context manager

        Args:
            N/A

        Returns:
            self: instance of self

        Raises:
            N/A

        """
        self.open()
        return self

    def __exit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """
        Exit method to cleanup for context manager

        Args:
            exception_type: exception type being raised
            exception_value: message from exception being raised
            traceback: traceback from exception being raised

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.close()

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
        return f"Scrape Object for host {self._host}"

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
        return (
            f"{self.__class__.__name__}("
            f"host={self._initialization_args['host']!r}, "
            f"port={self._initialization_args['port']!r}, "
            f"auth_username={self._initialization_args['auth_username']!r}, "
            f"auth_password={self._initialization_args['auth_password']!r}, "
            f"auth_private_key={self._initialization_args['auth_private_key']!r}, "
            f"auth_strict_key={self._initialization_args['auth_strict_key']!r}, "
            f"timeout_socket={self._initialization_args['timeout_socket']!r}, "
            f"timeout_transport={self._initialization_args['timeout_transport']!r}, "
            f"timeout_ops={self._initialization_args['timeout_ops']!r}, "
            f"timeout_exit={self._initialization_args['timeout_exit']!r}, "
            f"keepalive={self._initialization_args['keepalive']!r}, "
            f"keepalive_interval={self._initialization_args['keepalive_interval']!r}, "
            f"keepalive_type={self._initialization_args['keepalive_type']!r}, "
            f"keepalive_pattern={self._initialization_args['keepalive_pattern']!r}, "
            f"comms_prompt_pattern={self._initialization_args['comms_prompt_pattern']!r}, "
            f"comms_return_char={self._initialization_args['comms_return_char']!r}, "
            f"comms_ansi={self._initialization_args['comms_ansi']!r}, "
            f"ssh_config_file={self._initialization_args['ssh_config_file']!r}, "
            f"ssh_known_hosts_file={self._initialization_args['ssh_known_hosts_file']!r}, "
            f"on_open={self.on_open!r}, "
            f"on_close={self.on_close!r}, "
            f"transport={self._transport!r})"
        )

    def _setup_host(self, host: str, port: int) -> None:
        """
        Parse and setup host attributes

        Args:
            host: host to parse/set
            port: port to parse/set

        Returns:
            N/A  # noqa: DAR202

        Raises:
            ValueError: if host is not provided
            TypeError: if port is not an integer

        """
        if not host:
            raise ValueError("`host` should be a hostname/ip address, got nothing!")
        if not isinstance(port, int):
            raise TypeError(f"`port` should be int, got {type(port)}")
        self._host = host.strip()
        self._initialization_args["host"] = host.strip()
        self._initialization_args["port"] = port

    def _setup_auth(
        self, auth_username: str, auth_password: str, auth_private_key: str, auth_strict_key: bool
    ) -> None:
        """
        Parse and setup auth attributes

        Args:
            auth_username: username to parse/set
            auth_password: password to parse/set
            auth_private_key: public key to parse/set
            auth_strict_key: strict key to parse/set

        Returns:
            N/A  # noqa: DAR202

        Raises:
            TypeError: if auth_strict_key is not a bool
            ValueError: if auth_private_key is not a valid file

        """
        if not isinstance(auth_strict_key, bool):
            raise TypeError(f"`auth_strict_key` should be bool, got {type(auth_strict_key)}")

        self._initialization_args["auth_strict_key"] = auth_strict_key
        self._initialization_args["auth_username"] = auth_username.strip()
        self._initialization_args["auth_password"] = auth_password.strip()

        if auth_private_key:
            public_key_path = Path.expanduser(Path(auth_private_key.strip()))
            if not public_key_path.is_file():
                raise ValueError(f"Provided public key `{auth_private_key}` is not a file")
            self._initialization_args["auth_private_key"] = os.path.expanduser(
                auth_private_key.strip().encode()
            )
        else:
            self._initialization_args["auth_private_key"] = auth_private_key.encode()

    def _setup_timeouts(
        self, timeout_socket: int, timeout_transport: int, timeout_ops: int, timeout_exit: bool
    ) -> None:
        """
        Parse and setup timeout attributes

        Args:
            timeout_socket: socket timeout to parse/set
            timeout_transport: transport timeout to parse/set
            timeout_ops: ops timeout to parse/set
            timeout_exit: timeout exit bool to parse/set

        Returns:
            N/A  # noqa: DAR202

        Raises:
            TypeError: if invalid type args provided

        """
        if not isinstance(timeout_exit, bool):
            raise TypeError(f"`timeout_exit` should be bool, got {type(timeout_exit)}")

        self._initialization_args["timeout_socket"] = int(timeout_socket)
        self._initialization_args["timeout_transport"] = int(timeout_transport)
        self._initialization_args["timeout_ops"] = int(timeout_ops)
        self._initialization_args["timeout_exit"] = timeout_exit

    def _setup_keepalive(
        self, keepalive: bool, keepalive_type: str, keepalive_interval: int, keepalive_pattern: str
    ) -> None:
        """
        Parse and setup keepalive attributes

        Args:
            keepalive: keepalive to parse/set
            keepalive_type: keepalive_type to parse/set
            keepalive_interval: keepalive_interval to parse/set
            keepalive_pattern: keepalive_pattern to parse/set

        Returns:
            N/A  # noqa: DAR202

        Raises:
            TypeError: if keepalive is not a bool
            ValueError: if keepalive_type is not valid

        """
        if not isinstance(keepalive, bool):
            raise TypeError(f"`keepalive` should be bool, got {type(keepalive)}")
        if keepalive_type not in ["network", "standard"]:
            raise ValueError(
                f"`{keepalive_type}` is an invalid keepalive_type; must be 'network' or 'standard'"
            )
        self._initialization_args["keepalive"] = keepalive
        self._initialization_args["keepalive_interval"] = int(keepalive_interval)
        self._initialization_args["keepalive_type"] = keepalive_type
        self._initialization_args["keepalive_pattern"] = keepalive_pattern

    def _setup_comms(
        self, comms_prompt_pattern: str, comms_return_char: str, comms_ansi: bool
    ) -> None:
        """
        Parse and setup auth attributes

        Args:
            comms_prompt_pattern: prompt pattern to parse/set
            comms_return_char: return char to parse/set
            comms_ansi: ansi val to parse/set

        Returns:
            N/A  # noqa: DAR202

        Raises:
            TypeError: if invalid type args provided

        """
        # try to compile prompt to raise TypeError before opening any connections
        re.compile(comms_prompt_pattern, flags=re.M | re.I)

        if not isinstance(comms_return_char, str):
            raise TypeError(f"`comms_return_char` should be str, got {type(comms_return_char)}")
        if not isinstance(comms_ansi, bool):
            raise TypeError(f"`comms_ansi` should be bool, got {type(comms_ansi)}")

        self._initialization_args["comms_prompt_pattern"] = comms_prompt_pattern
        self._initialization_args["comms_return_char"] = comms_return_char
        self._initialization_args["comms_ansi"] = comms_ansi

    def _setup_callables(
        self, on_open: Optional[Callable[..., Any]], on_close: Optional[Callable[..., Any]]
    ) -> None:
        """
        Parse and setup callables (on_open/on_close)

        Args:
            on_open: on_open to parse/set
            on_close: on_close to parse/set

        Returns:
            N/A  # noqa: DAR202

        Raises:
            TypeError: if port is not an integer

        """
        if on_open is not None and not callable(on_open):
            raise TypeError(f"`on_open` must be a callable, got {type(on_open)}")
        if on_close is not None and not callable(on_close):
            raise TypeError(f"`on_close` must be a callable, got {type(on_close)}")
        self.on_open = on_open
        self.on_close = on_close
        self._initialization_args["on_open"] = on_open
        self._initialization_args["on_close"] = on_close

    def _setup_ssh_args(
        self, ssh_config_file: Union[str, bool], ssh_known_hosts_file: Union[str, bool]
    ) -> None:
        """
        Parse and setup ssh related arguments

        Args:
            ssh_config_file: string to path for ssh config file, True to use default ssh config file
                or False to ignore default ssh config file
            ssh_known_hosts_file: string to path for ssh known hosts file, True to use default known
                file locations. Only applicable/needed if `auth_strict_key` is set to True

        Returns:
            N/A  # noqa: DAR202

        Raises:
            TypeError: if invalid config file or known hosts file value provided

        """
        if not isinstance(ssh_config_file, (str, bool)):
            raise TypeError(f"`ssh_config_file` must be str or bool, got {type(ssh_config_file)}")
        if not isinstance(ssh_known_hosts_file, (str, bool)):
            raise TypeError(
                "`ssh_known_hosts_file` must be str or bool, got " f"{type(ssh_known_hosts_file)}"
            )

        if ssh_config_file is not False:
            if isinstance(ssh_config_file, bool):
                cfg = ""
            else:
                cfg = ssh_config_file
            self._initialization_args["ssh_config_file"] = resolve_ssh_config(cfg)
        else:
            self._initialization_args["ssh_config_file"] = ""

        if ssh_known_hosts_file is not False:
            if isinstance(ssh_known_hosts_file, bool):
                known_hosts = ""
            else:
                known_hosts = ssh_known_hosts_file
            self._initialization_args["ssh_known_hosts_file"] = resolve_ssh_known_hosts(known_hosts)
        else:
            self._initialization_args["ssh_known_hosts_file"] = ""

    def _transport_factory(self, transport: str) -> Tuple[Callable[..., Any], Dict[str, Any]]:
        """
        Private factory method to produce transport class

        Args:
            transport: string name of transport class to use

        Returns:
            Transport: initialized Transport class

        Raises:
            N/A  # noqa

        """
        transport_class = TRANSPORT_CLASS[transport]
        required_transport_args = TRANSPORT_ARGS[transport]

        transport_args = {}
        for arg in TRANSPORT_BASE_ARGS:
            transport_args[arg] = self._initialization_args.get(arg)
        for arg in required_transport_args:
            transport_args[arg] = self._initialization_args.get(arg)
        return transport_class, transport_args

    def open(self) -> None:
        """
        Open Transport (socket/session) and establish channel

        If on_open callable provided, execute that callable after opening connection

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.transport.open()
        if self.on_open:
            self.on_open(self)

    def close(self) -> None:
        """
        Close Transport (socket/session)

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        if self.on_close:
            self.on_close(self)
        self.transport.close()

    def isalive(self) -> bool:
        """
        Check if underlying socket/channel is alive

        Args:
            N/A

        Returns:
            bool: True/False if socket/channel is alive

        Raises:
            N/A

        """
        alive = False
        try:
            alive = self.transport.isalive()
        except AttributeError:
            pass
        return alive
