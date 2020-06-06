"""scrapli.transport.systemssh"""
import os
import re
from select import select
from subprocess import PIPE, Popen
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

from scrapli.decorators import operation_timeout, requires_open_session
from scrapli.exceptions import ScrapliAuthenticationFailed, ScrapliTimeout
from scrapli.helper import get_prompt_pattern, strip_ansi
from scrapli.ssh_config import SSHConfig
from scrapli.transport.ptyprocess import PtyProcess
from scrapli.transport.transport import Transport

if TYPE_CHECKING:
    PopenBytes = Popen[bytes]  # pylint: disable=E1136; # pragma:  no cover


SYSTEM_SSH_TRANSPORT_ARGS = (
    "auth_username",
    "auth_private_key",
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
        auth_password: str = "",
        auth_strict_key: bool = True,
        auth_bypass: bool = False,
        timeout_socket: int = 5,
        timeout_transport: int = 5,
        timeout_ops: int = 10,
        timeout_exit: bool = True,
        keepalive: bool = False,
        keepalive_interval: int = 30,
        keepalive_type: str = "",
        keepalive_pattern: str = "\005",
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

        SystemSSHTransport *always* prefers public key auth if given the option! If auth_private_key
        is set in the provided arguments OR if ssh_config_file is passed/True and there is a key for
        ANY match (i.e. `*` has a key in ssh config file!!), we will use that key! If public key
        auth fails and a username and password is set (manually or by ssh config file), password
        auth will be attempted.

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
            keepalive: whether or not to try to keep session alive
            keepalive_interval: interval to use for session keepalives
            keepalive_type: network|standard -- 'network' sends actual characters over the
                transport channel. This is useful for network-y type devices that may not support
                'standard' keepalive mechanisms. 'standard' is not currently implemented for
                system ssh
            keepalive_pattern: pattern to send to keep network channel alive. Default is
                u'\005' which is equivalent to 'ctrl+e'. This pattern moves cursor to end of the
                line which should be an innocuous pattern. This will only be entered *if* a lock
                can be acquired. This is only applicable if using keepalives and if the keepalive
                type is 'network'
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
            keepalive,
            keepalive_interval,
            keepalive_type,
            keepalive_pattern,
        )

        self.auth_username: str = auth_username
        self.auth_private_key: str = auth_private_key
        self.auth_password: str = auth_password
        self.auth_strict_key: bool = auth_strict_key
        self.auth_bypass: bool = auth_bypass

        self._timeout_ops: int = timeout_ops
        self._comms_prompt_pattern: str = comms_prompt_pattern
        self._comms_return_char: str = comms_return_char
        self._comms_ansi: bool = comms_ansi
        self._process_ssh_config(ssh_config_file)
        self.ssh_known_hosts_file: str = ssh_known_hosts_file

        self.session: Union[Popen[bytes], PtyProcess]  # pylint: disable=E1136
        self.lib_auth_exception = ScrapliAuthenticationFailed
        self._isauthenticated = False

        # ensure we set transport_options to a dict if its left as None
        self.transport_options = transport_options or {}

        self.open_cmd = ["ssh", self.host]
        self._build_open_cmd()

        # create stdin/stdout fd in case we can use pipes for session
        self._stdin_fd = -1
        self._stdout_fd = -1

    def _process_ssh_config(self, ssh_config_file: str) -> None:
        """
        Method to parse ssh config file

        Ensure ssh_config_file is valid (if providing a string path to config file), or resolve
        config file if passed True. Search config file for any private key, if ANY matching key is
        found and user has not provided a private key, set `auth_private_key` to the value of the
        found key. This is because we prefer to use `open_pipes` over `open_pty`!

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
        host_config = ssh.lookup(host=self.host)
        if not self.auth_private_key and host_config.identity_file:
            self.auth_private_key = os.path.expanduser(host_config.identity_file.strip())

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

        If possible it is preferable to use the `_open_pipes` method, but we can only do this IF we
        can authenticate with public key authorization (because we don't have to spawn a PTY; if no
        public key we have to spawn PTY to deal w/ authentication prompts). IF we get a private key
        provided, use pipes method, otherwise we will just deal with `_open_pty`. `_open_pty` is
        less preferable because we have to spawn a PTY and cannot as easily tell if SSH
        authentication is successful. With `_open_pipes` we can read stderr which contains the
        output from the verbose flag for SSH -- this contains a message that indicates success of
        SSH auth. In the case of `_open_pty` we have to read from the channel directly like in the
        case of telnet... so it works, but its just a bit less desirable.

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            ScrapliAuthenticationFailed: if all authentication means fail

        """
        self.session_lock.acquire()

        self.logger.info(f"Attempting to authenticate to {self.host}")

        # if auth_bypass kick off keepalive thread if necessary and return
        if self.auth_bypass:
            self.logger.info("`auth_bypass` is True, bypassing authentication")
            self._open_pty(skip_auth=True)
            self._session_keepalive()
            return

        # if authenticating with private key prefer to use open pipes
        # _open_pipes uses subprocess Popen which is preferable to opening a pty
        # if _open_pipes fails and no password available, raise failure, otherwise try password auth
        if self.auth_private_key:
            open_pipes_result = self._open_pipes()
            if open_pipes_result:
                if self.keepalive:
                    self._session_keepalive()
                return
            if not self.auth_password or not self.auth_username:
                msg = (
                    f"Failed to authenticate to host {self.host} with private key "
                    f"`{self.auth_private_key}`. Unable to continue authentication, "
                    "missing username, password, or both."
                )
                self.logger.critical(msg)
                raise ScrapliAuthenticationFailed(msg)
            msg = (
                f"Failed to authenticate to host {self.host} with private key "
                f"`{self.auth_private_key}`. Attempting to continue with password authentication."
            )
            self.logger.critical(msg)

        # If public key auth fails or is not configured, open a pty session
        if not self._open_pty():
            msg = f"Authentication to host {self.host} failed"
            self.logger.critical(msg)
            raise ScrapliAuthenticationFailed(msg)

        self.logger.info(f"Successfully authenticated to {self.host}")

        if self.keepalive:
            self._session_keepalive()

    def _open_pipes(self) -> bool:
        """
        Private method to open session with subprocess.Popen

        Args:
            N/A

        Returns:
            bool: True/False session was opened and authenticated

        Raises:
            N/A

        """
        # import here so that we dont blow up when running on windows (windows users need to use
        #  ssh2 or paramiko transport)
        import pty  # pylint: disable=C0415

        # copy the open_cmd as we don't want to update the objects open_cmd until we know we can
        # authenticate. add verbose output and disable batch mode (disables passphrase/password
        # queries). If auth is successful update the object open_cmd to represent what was used
        open_cmd = self.open_cmd.copy()
        open_cmd.append("-v")
        open_cmd.extend(["-o", "BatchMode=yes"])

        self.logger.info(f"Attempting to open session with the following command: {open_cmd}")

        stdout_master_pty, stdout_slave_pty = pty.openpty()
        stdin_master_pty, stdin_slave_pty = pty.openpty()

        self.session = Popen(
            open_cmd,
            bufsize=0,
            shell=False,
            stdin=stdin_slave_pty,
            stdout=stdout_slave_pty,
            stderr=PIPE,
        )
        # close the slave fds, don't need them anymore
        os.close(stdin_slave_pty)
        os.close(stdout_slave_pty)
        self.logger.debug(f"Session to host {self.host} spawned")

        try:
            self._pipes_isauthenticated(self.session)
            if self._isauthenticated is False:
                return False
        except TimeoutError:
            # If auth fails, kill the popen session, also need to manually close the stderr pipe
            # for some reason... unclear why, but w/out this it will hang open
            if self.session.stderr is not None:
                stderr_fd = self.session.stderr.fileno()
                os.close(stderr_fd)
            self.session.kill()

            # close the ptys we forked
            os.close(stdin_master_pty)
            os.close(stdout_master_pty)
            # it seems that killing the process/fds somehow unlocks the thread? very unsure how/why
            self.session_lock.acquire()
            return False

        self.logger.debug(f"Authenticated to host {self.host} with public key")

        # set stdin/stdout to the new master pty fds
        self._stdin_fd = stdin_master_pty
        self._stdout_fd = stdout_master_pty

        self.open_cmd = open_cmd
        self.session_lock.release()
        return True

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
        elif b"no matching key exchange found" in output.lower():
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
        elif b"no matching cipher found" in output.lower():
            msg = f"No matching cipher found for host {self.host}"
            ciphers_pattern = re.compile(pattern=rb"their offer: ([a-z0-9\-,]*)", flags=re.M | re.I)
            offered_ciphers_match = re.search(pattern=ciphers_pattern, string=output)
            if offered_ciphers_match:
                offered_ciphers = offered_ciphers_match.group(1).decode()
                msg = (
                    f"No matching cipher found for host {self.host}, their offer: {offered_ciphers}"
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

    @operation_timeout("_timeout_ops", "Timed out determining if session is authenticated")
    def _pipes_isauthenticated(self, pipes_session: "PopenBytes") -> bool:
        """
        Private method to check initial authentication when using subprocess.Popen

        Since we always run ssh with `-v` we can simply check the stderr (where verbose output goes)
        to see if `Authenticated to [our host]` is in the output.

        Args:
            pipes_session: Popen pipes session object

        Returns:
            bool: True/False session was authenticated

        Raises:
            ScrapliTimeout: if we cant read from stderr of the session

        """
        if pipes_session.stderr is None:
            raise ScrapliTimeout(f"Could not read stderr while connecting to host {self.host}")

        output = b""
        while True:
            output += pipes_session.stderr.read(65535)
            if f"authenticated to {self.host}".encode() in output.lower():
                self._isauthenticated = True
                return True
            if (
                b"next authentication method: keyboard-interactive" in output.lower()
                or b"next authentication method: password" in output.lower()
            ):
                return False
            self._ssh_message_handler(output=output)

    def _open_pty(self, skip_auth: bool = False) -> bool:
        """
        Private method to open session with PtyProcess

        Args:
            skip_auth: skip auth in the case of auth_bypass mode

        Returns:
            bool: True/False session was opened and authenticated

        Raises:
            N/A

        """
        self.logger.info(f"Attempting to open session with the following command: {self.open_cmd}")
        self.session = PtyProcess.spawn(self.open_cmd)
        self.logger.debug(f"Session to host {self.host} spawned")
        self.session_lock.release()
        if skip_auth:
            return True
        self._pty_authenticate(pty_session=self.session)
        if not self._pty_isauthenticated(self.session):
            return False
        self.logger.debug(f"Authenticated to host {self.host} with password")
        return True

    @operation_timeout("_timeout_ops", "Timed out looking for SSH login password prompt")
    def _pty_authenticate(self, pty_session: PtyProcess) -> None:
        """
        Private method to check initial authentication when using pty_session

        Args:
            pty_session: PtyProcess session object

        Returns:
            N/A  # noqa: DAR202

        Raises:
            ScrapliAuthenticationFailed: if we get EOF and _ssh_message_handler does not raise an
                explicit exception/message

        """
        self.session_lock.acquire()
        output = b""
        while True:
            try:
                new_output = pty_session.read()
                output += new_output
                self.logger.debug(f"Attempting to authenticate. Read: {repr(new_output)}")
            except EOFError:
                self._ssh_message_handler(output=output)
                # if _ssh_message_handler didn't raise any exception, we can raise the standard --
                # did you disable strict key message/exception
                msg = (
                    f"Failed to open connection to host {self.host}. Do you need to disable "
                    "`auth_strict_key`?"
                )
                self.logger.critical(msg)
                raise ScrapliAuthenticationFailed(msg)
            if self._comms_ansi:
                output = strip_ansi(output)
            if b"password" in output.lower():
                self.logger.info("Found password prompt, sending password")
                pty_session.write(self.auth_password.encode())
                pty_session.write(self._comms_return_char.encode())
                self.session_lock.release()
                break

    @operation_timeout("_timeout_ops", "Timed out determining if session is authenticated")
    def _pty_isauthenticated(self, pty_session: PtyProcess) -> bool:
        """
        Check if session is authenticated

        This is very naive -- it only knows if the sub process is alive and has not received an EOF.
        Beyond that we lock the session and send the return character and re-read the channel.

        Args:
            pty_session: PtyProcess session object

        Returns:
            bool: True if authenticated, else False

        Raises:
            N/A

        """
        self.logger.debug("Attempting to determine if PTY authentication was successful")
        if pty_session.isalive() and not pty_session.eof():
            prompt_pattern = get_prompt_pattern(prompt="", class_prompt=self._comms_prompt_pattern)
            self.session_lock.acquire()
            pty_session.write(self._comms_return_char.encode())
            while True:
                # almost all of the time we don't need a while loop here, but every once in a while
                # fd won't be ready which causes a failure without an obvious root cause,
                # loop/logging to hopefully help with that
                fd_ready, _, _ = select([pty_session.fd], [], [], 0)
                if pty_session.fd in fd_ready:
                    break
                self.logger.debug("PTY fd not ready yet...")
            output = b""
            while True:
                new_output = pty_session.read()
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
                if b"\x1B" in output:
                    output = strip_ansi(output=output)
                channel_match = re.search(pattern=prompt_pattern, string=output)
                if channel_match:
                    self.session_lock.release()
                    self._isauthenticated = True
                    return True
                if b"password:" in output.lower():
                    # if we see "password" we know auth failed (hopefully in all scenarios!)
                    self.logger.critical(
                        "Found `password:` in output, assuming password authentication failed"
                    )
                    return False
                if output:
                    self.logger.debug(
                        f"Cannot determine if authenticated, \n\tRead: {repr(output)}"
                    )
        self.session_lock.release()
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
        self.session_lock.acquire()
        if isinstance(self.session, Popen):
            self.session.kill()
            try:
                os.close(self._stdout_fd)
                os.close(self._stdin_fd)
            except OSError:
                # fds were never opened or were already closed
                pass
        elif isinstance(self.session, PtyProcess):
            # killing ptyprocess seems to make things hang open?
            self.session.terminated = True
        self.logger.debug(f"Channel to host {self.host} closed")
        self.session_lock.release()

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
        if isinstance(self.session, Popen):
            try:
                os.stat(self._stdout_fd)
                os.stat(self._stdin_fd)
                return True
            except OSError:
                return False
        elif isinstance(self.session, PtyProcess):
            if self.session.isalive() and self._isauthenticated and not self.session.eof():
                return True
        return False

    @requires_open_session()
    @operation_timeout("timeout_transport", "Timed out reading from transport")
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
        if isinstance(self.session, Popen):
            return os.read(self._stdout_fd, read_bytes)
        if isinstance(self.session, PtyProcess):
            return self.session.read(read_bytes)
        return b""

    @requires_open_session()
    @operation_timeout("timeout_transport", "Timed out writing to transport")
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
        if isinstance(self.session, Popen):
            os.write(self._stdin_fd, channel_input.encode())
        elif isinstance(self.session, PtyProcess):
            self.session.write(channel_input.encode())

    def set_timeout(self, timeout: Optional[int] = None) -> None:
        """
        Set session timeout

        Note that this modifies the objects `timeout_transport` value directly as this value is
        what controls the timeout decorator for read/write methods. This is slightly different
        behavior from ssh2/paramiko/telnet in that those transports modify the session value and
        leave the objects `timeout_transport` alone.

        Args:
            timeout: timeout in seconds

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        if isinstance(timeout, int):
            set_timeout = timeout
        else:
            set_timeout = self.timeout_transport
        self.timeout_transport = set_timeout

    def _keepalive_standard(self) -> None:
        """
        Send "out of band" (protocol level) keepalives to devices.

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            NotImplementedError: 'standard' keepalive mechanism not yet implemented for system

        """
        raise NotImplementedError("'standard' keepalive mechanism not yet implemented for system.")
