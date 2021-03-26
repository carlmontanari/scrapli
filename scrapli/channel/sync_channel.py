"""scrapli.channel.sync_channel"""
import re
import time
from contextlib import contextmanager
from datetime import datetime
from io import SEEK_END, BytesIO
from threading import Lock
from typing import Iterator, List, Optional, Tuple

from scrapli.channel.base_channel import BaseChannel, BaseChannelArgs
from scrapli.decorators import ChannelTimeout
from scrapli.exceptions import ScrapliAuthenticationFailed, ScrapliTimeout
from scrapli.transport.base import Transport


class Channel(BaseChannel):
    def __init__(
        self,
        transport: Transport,
        base_channel_args: BaseChannelArgs,
    ) -> None:
        super().__init__(
            transport=transport,
            base_channel_args=base_channel_args,
        )
        self.transport: Transport

        self.channel_lock: Optional[Lock] = None
        if self._base_channel_args.channel_lock:
            self.channel_lock = Lock()

    @contextmanager
    def _channel_lock(self) -> Iterator[None]:
        """
        Lock the channel during public channel operations if channel_lock is enabled

        Args:
            N/A

        Yields:
            None

        Raises:
            N/A

        """
        if self.channel_lock:
            with self.channel_lock:
                yield
        else:
            yield

    def read(self) -> bytes:
        """
        Read chunks of output from the channel

        Replaces any r"\r" characters that sometimes get stuffed into the output from the devices

        Args:
            N/A

        Returns:
            bytes: output read from channel

        Raises:
            N/A

        """
        buf = self.transport.read()
        buf = buf.replace(b"\r", b"")

        self.logger.debug(f"read: {repr(buf)}")

        if self.channel_log:
            self.channel_log.write(buf)

        if self._base_channel_args.comms_ansi:
            buf = self._strip_ansi(buf=buf)

        return buf

    def _read_until_input(self, channel_input: bytes) -> bytes:
        """
        Read until all channel_input has been read on the channel

        Args:
            channel_input: bytes that should have been written to the channel

        Returns:
            bytes: output read from channel while checking for the input in the channel stream

        Raises:
            N/A

        """
        buf = b""

        if not channel_input:
            return buf

        # squish all channel input words together and cast to lower to make comparison easier
        processed_channel_input = b"".join(channel_input.lower().split())

        while True:
            buf += self.read()

            # replace any backspace chars (particular problem w/ junos), and remove any added spaces
            # this is just for comparison of the inputs to what was read from channel
            if processed_channel_input in b"".join(buf.lower().replace(b"\x08", b"").split()):
                return buf

    def _read_until_prompt(self, buf: bytes = b"", prompt: str = "") -> bytes:
        """
        Read until expected prompt is seen

        Args:
            buf: output from previous reads if needed (used in scrapli netconf)
            prompt: prompt to look for if not looking for base prompt (comms_prompt_pattern)

        Returns:
            bytes: output read from channel

        Raises:
            N/A

        """
        search_pattern = self._get_prompt_pattern(
            class_pattern=self._base_channel_args.comms_prompt_pattern, pattern=prompt
        )

        read_buf = BytesIO(buf)

        while True:
            read_buf.write(self.read())

            read_buf.seek(-self._base_channel_args.comms_prompt_search_depth, SEEK_END)
            search_buf = read_buf.read()

            channel_match = re.search(
                pattern=search_pattern,
                string=search_buf,
            )

            if channel_match:
                return read_buf.getvalue()

    def _read_until_prompt_or_time(
        self,
        buf: bytes = b"",
        channel_outputs: Optional[List[bytes]] = None,
        read_duration: Optional[float] = None,
    ) -> bytes:
        """
        Read until expected prompt is seen, outputs are seen, or for duration, whichever comes first

        As transport reading may block, transport timeout is temporarily set to the read_duration
        and any `ScrapliTimeout` that is raised while reading is ignored.

        Args:
            buf: bytes from previous reads if needed
            channel_outputs: List of bytes to search for in channel output, if any are seen, return
                read output
            read_duration: duration to read from channel for

        Returns:
            bytes: output read from channel

        Raises:
            N/A

        """
        search_pattern = self._get_prompt_pattern(
            class_pattern=self._base_channel_args.comms_prompt_pattern,
        )

        if channel_outputs is None:
            channel_outputs = []
        if read_duration is None:
            read_duration = 2.5

        regex_channel_outputs_pattern = self._join_and_compile(channel_outputs=channel_outputs)

        _transport_args = self.transport._base_transport_args  # pylint: disable=W0212
        previous_timeout_transport = _transport_args.timeout_transport
        _transport_args.timeout_transport = int(read_duration)

        read_buf = BytesIO(buf)

        start = time.time()
        while True:
            try:
                read_buf.write(self.read())
            except ScrapliTimeout:
                pass

            read_buf.seek(-self._base_channel_args.comms_prompt_search_depth, SEEK_END)
            search_buf = read_buf.read()

            if (time.time() - start) > read_duration:
                break
            if any((channel_output in search_buf for channel_output in channel_outputs)):
                break
            if re.search(pattern=regex_channel_outputs_pattern, string=search_buf):
                break
            if re.search(pattern=search_pattern, string=search_buf):
                break

        _transport_args.timeout_transport = previous_timeout_transport

        return read_buf.getvalue()

    @ChannelTimeout(message="timed out during in channel ssh authentication")
    def channel_authenticate_ssh(
        self, auth_password: str, auth_private_key_passphrase: str
    ) -> None:
        """
        Handle SSH Authentication for transports that only operate "in the channel" (i.e. system)

        Args:
            auth_password: password to authenticate with
            auth_private_key_passphrase: passphrase for ssh key if necessary

        Returns:
            None

        Raises:
            ScrapliAuthenticationFailed: if password prompt seen more than twice
            ScrapliAuthenticationFailed: if passphrase prompt seen more than twice

        """
        self.logger.debug("attempting in channel ssh authentication")

        password_count = 0
        passphrase_count = 0
        authenticate_buf = b""

        search_pattern = self._get_prompt_pattern(
            class_pattern=self._base_channel_args.comms_prompt_pattern
        )

        with self._channel_lock():
            while True:
                buf = self.read()

                # if user sets comms_ansi *or* if we see an escape char, strip ansi... at least eos
                # tends to have one escape char in the login output that will break things; other
                # than this and telnet login, stripping ansi will only ever be governed by the users
                # comms_ansi setting
                if self._base_channel_args.comms_ansi or b"\x1b" in buf.lower():
                    buf = self._strip_ansi(buf=buf)

                authenticate_buf += buf.lower()

                self._ssh_message_handler(output=authenticate_buf)

                if b"password" in authenticate_buf:
                    # clear the authentication buffer so we don't re-read the password prompt
                    authenticate_buf = b""
                    password_count += 1
                    if password_count > 2:
                        msg = "password prompt seen more than once, assuming auth failed"
                        self.logger.critical(msg)
                        raise ScrapliAuthenticationFailed(msg)
                    self.write(channel_input=auth_password, redacted=True)
                    self.send_return()

                if b"enter passphrase for key" in authenticate_buf:
                    # clear the authentication buffer so we don't re-read the passphrase prompt
                    authenticate_buf = b""
                    passphrase_count += 1
                    if passphrase_count > 2:
                        msg = "passphrase prompt seen more than once, assuming auth failed"
                        self.logger.critical(msg)
                        raise ScrapliAuthenticationFailed(msg)
                    self.write(channel_input=auth_private_key_passphrase, redacted=True)
                    self.send_return()

                channel_match = re.search(
                    pattern=search_pattern,
                    string=authenticate_buf,
                )

                if channel_match:
                    return

    @ChannelTimeout(message="timed out during in channel telnet authentication")
    def channel_authenticate_telnet(self, auth_username: str = "", auth_password: str = "") -> None:
        """
        Handle Telnet Authentication

        Args:
            auth_username: username to use for telnet authentication
            auth_password: password to use for telnet authentication

        Returns:
            None

        Raises:
            ScrapliAuthenticationFailed: if password prompt seen more than twice
            ScrapliAuthenticationFailed: if login prompt seen more than twice

        """
        self.logger.debug("attempting in channel telnet authentication")

        username_count = 0
        password_count = 0
        authenticate_buf = b""

        # ignoring type here out of laziness mostly, telnet is kind of special and this should be
        # the only real one off type thing hopefully
        bytes_username_prompt = self.transport.username_prompt.encode()  # type: ignore
        bytes_password_prompt = self.transport.password_prompt.encode()  # type: ignore

        search_pattern = self._get_prompt_pattern(
            class_pattern=self._base_channel_args.comms_prompt_pattern
        )

        # capture the start time of the authentication event; we also set a "return_interval" which
        # is 1/10 the timout_ops value, we will send a return character at roughly this interval if
        # there is no output on the channel. we do this because sometimes telnet needs a kick to get
        # it to prompt for auth -- particularity when connecting to terminal server/console port
        auth_start_time = datetime.now().timestamp()
        return_interval = self._base_channel_args.timeout_ops / 10
        return_attempts = 1

        with self._channel_lock():
            while True:
                buf = self.read()

                # telnet auth *probably* wont have ansi chars, but strip them if they do exist so
                # we can at least get past auth
                if self._base_channel_args.comms_ansi or b"\x1B" in buf:
                    buf = self._strip_ansi(buf=buf)

                if not buf:
                    current_iteration_time = datetime.now().timestamp()
                    if (current_iteration_time - auth_start_time) > (
                        return_interval * return_attempts
                    ):
                        self.send_return()
                        return_attempts += 1

                authenticate_buf += buf.lower()

                if bytes_username_prompt in authenticate_buf:
                    # clear the authentication buffer so we don't re-read the username prompt
                    authenticate_buf = b""
                    username_count += 1
                    if username_count > 2:
                        msg = "username/login prompt seen more than once, assuming auth failed"
                        self.logger.critical(msg)
                        raise ScrapliAuthenticationFailed(msg)
                    self.write(channel_input=auth_username)
                    self.send_return()

                if bytes_password_prompt in authenticate_buf:
                    # clear the authentication buffer so we don't re-read the password prompt
                    authenticate_buf = b""
                    password_count += 1
                    if password_count > 2:
                        msg = "password prompt seen more than once, assuming auth failed"
                        self.logger.critical(msg)
                        raise ScrapliAuthenticationFailed(msg)
                    self.write(channel_input=auth_password, redacted=True)
                    self.send_return()

                channel_match = re.search(
                    pattern=search_pattern,
                    string=authenticate_buf,
                )

                if channel_match:
                    return

    @ChannelTimeout(message="timed out getting prompt")
    def get_prompt(self) -> str:
        """
        Get current channel prompt

        Args:
            N/A

        Returns:
            str: string of the current prompt

        Raises:
            N/A

        """
        buf = b""

        search_pattern = self._get_prompt_pattern(
            class_pattern=self._base_channel_args.comms_prompt_pattern
        )

        with self._channel_lock():
            self.send_return()

            while True:
                buf += self.read()

                channel_match = re.search(
                    pattern=search_pattern,
                    string=buf,
                )

                if channel_match:
                    current_prompt = channel_match.group(0)
                    return current_prompt.decode().strip()

    @ChannelTimeout(message="timed out sending input to device")
    def send_input(
        self,
        channel_input: str,
        *,
        strip_prompt: bool = True,
        eager: bool = False,
    ) -> Tuple[bytes, bytes]:
        """
        Primary entry point to send data to devices in shell mode; accept input and returns result

        Args:
            channel_input: string input to send to channel
            strip_prompt: strip prompt or not, defaults to True (yes, strip the prompt)
            eager: eager mode reads and returns the `_read_until_input` value, but does not attempt
                to read to the prompt pattern -- this should not be used manually! (only used by
                `send_configs` with the eager flag set)

        Returns:
            Tuple[bytes, bytes]: tuple of "raw" output and "processed" (cleaned up/stripped) output

        Raises:
            N/A

        """
        self._pre_send_input(channel_input=channel_input)

        buf = b""
        bytes_channel_input = channel_input.encode()

        self.logger.info(
            f"sending channel input: {channel_input}; strip_prompt: {strip_prompt}; eager: {eager}"
        )

        with self._channel_lock():
            self.write(channel_input=channel_input)
            _buf_until_input = self._read_until_input(channel_input=bytes_channel_input)
            self.send_return()

            if not eager:
                buf += self._read_until_prompt()

        processed_buf = self._process_output(
            buf=buf,
            strip_prompt=strip_prompt,
        )
        return buf, processed_buf

    @ChannelTimeout(message="timed out sending input to device")
    def send_input_and_read(
        self,
        channel_input: str,
        *,
        strip_prompt: bool = True,
        expected_outputs: Optional[List[str]] = None,
        read_duration: Optional[float] = None,
    ) -> Tuple[bytes, bytes]:
        """
        Send a command and read until expected prompt is seen, outputs are seen, or for duration

        Args:
            channel_input: string input to send to channel
            strip_prompt: strip prompt or not, defaults to True (yes, strip the prompt)
            expected_outputs: list of strings to look for in output; if any of these are seen,
                return output read up till that read
            read_duration: float duration to read for

        Returns:
            Tuple[bytes, bytes]: tuple of "raw" output and "processed" (cleaned up/stripped) output

        Raises:
            N/A

        """
        self._pre_send_input(channel_input=channel_input)

        buf = b""
        bytes_channel_input = channel_input.encode()
        bytes_channel_outputs = [
            channel_output.encode() for channel_output in expected_outputs or []
        ]

        self.logger.info(
            f"sending channel input and read: {channel_input}; strip_prompt: {strip_prompt}; "
            f"expected_outputs: {expected_outputs}; read_duration: {read_duration}"
        )

        with self._channel_lock():
            self.write(channel_input=channel_input)
            _buf_until_input = self._read_until_input(channel_input=bytes_channel_input)
            self.send_return()

            buf += self._read_until_prompt_or_time(
                channel_outputs=bytes_channel_outputs, read_duration=read_duration
            )

        processed_buf = self._process_output(
            buf=buf,
            strip_prompt=strip_prompt,
        )

        return buf, processed_buf

    @ChannelTimeout(message="timed out sending interactive input to device")
    def send_inputs_interact(
        self, interact_events: List[Tuple[str, str, Optional[bool]]]
    ) -> Tuple[bytes, bytes]:
        """
        Interact with a device with changing prompts per input.

        Used to interact with devices where prompts change per input, and where inputs may be hidden
        such as in the case of a password input. This can be used to respond to challenges from
        devices such as the confirmation for the command "clear logging" on IOSXE devices for
        example. You may have as many elements in the "interact_events" list as needed, and each
        element of that list should be a tuple of two or three elements. The first element is always
        the input to send as a string, the second should be the expected response as a string, and
        the optional third a bool for whether or not the input is "hidden" (i.e. password input)

        An example where we need this sort of capability:

        '''
        3560CX#copy flash: scp:
        Source filename []? test1.txt
        Address or name of remote host []? 172.31.254.100
        Destination username [carl]?
        Writing test1.txt
        Password:

        Password:
         Sink: C0644 639 test1.txt
        !
        639 bytes copied in 12.066 secs (53 bytes/sec)
        3560CX#
        '''

        To accomplish this we can use the following:

        '''
        interact = conn.channel.send_inputs_interact(
            [
                ("copy flash: scp:", "Source filename []?", False),
                ("test1.txt", "Address or name of remote host []?", False),
                ("172.31.254.100", "Destination username [carl]?", False),
                ("carl", "Password:", False),
                ("super_secure_password", prompt, True),
            ]
        )
        '''

        If we needed to deal with more prompts we could simply continue adding tuples to the list of
        interact "events".

        Args:
            interact_events: list of tuples containing the "interactions" with the device
                each list element must have an input and an expected response, and may have an
                optional bool for the third and final element -- the optional bool specifies if the
                input that is sent to the device is "hidden" (ex: password), if the hidden param is
                not provided it is assumed the input is "normal" (not hidden)

        Returns:
            Tuple[bytes, bytes]: output read from the channel with no whitespace trimming/cleaning,
                and the output read from the channel that has been "cleaned up"

        Raises:
            N/A

        """
        self._pre_send_inputs_interact(interact_events=interact_events)

        buf = b""
        processed_buf = b""

        with self._channel_lock():
            for interact_event in interact_events:
                channel_input = interact_event[0]
                bytes_channel_input = channel_input.encode()
                channel_response = interact_event[1]
                try:
                    hidden_input = interact_event[2]
                except IndexError:
                    hidden_input = False

                _channel_input = channel_input if not hidden_input else "REDACTED"
                self.logger.info(
                    f"sending interactive input: {_channel_input}; "
                    f"expecting: {channel_response}; "
                    f"hidden_input: {hidden_input}"
                )

                self.write(channel_input=channel_input, redacted=bool(hidden_input))
                if not channel_response or hidden_input is True:
                    self.send_return()
                else:
                    buf += self._read_until_input(channel_input=bytes_channel_input)
                    self.send_return()
                buf += self._read_until_prompt(prompt=channel_response)

        processed_buf += self._process_output(
            buf=buf,
            strip_prompt=False,
        )

        return buf, processed_buf
