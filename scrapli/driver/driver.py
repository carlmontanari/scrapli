"""scrapli.driver.driver"""
import logging
import os
import re
from types import TracebackType
from typing import Any, Callable, Dict, Optional, Tuple, Type, Union

from scrapli.channel import CHANNEL_ARGS, Channel
from scrapli.helper import get_external_function, resolve_ssh_config, validate_external_function
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

LOG = logging.getLogger("scrapli_base")


class Scrape:
    def __init__(
        self,
        host: str = "",
        port: int = 22,
        auth_username: str = "",
        auth_password: str = "",
        auth_public_key: str = "",
        auth_strict_key: bool = True,
        timeout_socket: int = 5,
        timeout_transport: int = 5000,
        timeout_ops: int = 10,
        comms_prompt_pattern: str = r"^[a-z0-9.\-@()/:]{1,32}[#>$]$",
        comms_return_char: str = "\n",
        comms_ansi: bool = False,
        session_pre_login_handler: Union[str, Callable[..., Any]] = "",
        session_disable_paging: Union[str, Callable[..., Any]] = "terminal length 0",
        ssh_config_file: Union[str, bool] = False,
        transport: str = "system",
    ):
        """
        Scrape Object

        Scrape is the base class for NetworkDriver, and subsequent platform specific drivers (i.e.
        IOSXEDriver). Scrape can be used on its own and offers a semi-pexpect like experience in
        that it doesn't know or care about privilege levels, platform types, and things like that.

        Args:
            host: host ip/name to connect to
            port: port to connect to
            auth_username: username for authentication
            auth_public_key: path to public key for authentication
            auth_password: password for authentication
            auth_strict_key: strict host checking or not -- applicable for system ssh driver only
            timeout_socket: timeout for establishing socket in seconds
            timeout_transport: timeout for ssh|telnet transport in milliseconds
            timeout_ops: timeout for ssh channel operations
            comms_prompt_pattern: raw string regex pattern -- preferably use `^` and `$` anchors!
                this is the single most important attribute here! if this does not match a prompt,
                scrapli will not work!
                IMPORTANT: regex search uses multi-line + case insensitive flags. multi-line allows
                for highly reliably matching for prompts after stripping trailing white space,
                case insensitive is just a convenience factor so i can be lazy.
            comms_return_char: character to use to send returns to host
            comms_ansi: True/False strip comms_ansi characters from output
            session_pre_login_handler: callable or string that resolves to an importable function to
                handle pre-login (pre disable paging) operations
            session_disable_paging: callable, string that resolves to an importable function, or
                string to send to device to disable paging
            ssh_config_file: string to path for ssh config file, True to use default ssh config file
                or False to ignore default ssh config file
            transport: system|ssh2|paramiko|telnet -- type of transport to use
                system uses system available ssh (/usr/bin/ssh)
                ssh2 uses ssh2-python
                paramiko uses... paramiko
                telnet uses telnetlib
                choice of driver depends on the features you need. in general system is easiest as
                it will just "auto-magically" use your ssh config file (~/.ssh/config or
                /etc/ssh/config_file). ssh2 is very very fast as it is a thin wrapper around libssh2
                however it is slightly feature limited. paramiko is slower than ssh2, but has more
                features built in (though scrapli does not expose/support them all).

        Returns:
            N/A  # noqa: DAR202

        Raises:
            TypeError: if auth_strict_key is not a bool
            ValueError: if driver value is invalid

        """
        self.host = host.strip()
        if not isinstance(port, int):
            raise TypeError(f"port should be int, got {type(port)}")
        self.port = port

        self.auth_username: str = ""
        self.auth_password: str = ""
        if not isinstance(auth_strict_key, bool):
            raise TypeError(f"auth_strict_key should be bool, got {type(auth_strict_key)}")
        self.auth_strict_key = auth_strict_key
        self._setup_auth(auth_username, auth_password, auth_public_key)

        self.timeout_socket = int(timeout_socket)
        self.timeout_transport = int(timeout_transport)
        self.timeout_ops = int(timeout_ops)

        self.comms_prompt_pattern: str = ""
        self.comms_return_char: str = ""
        self.comms_ansi: bool = False
        self._setup_comms(comms_prompt_pattern, comms_return_char, comms_ansi)

        self.session_pre_login_handler: Optional[Callable[..., Any]] = None
        self.session_disable_paging: Union[str, Callable[..., Any]] = ""
        self._setup_session(session_pre_login_handler, session_disable_paging)

        if transport not in ("ssh2", "paramiko", "system", "telnet"):
            raise ValueError(
                f"transport should be one of ssh2|paramiko|system|telnet, got {transport}"
            )

        if not isinstance(ssh_config_file, (str, bool)):
            raise TypeError(f"ssh_config_file should be str or bool, got {type(ssh_config_file)}")
        if transport != "telnet" and ssh_config_file is not False:
            if isinstance(ssh_config_file, bool):
                cfg = ""
            else:
                cfg = ssh_config_file
            self.ssh_config_file = resolve_ssh_config(cfg)
        else:
            self.ssh_config_file = ""

        self.transport: Transport
        self.transport_class, self.transport_args = self._transport_factory(transport)

        self.channel: Channel
        self.channel_args = {}
        for arg in CHANNEL_ARGS:
            if arg == "transport":
                continue
            self.channel_args[arg] = getattr(self, arg)

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
        return f"Scrape Object for host {self.host}"

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
        class_dict = self.__dict__.copy()
        class_dict["auth_password"] = "********"
        return f"Scrape {class_dict}"

    def _setup_auth(self, auth_username: str, auth_password: str, auth_public_key: str) -> None:
        """
        Parse and setup auth attributes

        Args:
            auth_username: username to parse/set
            auth_password: password to parse/set
            auth_public_key: public key to parse/set

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.auth_username = auth_username.strip()
        if auth_public_key:
            self.auth_public_key = os.path.expanduser(auth_public_key.strip().encode())
        else:
            self.auth_public_key = auth_public_key.encode()
        if auth_password:
            self.auth_password = auth_password.strip()
        else:
            self.auth_password = auth_password

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
        self.comms_prompt_pattern = comms_prompt_pattern
        if not isinstance(comms_return_char, str):
            raise TypeError(f"comms_return_char should be str, got {type(comms_return_char)}")
        self.comms_return_char = comms_return_char
        if not isinstance(comms_ansi, bool):
            raise TypeError(f"comms_ansi should be bool, got {type(comms_ansi)}")
        self.comms_ansi = comms_ansi

    def _setup_session(
        self,
        session_pre_login_handler: Union[str, Callable[..., Any]],
        session_disable_paging: Union[str, Callable[..., Any]],
    ) -> None:
        """
        Parse and setup session attributes

        Args:
            session_pre_login_handler: pre login handler to parse/set
            session_disable_paging: disable paging to parse/set

        Returns:
            N/A  # noqa: DAR202

        Raises:
            TypeError: if invalid type args provided

        """
        if session_pre_login_handler:
            self.session_pre_login_handler = self._set_session_pre_login_handler(
                session_pre_login_handler
            )
        else:
            self.session_pre_login_handler = None
        if callable(session_disable_paging):
            self.session_disable_paging = session_disable_paging
        if not isinstance(session_disable_paging, str) and not callable(session_disable_paging):
            raise TypeError(
                "session_disable_paging should be str or callable, got "
                f"{type(session_disable_paging)}"
            )
        if session_disable_paging != "terminal length 0":
            try:
                self.session_disable_paging = self._set_session_disable_paging(
                    session_disable_paging
                )
            except TypeError:
                self.session_disable_paging = session_disable_paging
        else:
            self.session_disable_paging = "terminal length 0"

    @staticmethod
    def _set_session_pre_login_handler(
        session_pre_login_handler: Union[str, Callable[..., Any]]
    ) -> Optional[Callable[..., Any]]:
        """
        Return session_pre_login_handler argument

        Args:
            session_pre_login_handler: callable function, or string representing a path to
                a callable

        Returns:
            session_pre_login_handler: callable or default empty string value

        Raises:
            TypeError: if provided string does not result in a callable

        """
        if callable(session_pre_login_handler):
            return session_pre_login_handler
        if not validate_external_function(session_pre_login_handler):
            LOG.critical(f"Invalid comms_pre_login_handler: {session_pre_login_handler}")
            raise TypeError(
                f"{session_pre_login_handler} is an invalid session_pre_login_handler function "
                "or path to a function."
            )
        return get_external_function(session_pre_login_handler)

    @staticmethod
    def _set_session_disable_paging(
        session_disable_paging: Union[Callable[..., Any], str]
    ) -> Union[Callable[..., Any], str]:
        """
        Return session_disable_paging argument

        Args:
            session_disable_paging: callable function, string representing a path to
                a callable, or a string to send to device to disable paging

        Returns:
            session_disable_paging: callable or string to use to disable paging

        Raises:
            TypeError: if provided string does not result in a callable

        """
        if callable(session_disable_paging):
            return session_disable_paging
        if not validate_external_function(session_disable_paging):
            raise TypeError(
                f"{session_disable_paging} is an invalid session_disable_paging function or path "
                "to a function. Assuming this is string to send to disable paging."
            )
        return get_external_function(session_disable_paging)

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
        for arg in required_transport_args:
            transport_args[arg] = getattr(self, arg)
        return transport_class, transport_args

    def open(self) -> None:
        """
        Open Transport (socket/session) and establish channel

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.transport = self.transport_class(**self.transport_args)
        self.transport.open()
        self.channel = Channel(self.transport, **self.channel_args)

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
        try:
            alive = self.transport.isalive()
        except AttributeError:
            alive = False
        return alive
