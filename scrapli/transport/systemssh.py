"""scrapli.transport.systemssh"""
import os
import pty
import re
from logging import getLogger
from select import select
from subprocess import PIPE, Popen
from typing import TYPE_CHECKING, Optional, Union

from scrapli.decorators import operation_timeout
from scrapli.exceptions import ScrapliAuthenticationFailed, ScrapliTimeout
from scrapli.helper import get_prompt_pattern, strip_ansi
from scrapli.ssh_config import SSHConfig
from scrapli.transport.ptyprocess import PtyProcess
from scrapli.transport.transport import Transport

if TYPE_CHECKING:
    PopenBytes = Popen[bytes]  # pylint: disable=E1136

LOG = getLogger("transport")

SYSTEM_SSH_TRANSPORT_ARGS = (
    "auth_username",
    "auth_private_key",
    "auth_password",
    "auth_strict_key",
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
    ) -> None:
        """
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

        self._timeout_ops: int = timeout_ops
        self._comms_prompt_pattern: str = comms_prompt_pattern
        self._comms_return_char: str = comms_return_char
        self._comms_ansi: bool = comms_ansi
        self._process_ssh_config(ssh_config_file)
        self.ssh_known_hosts_file: str = ssh_known_hosts_file

        self.session: Union[Popen[bytes], PtyProcess]  # pylint: disable=E1136
        self.lib_auth_exception = ScrapliAuthenticationFailed
        self._isauthenticated = False

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
        ssh = SSHConfig(ssh_config_file)
        self.ssh_config_file = ssh.ssh_config_file
        host_config = ssh.lookup(self.host)
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

        # If authenticating with private key prefer to use open pipes
        # _open_pipes uses subprocess Popen which is preferable to opening a pty
        # if _open_pipes fails and no password available, raise failure, otherwise try password auth
        if self.auth_private_key:
            open_pipes_result = self._open_pipes()
            if open_pipes_result:
                return
            if not self.auth_password or not self.auth_username:
                msg = (
                    f"Public key authentication to host {self.host} failed. Missing username or"
                    " password unable to attempt password authentication."
                )
                LOG.critical(msg)
                raise ScrapliAuthenticationFailed(msg)

        # If public key auth fails or is not configured, open a pty session
        if not self._open_pty():
            msg = f"Authentication to host {self.host} failed"
            LOG.critical(msg)
            raise ScrapliAuthenticationFailed(msg)

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
        # copy the open_cmd as we don't want to update the objects open_cmd until we know we can
        # authenticate. add verbose output and disable batch mode (disables passphrase/password
        # queries). If auth is successful update the object open_cmd to represent what was used
        open_cmd = self.open_cmd.copy()
        open_cmd.append("-v")
        open_cmd.extend(["-o", "BatchMode=yes"])

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
        LOG.debug(f"Session to host {self.host} spawned")

        try:
            self._pipes_isauthenticated(self.session)
        except TimeoutError:
            # If auth fails, kill the popen session, also need to manually close the stderr pipe
            # for some reason... unclear why, but w/out this it will hang open
            if self.session.stderr is not None:
                stderr_fd = self.session.stderr.fileno()
                os.close(stderr_fd)
            self.session.kill()
            return False

        LOG.debug(f"Authenticated to host {self.host} with public key")

        # set stdin/stdout to the new master pty fds
        self._stdin_fd = stdin_master_pty
        self._stdout_fd = stdout_master_pty

        self.open_cmd = open_cmd
        self.session_lock.release()
        return True

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
            ScrapliTimeout: if `Operation timed out` in stderr output

        """
        if pipes_session.stderr is None:
            raise ScrapliTimeout(f"Could not read stderr while connecting to host {self.host}")

        output = b""
        while True:
            output += pipes_session.stderr.read(65535)
            if f"Authenticated to {self.host}".encode() in output:
                self._isauthenticated = True
                return True
            if "Operation timed out".encode() in output:
                raise ScrapliTimeout(f"Timed opening connection to host {self.host}")

    def _open_pty(self) -> bool:
        """
        Private method to open session with PtyProcess

        Args:
            N/A

        Returns:
            bool: True/False session was opened and authenticated

        Raises:
            N/A

        """
        self.session = PtyProcess.spawn(self.open_cmd)
        LOG.debug(f"Session to host {self.host} spawned")
        self.session_lock.release()
        self._pty_authenticate(self.session)
        if not self._pty_isauthenticated(self.session):
            return False
        LOG.debug(f"Authenticated to host {self.host} with password")
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
            ScrapliAuthenticationFailed: if we receive an EOFError -- this usually indicates that
                host key checking is enabled and failed.

        """
        self.session_lock.acquire()
        output = b""
        while True:
            try:
                output += pty_session.read()
            except EOFError:
                raise ScrapliAuthenticationFailed(f"Failed to open connection to host {self.host}")
            if self._comms_ansi:
                output = strip_ansi(output)
            if b"password" in output.lower():
                LOG.debug("Found password prompt, sending password")
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
        LOG.debug("Attempting to determine if PTY authentication was successful")
        if pty_session.isalive() and not pty_session.eof():
            prompt_pattern = get_prompt_pattern("", self._comms_prompt_pattern)
            self.session_lock.acquire()
            pty_session.write(self._comms_return_char.encode())
            fd_ready, _, _ = select([pty_session.fd], [], [], 0)
            if pty_session.fd in fd_ready:
                output = b""
                while True:
                    new_output = pty_session.read()
                    output += new_output
                    # we do not need to deal w/ line replacement for the actual output, only for
                    # parsing if a prompt-like thing is at the end of the output
                    output = re.sub(b"\r", b"", output)
                    if self._comms_ansi:
                        output = strip_ansi(output)
                    channel_match = re.search(prompt_pattern, output)
                    if channel_match:
                        self.session_lock.release()
                        self._isauthenticated = True
                        return True
                    if b"password" in new_output.lower():
                        # if we see "password" we know auth failed (hopefully in all scenarios!)
                        return False
                    if new_output:
                        LOG.debug(
                            f"Cannot determine if authenticated, \n\tRead: {repr(new_output)}"
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
        elif isinstance(self.session, PtyProcess):
            self.session.kill(1)
        LOG.debug(f"Channel to host {self.host} closed")
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
            if self.session.poll() is None and self._isauthenticated:
                return True
        elif isinstance(self.session, PtyProcess):
            if self.session.isalive() and self._isauthenticated and not self.session.eof():
                return True
        return False

    @operation_timeout("timeout_transport", "Transport timeout during read operation.")
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

    @operation_timeout("timeout_transport", "Transport timeout during write operation.")
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
            NotImplementedError: always, because this is not implemented for telnet

        """
        raise NotImplementedError("No 'standard' keepalive mechanism for telnet.")
