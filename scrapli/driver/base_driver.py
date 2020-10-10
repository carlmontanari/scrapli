"""scrapli.driver.base_driver"""
import os
import re
import sys
from logging import Logger, getLogger
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple, Union

from scrapli.channel import CHANNEL_ARGS
from scrapli.exceptions import UnsupportedPlatform
from scrapli.helper import _find_transport_plugin, resolve_ssh_config, resolve_ssh_known_hosts
from scrapli.transport import (
    SYSTEM_SSH_TRANSPORT_ARGS,
    TELNET_TRANSPORT_ARGS,
    SystemSSHTransport,
    TelnetTransport,
    Transport,
)

TRANSPORT_CLASS: Dict[str, Callable[..., Transport]] = {
    "system": SystemSSHTransport,
    "telnet": TelnetTransport,
}
TRANSPORT_ARGS: Dict[str, Tuple[str, ...]] = {
    "system": SYSTEM_SSH_TRANSPORT_ARGS,
    "telnet": TELNET_TRANSPORT_ARGS,
}
TRANSPORT_BASE_ARGS = (
    "host",
    "port",
    "timeout_socket",
    "timeout_transport",
    "timeout_exit",
)
ASYNCIO_TRANSPORTS = ("asyncssh",)


class ScrapeBase:
    def __init__(
        self,
        host: str = "",
        port: int = 22,
        auth_username: str = "",
        auth_password: str = "",
        auth_private_key: str = "",
        auth_private_key_passphrase: str = "",
        auth_strict_key: bool = True,
        auth_bypass: bool = False,
        timeout_socket: int = 5,
        timeout_transport: int = 10,
        timeout_ops: float = 30,
        timeout_exit: bool = True,
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
    ):
        r"""
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
            auth_private_key_passphrase: passphrase for decrypting ssh key if necessary
            auth_password: password for authentication
            auth_strict_key: strict host checking or not -- applicable for system ssh driver only
            auth_bypass: bypass ssh key or password auth for devices without authentication, or that
                have auth prompts after ssh session establishment. Currently only supported on
                system transport; ignored on other transports
            timeout_socket: timeout for establishing socket in seconds
            timeout_transport: timeout for ssh|telnet transport in seconds
            timeout_ops: timeout for ssh channel operations
            timeout_exit: True/False close transport if timeout encountered. If False and keepalives
                are in use, keepalives will prevent program from exiting so you should be sure to
                catch Timeout exceptions and handle them appropriately
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
                or to logout properly to free up vtys or similar.
            transport: system|telnet or a plugin -- type of transport to use for connection
                system uses system available ssh (/usr/bin/ssh)
                ssh2 uses ssh2-python *has been migrated to a plugin
                paramiko uses... paramiko *has been migrated to a plugin
                telnet uses telnetlib
                choice of driver depends on the features you need. in general system is easiest as
                it will just 'auto-magically' use your ssh config file ('~/.ssh/config' or
                '/etc/ssh/config_file'). ssh2 is very very fast as it is a thin wrapper around
                libssh2 however it is slightly feature limited. paramiko is slower than ssh2, but
                has more features built in (though scrapli does not expose/support them all).
            transport_options: dictionary of options to pass to selected transport class; see
                docs for given transport class for details of what to pass here

        Returns:
            N/A  # noqa: DAR202

        Raises:
            UnsupportedPlatform: if using windows with system transport

        """
        # create a dict of all "initialization" args for posterity and for passing to Transport
        # and Channel objects
        self._initialization_args: Dict[str, Any] = {}

        self._setup_host(host=host, port=port)
        self.logger: Logger = getLogger(f"scrapli.driver-{self._host}")

        self._setup_auth(
            auth_username=auth_username,
            auth_password=auth_password,
            auth_private_key=auth_private_key,
            auth_private_key_passphrase=auth_private_key_passphrase,
            auth_strict_key=auth_strict_key,
            auth_bypass=auth_bypass,
        )
        self._setup_timeouts(
            timeout_socket=timeout_socket,
            timeout_transport=timeout_transport,
            timeout_ops=timeout_ops,
            timeout_exit=timeout_exit,
        )
        self._timeout_ops: float = self._initialization_args["timeout_ops"]

        self._setup_comms(
            comms_prompt_pattern=comms_prompt_pattern,
            comms_return_char=comms_return_char,
            comms_ansi=comms_ansi,
        )
        self._setup_callables(on_init=on_init, on_open=on_open, on_close=on_close)

        if transport not in ("system", "telnet"):
            self.logger.info(f"Non-core transport `{transport}` selected")
        self._transport = transport

        if transport == "system" and sys.platform.startswith("win"):
            msg = "`system` transport is not supported on Windows, please use a different transport"
            raise UnsupportedPlatform(msg)

        if transport != "telnet":
            self._setup_ssh_args(
                ssh_config_file=ssh_config_file, ssh_known_hosts_file=ssh_known_hosts_file
            )

        self._initialization_args["transport_options"] = transport_options
        self.transport_class, self.transport_args = self._transport_factory(transport=transport)
        # so transport drivers don't need to support `transport_options` as an argument, if no
        # transport options provided, do nothing, otherwise add this to the args we ship to the
        # transport class
        if transport_options is not None:
            self.transport_args["transport_options"] = transport_options
        self.transport = self.transport_class(**self.transport_args)

        self.channel_args: Dict[str, Any] = {}
        for arg in CHANNEL_ARGS:
            if arg == "transport":
                continue
            self.channel_args[arg] = self._initialization_args.get(arg)

        if self.on_init:
            self.on_init()

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
            "auth_private_key_passphrase="
            f"{self._initialization_args['auth_private_key_passphrase']!r}, "
            f"auth_strict_key={self._initialization_args['auth_strict_key']!r}, "
            f"auth_bypass={self._initialization_args['auth_bypass']!r}, "
            f"timeout_socket={self._initialization_args['timeout_socket']!r}, "
            f"timeout_transport={self._initialization_args['timeout_transport']!r}, "
            f"timeout_ops={self._initialization_args['timeout_ops']!r}, "
            f"timeout_exit={self._initialization_args['timeout_exit']!r}, "
            f"comms_prompt_pattern={self._initialization_args['comms_prompt_pattern']!r}, "
            f"comms_return_char={self._initialization_args['comms_return_char']!r}, "
            f"comms_ansi={self._initialization_args['comms_ansi']!r}, "
            f"ssh_config_file={self._initialization_args.get('ssh_config_file')!r}, "
            f"ssh_known_hosts_file={self._initialization_args.get('ssh_known_hosts_file')!r}, "
            f"on_init={self.on_init!r}, "
            f"on_open={self.on_open!r}, "
            f"on_close={self.on_close!r}, "
            f"transport={self._transport!r}, "
            f"transport_options={self._initialization_args.get('transport_options')!r})"
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
        self,
        auth_username: str,
        auth_password: str,
        auth_private_key: str,
        auth_private_key_passphrase: str,
        auth_strict_key: bool,
        auth_bypass: bool,
    ) -> None:
        """
        Parse and setup auth attributes

        Args:
            auth_username: username to parse/set
            auth_password: password to parse/set
            auth_private_key: ssh key to parse/set
            auth_private_key_passphrase: ssh key passphrase to parse/set
            auth_strict_key: strict key to parse/set
            auth_bypass: bypass to parse/set

        Returns:
            N/A  # noqa: DAR202

        Raises:
            TypeError: if auth_strict_key is not a bool
            ValueError: if auth_private_key is not a valid file

        """
        if not isinstance(auth_strict_key, bool):
            raise TypeError(f"`auth_strict_key` should be bool, got {type(auth_strict_key)}")
        if not isinstance(auth_bypass, bool):
            raise TypeError(f"`auth_bypass` should be bool, got {type(auth_bypass)}")

        self._initialization_args["auth_strict_key"] = auth_strict_key
        self._initialization_args["auth_bypass"] = auth_bypass
        self._initialization_args["auth_username"] = auth_username.strip()
        self._initialization_args["auth_password"] = auth_password.strip()
        self._initialization_args[
            "auth_private_key_passphrase"
        ] = auth_private_key_passphrase.strip()

        if auth_private_key:
            private_key_path = Path.expanduser(Path(auth_private_key.strip()))
            if not private_key_path.is_file():
                raise ValueError(f"Provided public key `{auth_private_key}` is not a file")
            self._initialization_args["auth_private_key"] = os.path.expanduser(
                auth_private_key.strip()
            )
        else:
            self._initialization_args["auth_private_key"] = auth_private_key

    def _setup_timeouts(
        self,
        timeout_socket: int,
        timeout_transport: int,
        timeout_ops: float,
        timeout_exit: bool,
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
        self._initialization_args["timeout_ops"] = float(timeout_ops)
        self._initialization_args["timeout_exit"] = timeout_exit

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
        self,
        on_init: Optional[Callable[..., Any]],
        on_open: Optional[Callable[..., Any]],
        on_close: Optional[Callable[..., Any]],
    ) -> None:
        """
        Parse and setup callables (on_open/on_close)

        Args:
            on_init: on_init to parse/set
            on_open: on_open to parse/set
            on_close: on_close to parse/set

        Returns:
            N/A  # noqa: DAR202

        Raises:
            TypeError: if port is not an integer

        """
        if on_init is not None and not callable(on_init):
            raise TypeError(f"`on_init` must be a callable, got {type(on_init)}")
        if on_open is not None and not callable(on_open):
            raise TypeError(f"`on_open` must be a callable, got {type(on_open)}")
        if on_close is not None and not callable(on_close):
            raise TypeError(f"`on_close` must be a callable, got {type(on_close)}")
        self.on_init = on_init
        self.on_open = on_open
        self.on_close = on_close
        self._initialization_args["on_init"] = on_init
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
        transport_class = TRANSPORT_CLASS.get(transport, None)
        required_transport_args = TRANSPORT_ARGS.get(transport, ())

        if transport_class is None:
            transport_class, required_transport_args = _find_transport_plugin(transport=transport)

        transport_args = {}
        for arg in TRANSPORT_BASE_ARGS:
            transport_args[arg] = self._initialization_args.get(arg)
        for arg in required_transport_args:
            transport_args[arg] = self._initialization_args.get(arg)
        return transport_class, transport_args

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
