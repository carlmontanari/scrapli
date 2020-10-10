"""scrapli.transport.systemssh"""
import re
from typing import Any, Dict, Optional

from scrapli.decorators import OperationTimeout, requires_open_session
from scrapli.exceptions import ScrapliAuthenticationFailed
from scrapli.helper import get_prompt_pattern, strip_ansi
from scrapli.ssh_config import SSHConfig
from scrapli.transport.ptyprocess import PtyProcess
from scrapli.transport.transport import Transport

SYSTEM_SSH_TRANSPORT_ARGS = (
    "auth_username",
    "auth_private_key",
    "auth_private_key_passphrase",
    "auth_password",
    "auth_strict_key",
    "auth_bypass",
    "ssh_config_file",
    "ssh_known_hosts_file",
    "comms_prompt_pattern",
    "comms_return_char",
    "comms_ansi",
    "timeout_ops",
)


class SystemSSHTransport(Transport):
    def __init__(
        self,
        host: str = "",
        port: int = 22,
        auth_username: str = "",
        auth_private_key: str = "",
        auth_private_key_passphrase: str = "",
        auth_password: str = "",
        auth_strict_key: bool = True,
        auth_bypass: bool = False,
        timeout_socket: int = 5,
        timeout_transport: int = 5,
        timeout_ops: float = 10,
        timeout_exit: bool = True,
        comms_prompt_pattern: str = r"^[a-z0-9.\-@()/:]{1,32}[#>$]$",
        comms_return_char: str = "\n",
        comms_ansi: bool = False,
        ssh_config_file: str = "",
        ssh_known_hosts_file: str = "",
        transport_options: Optional[Dict[str, Any]] = None,
    ) -> None:
        r"""
        SystemSSHTransport Object

        Inherit from Transport ABC
        SSH2Transport <- Transport (ABC)

        If using this driver, and passing a ssh_config_file (or setting this argument to `True`),
        all settings in the ssh config file will be superseded by any arguments passed here!

        Note that comms_prompt_pattern, comms_return_char and comms_ansi are only passed here to
        handle "in channel" authentication required by SystemSSH -- these are assigned to private
        attributes in this class and ignored after authentication. If you wish to modify these
        values on a "live" scrapli connection, modify them in the Channel object, i.e.
        `conn.channel.comms_prompt_pattern`. Additionally timeout_ops is passed and assigned to
        _timeout_ops to use the same timeout_ops that is used in Channel to decorate the
        authentication methods here.

        Args:
            host: host ip/name to connect to
            port: port to connect to
            auth_username: username for authentication
            auth_private_key: path to private key for authentication
            auth_private_key_passphrase: passphrase for decrypting ssh key if necessary
            auth_password: password for authentication
            auth_strict_key: True/False to enforce strict key checking (default is True)
            auth_bypass: bypass ssh key or password auth for devices without authentication, or that
                have auth prompts after ssh session establishment
            timeout_socket: timeout for ssh session to start -- this directly maps to ConnectTimeout
                ssh argument; see `man ssh_config`
            timeout_transport: timeout for transport in seconds. since system ssh is using popen/pty
                we can't really set a timeout directly, so this value governs the time timeout
                decorator for the transport read and write methods
            timeout_ops: timeout for telnet channel operations in seconds -- this is also the
                timeout for finding and responding to username and password prompts at initial
                login. This is assigned to a private attribute and is ignored after authentication
                is completed.
            timeout_exit: True/False close transport if timeout encountered. If False and keepalives
                are in use, keepalives will prevent program from exiting so you should be sure to
                catch Timeout exceptions and handle them appropriately
            comms_prompt_pattern: prompt pattern expected for device, same as the one provided to
                channel -- system ssh needs to know this to know how to decide if we are properly
                sending/receiving data -- i.e. we are not stuck at some password prompt or some
                other failure scenario. If using driver, this should be passed from driver (Scrape,
                or IOSXE, etc.) to this Transport class. This is assigned to a private attribute and
                is ignored after authentication is completed.
            comms_return_char: return character to use on the channel, same as the one provided to
                channel -- system ssh needs to know this to know what to send so that we can probe
                the channel to make sure we are authenticated and sending/receiving data. If using
                driver, this should be passed from driver (Scrape, or IOSXE, etc.) to this Transport
                class. This is assigned to a private attribute and is ignored after authentication
                is completed.
            comms_ansi: True/False strip comms_ansi characters from output; this value is assigned
                self._comms_ansi and is ignored after authentication. We only need it for transport
                on the off chance (maybe never?) that username/password prompts contain ansi
                characters, otherwise "comms_ansi" is really a channel attribute and is treated as
                such. This is assigned to a private attribute and is ignored after authentication
                is completed.
            ssh_config_file: string to path for ssh config file
            ssh_known_hosts_file: string to path for ssh known hosts file
            transport_options: SystemSSHTransport specific transport options (options that don't
                apply to any of the other transport classes) supplied in a dictionary where the key
                is the name of the option and the value is of course the value.
                - open_cmd: string or list of strings to extend the open_cmd with, for example:
                    `["-o", "KexAlgorithms=+diffie-hellman-group1-sha1"]` or:
                    `-oKexAlgorithms=+diffie-hellman-group1-sha1`
                    these commands will be appended to the open command that scrapli builds which
                    looks something like the following depending on the inputs provided:
                        ssh 172.31.254.1 -p 22 -o ConnectTimeout=5 -o ServerAliveInterval=10
                         -l scrapli -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null
                         -F /dev/null
                    You can pass any arguments that would be supported if you were ssh'ing on your
                    terminal "normally", passing some bad arguments can break things!

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        super().__init__(
            host,
            port,
            timeout_socket,
            timeout_transport,
            timeout_exit,
        )

        self.auth_username: str = auth_username
        self.auth_private_key: str = auth_private_key
        self.auth_private_key_passphrase: str = auth_private_key_passphrase
        self.auth_password: str = auth_password
        self.auth_strict_key: bool = auth_strict_key
        self.auth_bypass: bool = auth_bypass

        self._timeout_ops: float = timeout_ops
        self._comms_prompt_pattern: str = comms_prompt_pattern
        self._comms_return_char: str = comms_return_char
        self._comms_ansi: bool = comms_ansi
        self._process_ssh_config(ssh_config_file)
        self.ssh_known_hosts_file: str = ssh_known_hosts_file

        self.session: PtyProcess
        self.lib_auth_exception = ScrapliAuthenticationFailed
        self._isauthenticated = False

        # ensure we set transport_options to a dict if its left as None
        self.transport_options = transport_options or {}

        self.open_cmd = ["ssh", self.host]
        self._build_open_cmd()

    def _process_ssh_config(self, ssh_config_file: str) -> None:
        """
        Method to parse ssh config file

        Ensure ssh_config_file is valid (if providing a string path to config file), or resolve
        config file if passed True.

        Args:
            ssh_config_file: string path to ssh config file; passed down from `Scrape`, or the
                `NetworkDriver` or subclasses of it, in most cases.

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        ssh = SSHConfig(ssh_config_file=ssh_config_file)
        self.ssh_config_file = ssh.ssh_config_file

    def _build_open_cmd(self) -> None:
        """
        Method to craft command to open ssh session

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.open_cmd.extend(["-p", str(self.port)])
        self.open_cmd.extend(["-o", f"ConnectTimeout={self.timeout_socket}"])
        self.open_cmd.extend(["-o", f"ServerAliveInterval={self.timeout_transport}"])
        if self.auth_private_key:
            self.open_cmd.extend(["-i", self.auth_private_key])
        if self.auth_username:
            self.open_cmd.extend(["-l", self.auth_username])
        if self.auth_strict_key is False:
            self.open_cmd.extend(["-o", "StrictHostKeyChecking=no"])
            self.open_cmd.extend(["-o", "UserKnownHostsFile=/dev/null"])
        else:
            self.open_cmd.extend(["-o", "StrictHostKeyChecking=yes"])
            if self.ssh_known_hosts_file:
                self.open_cmd.extend(["-o", f"UserKnownHostsFile={self.ssh_known_hosts_file}"])
        if self.ssh_config_file:
            self.open_cmd.extend(["-F", self.ssh_config_file])
        else:
            self.open_cmd.extend(["-F", "/dev/null"])

        user_args = self.transport_options.get("open_cmd", [])
        if isinstance(user_args, str):
            user_args = [user_args]
        self.open_cmd.extend(user_args)

    def open(self) -> None:
        """
        Parent method to open session, authenticate and acquire shell

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.logger.info(f"Attempting to authenticate to {self.host}")
        self._open_pty()
        self.logger.info(f"Successfully authenticated to {self.host}")

    def _ssh_message_handler(self, output: bytes) -> None:  # noqa: C901
        """
        Parse EOF messages from _pty_authenticate and create log/stack exception message

        Args:
            output: bytes output from _pty_authenticate

        Returns:
            N/A  # noqa: DAR202

        Raises:
            ScrapliAuthenticationFailed: if any errors are read in the output

        """
        msg = ""
        if b"host key verification failed" in output.lower():
            msg = f"Host key verification failed for host {self.host}"
        elif b"operation timed out" in output.lower() or b"connection timed out" in output.lower():
            msg = f"Timed out connecting to host {self.host}"
        elif b"no route to host" in output.lower():
            msg = f"No route to host {self.host}"
        elif b"no matching key exchange" in output.lower():
            msg = f"No matching key exchange found for host {self.host}"
            key_exchange_pattern = re.compile(
                pattern=rb"their offer: ([a-z0-9\-,]*)", flags=re.M | re.I
            )
            offered_key_exchanges_match = re.search(pattern=key_exchange_pattern, string=output)
            if offered_key_exchanges_match:
                offered_key_exchanges = offered_key_exchanges_match.group(1).decode()
                msg = (
                    f"No matching key exchange found for host {self.host}, their offer: "
                    f"{offered_key_exchanges}"
                )
        elif b"no matching cipher" in output.lower():
            msg = f"No matching cipher found for host {self.host}"
            ciphers_pattern = re.compile(pattern=rb"their offer: ([a-z0-9\-,]*)", flags=re.M | re.I)
            offered_ciphers_match = re.search(pattern=ciphers_pattern, string=output)
            if offered_ciphers_match:
                offered_ciphers = offered_ciphers_match.group(1).decode()
                msg = (
                    f"No matching cipher found for host {self.host}, their offer: {offered_ciphers}"
                )
        elif b"bad configuration" in output.lower():
            msg = f"Bad SSH configuration option(s) for host {self.host}"
            configuration_pattern = re.compile(
                pattern=rb"bad configuration option: ([a-z0-9\+\=,]*)", flags=re.M | re.I
            )
            configuration_issue_match = re.search(pattern=configuration_pattern, string=output)
            if configuration_issue_match:
                configuration_issues = configuration_issue_match.group(1).decode()
                msg = (
                    f"Bad SSH configuration option(s) for host {self.host}, bad option(s): "
                    f"{configuration_issues}"
                )
        elif b"WARNING: UNPROTECTED PRIVATE KEY FILE!" in output:
            msg = (
                f"Permissions for private key `{self.auth_private_key}` are too open, "
                "authentication failed!"
            )
        elif b"could not resolve hostname" in output.lower():
            msg = f"Could not resolve address for host `{self.host}`"
        if msg:
            self.logger.critical(msg)
            raise ScrapliAuthenticationFailed(msg)

    def _open_pty(self) -> bool:
        """
        Private method to open session with PtyProcess

        Args:
            N/A

        Returns:
            bool: True/False session was opened and authenticated

        Raises:
            ScrapliAuthenticationFailed: if all authentication means fail

        """
        self.logger.info(f"Attempting to open session with the following command: {self.open_cmd}")
        self.session = PtyProcess.spawn(self.open_cmd)
        self.logger.debug(f"Session to host {self.host} spawned")

        if not self.auth_bypass:
            self._authenticate()
        else:
            self.logger.info("`auth_bypass` is True, bypassing authentication")
            # if we skip auth, we'll manually set _isauthenticated to True
            self._isauthenticated = True

        if not self._isauthenticated and not self._system_isauthenticated():
            msg = f"Authentication to host {self.host} failed"
            self.logger.critical(msg)
            raise ScrapliAuthenticationFailed(msg)

        self.logger.debug(f"Authenticated to host {self.host} with password")
        return True

    @OperationTimeout("_timeout_ops", "Timed out attempting to authenticate")
    def _authenticate(self) -> None:
        """
        Private method to check initial authentication when using pty_session

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            ScrapliAuthenticationFailed: if we get EOF and _ssh_message_handler does not raise an
                explicit exception/message

        """
        output = b""
        prompt_pattern = get_prompt_pattern(prompt="", class_prompt=self._comms_prompt_pattern)
        while True:
            try:
                new_output = self.session.read()
                output += new_output
                self.logger.debug(f"Attempting to authenticate. Read: {repr(new_output)}")
            except EOFError as exc:
                self._ssh_message_handler(output=output)
                # if _ssh_message_handler didn't raise any exception, we can raise the standard
                # "did you disable strict key message/exception"
                msg = (
                    f"Failed to open connection to host {self.host}. Do you need to disable "
                    "`auth_strict_key`?"
                )
                self.logger.critical(msg)
                raise ScrapliAuthenticationFailed(msg) from exc

            # even if we dont hit EOF, we may still have hit a message we need to process such
            # as insecure key permissions
            self._ssh_message_handler(output=output)

            if self._comms_ansi or b"\x1B" in output:
                output = strip_ansi(output=output)
            if b"password" in output.lower():
                self.logger.info("Found password prompt, sending password")
                self.session.write(self.auth_password.encode())
                self.session.write(self._comms_return_char.encode())
                break
            if b"enter passphrase for key" in output.lower():
                self.logger.info("Found key passphrase prompt, sending passphrase")
                self.session.write(self.auth_private_key_passphrase.encode())
                self.session.write(self._comms_return_char.encode())
                break
            channel_match = re.search(pattern=prompt_pattern, string=output)
            if channel_match:
                self.logger.info(
                    "Found channel prompt, assuming that key based authentication has succeeded"
                )
                # set _isauthenticated to true, we've already authenticated, don't re-check
                self._isauthenticated = True
                break

    @OperationTimeout("_timeout_ops", "Timed out determining if session is authenticated")
    def _system_isauthenticated(self) -> bool:
        """
        Check if session is authenticated

        This is very naive -- it only knows if the sub process is alive and has not received an EOF.
        Beyond that we send the return character and re-read the channel.

        Args:
            N/A

        Returns:
            bool: True if authenticated, else False

        Raises:
            N/A

        """
        self.logger.debug("Attempting to determine if authentication was successful")

        if self.session.isalive() and not self.session.eof():
            prompt_pattern = get_prompt_pattern(prompt="", class_prompt=self._comms_prompt_pattern)
            self.session.write(self._comms_return_char.encode())
            self._wait_for_session_fd_ready(fd=self.session.fd)

            output = b""
            while True:
                new_output = self.session.read()
                output += new_output
                self.logger.debug(
                    f"Attempting to validate authentication. Read: {repr(new_output)}"
                )
                # we do not need to deal w/ line replacement for the actual output, only for
                # parsing if a prompt-like thing is at the end of the output
                output = output.replace(b"\r", b"")
                # always check to see if we should strip ansi here; if we don't handle this we
                # may raise auth failures for the wrong reason which would be confusing for
                # users
                if self._comms_ansi or b"\x1B" in output:
                    output = strip_ansi(output=output)
                channel_match = re.search(pattern=prompt_pattern, string=output)
                if channel_match:
                    self._isauthenticated = True
                    break
                if b"password:" in output.lower():
                    # if we see "password" we know auth failed (hopefully in all scenarios!)
                    self.logger.critical(
                        "Found `password:` in output, assuming password authentication failed"
                    )
                    break
                if output:
                    self.logger.debug(
                        f"Cannot determine if authenticated, \n\tRead: {repr(output)}"
                    )

        if self._isauthenticated:
            return True

        return False

    def close(self) -> None:
        """
        Close session and socket

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.session.close()
        self.logger.debug(f"Channel to host {self.host} closed")

    def isalive(self) -> bool:
        """
        Check if session is alive and session is authenticated

        Args:
            N/A

        Returns:
            bool: True if session is alive and session authenticated, else False

        Raises:
            N/A

        """
        if self.session.isalive() and self._isauthenticated and not self.session.eof():
            return True
        return False

    @requires_open_session()
    @OperationTimeout("timeout_transport", "Timed out reading from transport")
    def read(self) -> bytes:
        """
        Read data from the channel

        Args:
            N/A

        Returns:
            bytes: bytes output as read from channel

        Raises:
            N/A

        """
        read_bytes = 65535
        return self.session.read(read_bytes)

    @requires_open_session()
    @OperationTimeout("timeout_transport", "Timed out writing to transport")
    def write(self, channel_input: str) -> None:
        """
        Write data to the channel

        Args:
            channel_input: string to send to channel

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.session.write(channel_input.encode())

    def set_timeout(self, timeout: int) -> None:
        """
        Set session timeout

        Args:
            timeout: timeout in seconds

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.timeout_transport = timeout
