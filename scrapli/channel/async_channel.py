"""scrapli.channel.async_channel"""

import asyncio
import re
import time
from contextlib import asynccontextmanager, suppress
from datetime import datetime
from io import BytesIO
from typing import AsyncIterator, List, Optional, Tuple

from scrapli.channel.base_channel import BaseChannel, BaseChannelArgs
from scrapli.decorators import timeout_wrapper
from scrapli.exceptions import ScrapliAuthenticationFailed, ScrapliTimeout
from scrapli.helper import output_roughly_contains_input
from scrapli.transport.base import AsyncTransport


class AsyncChannel(BaseChannel):
    def __init__(
        self,
        transport: AsyncTransport,
        base_channel_args: BaseChannelArgs,
    ) -> None:
        super().__init__(
            transport=transport,
            base_channel_args=base_channel_args,
        )
        self.transport: AsyncTransport

        self.channel_lock: Optional[asyncio.Lock] = None
        if self._base_channel_args.channel_lock:
            self.channel_lock = asyncio.Lock()

    @asynccontextmanager
    async def _channel_lock(self) -> AsyncIterator[None]:
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
            async with self.channel_lock:
                yield
        else:
            yield

    async def read(self) -> bytes:
        r"""
        Read chunks of output from the channel

        Replaces any \r characters that sometimes get stuffed into the output from the devices

        Args:
            N/A

        Returns:
            bytes: output read from channel

        Raises:
            N/A

        """
        buf = await self.transport.read()
        buf = buf.replace(b"\r", b"")

        self.logger.debug("read: %r", buf)

        if self.channel_log:
            self.channel_log.write(buf)

        if b"\x1b" in buf.lower():
            buf = self._strip_ansi(buf=buf)

        return buf

    async def _read_until_input(self, channel_input: bytes) -> bytes:
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
            buf += await self.read()

            if not self._base_channel_args.comms_roughly_match_inputs:
                # replace any backspace chars (particular problem w/ junos), and remove any added
                # spaces this is just for comparison of the inputs to what was read from channel
                # note (2024) this would be worked around by using the roughly contains search,
                # *but* that is slower (probably immaterially for most people but... ya know...)
                processed_buf = b"".join(buf.lower().replace(b"\x08", b"").split())

                if processed_channel_input in processed_buf:
                    return buf
            elif output_roughly_contains_input(input_=processed_channel_input, output=buf):
                return buf

    async def _read_until_prompt(self, buf: bytes = b"") -> bytes:
        """
        Read until expected prompt is seen.

        This reads until the "normal" `_base_channel_args.comms_prompt_pattern` is seen. The
        `_read_until_explicit_prompt` method can be used to read until some pattern in an arbitrary
        list of patterns is seen.

        Args:
            buf: output from previous reads if needed (used by scrapli netconf)

        Returns:
            bytes: output read from channel

        Raises:
            N/A

        """
        search_pattern = self._get_prompt_pattern(
            class_pattern=self._base_channel_args.comms_prompt_pattern
        )

        read_buf = BytesIO(buf)

        while True:
            b = await self.read()
            read_buf.write(b)

            search_buf = self._process_read_buf(read_buf=read_buf)

            channel_match = re.search(
                pattern=search_pattern,
                string=search_buf,
            )

            if channel_match:
                return read_buf.getvalue()

    async def _read_until_explicit_prompt(self, prompts: List[str]) -> bytes:
        """
        Read until expected prompt is seen.

        This method is for *explicit* prompt patterns instead of the "standard" prompt patterns
        contained in the `_base_channel_args.comms_prompt_pattern` attribute. Generally this is
        only used for `send_interactive` though it could be used elsewhere as well.

        Args:
            prompts: list of prompt patterns to look for, will return upon seeing any match

        Returns:
            bytes: output read from channel

        Raises:
            N/A

        """
        search_patterns = [
            self._get_prompt_pattern(
                class_pattern=self._base_channel_args.comms_prompt_pattern, pattern=prompt
            )
            for prompt in prompts
        ]

        read_buf = BytesIO(b"")

        while True:
            b = await self.read()
            read_buf.write(b)

            search_buf = self._process_read_buf(read_buf=read_buf)

            for search_pattern in search_patterns:
                channel_match = re.search(
                    pattern=search_pattern,
                    string=search_buf,
                )

                if channel_match:
                    return read_buf.getvalue()

    async def _read_until_prompt_or_time(
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
            with suppress(ScrapliTimeout):
                b = await self.read()
                read_buf.write(b)

            search_buf = self._process_read_buf(read_buf=read_buf)

            if (time.time() - start) > read_duration:
                break
            if any(channel_output in search_buf for channel_output in channel_outputs):
                break
            if re.search(pattern=regex_channel_outputs_pattern, string=search_buf):
                break
            if re.search(pattern=search_pattern, string=search_buf):
                break

        _transport_args.timeout_transport = previous_timeout_transport

        return read_buf.getvalue()

    @timeout_wrapper
    async def channel_authenticate_ssh(
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

        (
            password_pattern,
            passphrase_pattern,
            prompt_pattern,
        ) = self._pre_channel_authenticate_ssh()

        async with self._channel_lock():
            while True:
                try:
                    buf = await asyncio.wait_for(self.read(), timeout=1)
                except asyncio.TimeoutError:
                    buf = b""
                authenticate_buf += buf.lower()

                if re.search(
                    pattern=password_pattern,
                    string=authenticate_buf,
                ):
                    # clear the authentication buffer so we don't re-read the password prompt
                    authenticate_buf = b""
                    password_count += 1
                    if password_count > 2:
                        msg = "password prompt seen more than once, assuming auth failed"
                        self.logger.critical(msg)
                        raise ScrapliAuthenticationFailed(msg)
                    self.write(channel_input=auth_password, redacted=True)
                    self.send_return()

                if re.search(
                    pattern=passphrase_pattern,
                    string=authenticate_buf,
                ):
                    # clear the authentication buffer so we don't re-read the passphrase prompt
                    authenticate_buf = b""
                    passphrase_count += 1
                    if passphrase_count > 2:
                        msg = "passphrase prompt seen more than once, assuming auth failed"
                        self.logger.critical(msg)
                        raise ScrapliAuthenticationFailed(msg)
                    self.write(channel_input=auth_private_key_passphrase, redacted=True)
                    self.send_return()

                if re.search(
                    pattern=prompt_pattern,
                    string=authenticate_buf,
                ):
                    return

    @timeout_wrapper
    async def channel_authenticate_telnet(  # noqa: C901
        self, auth_username: str = "", auth_password: str = ""
    ) -> None:
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

        (
            username_pattern,
            password_pattern,
            prompt_pattern,
            auth_start_time,
            return_interval,
        ) = self._pre_channel_authenticate_telnet()

        read_interval = self._base_channel_args.timeout_ops / 20
        return_attempts = 1

        async with self._channel_lock():
            while True:
                try:
                    buf = await asyncio.wait_for(self.read(), timeout=read_interval)
                except asyncio.TimeoutError:
                    buf = b""

                if not buf:
                    current_iteration_time = datetime.now().timestamp()
                    if (current_iteration_time - auth_start_time) > (
                        return_interval * return_attempts
                    ):
                        self.send_return()
                        return_attempts += 1

                authenticate_buf += buf.lower()

                if re.search(
                    pattern=username_pattern,
                    string=authenticate_buf,
                ):
                    # clear the authentication buffer so we don't re-read the username prompt
                    authenticate_buf = b""
                    username_count += 1
                    if username_count > 2:
                        msg = "username/login prompt seen more than once, assuming auth failed"
                        self.logger.critical(msg)
                        raise ScrapliAuthenticationFailed(msg)
                    self.write(channel_input=auth_username)
                    self.send_return()

                if re.search(
                    pattern=password_pattern,
                    string=authenticate_buf,
                ):
                    # clear the authentication buffer so we don't re-read the password prompt
                    authenticate_buf = b""
                    password_count += 1
                    if password_count > 2:
                        msg = "password prompt seen more than once, assuming auth failed"
                        self.logger.critical(msg)
                        raise ScrapliAuthenticationFailed(msg)
                    self.write(channel_input=auth_password, redacted=True)
                    self.send_return()

                if re.search(
                    pattern=prompt_pattern,
                    string=authenticate_buf,
                ):
                    return

    @timeout_wrapper
    async def get_prompt(self) -> str:
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

        async with self._channel_lock():
            self.send_return()

            while True:
                buf += await self.read()

                channel_match = re.search(
                    pattern=search_pattern,
                    string=buf,
                )

                if channel_match:
                    current_prompt = channel_match.group(0)
                    return current_prompt.decode().strip()

    @timeout_wrapper
    async def send_input(
        self,
        channel_input: str,
        *,
        strip_prompt: bool = True,
        eager: bool = False,
        eager_input: bool = False,
    ) -> Tuple[bytes, bytes]:
        """
        Primary entry point to send data to devices in shell mode; accept input and returns result

        Args:
            channel_input: string input to send to channel
            strip_prompt: strip prompt or not, defaults to True (yes, strip the prompt)
            eager: eager mode reads and returns the `_read_until_input` value, but does not attempt
                to read to the prompt pattern -- this should not be used manually! (only used by
                `send_configs` with the eager flag set)
            eager_input: when true does *not* try to read our input off the channel -- generally
                this should be left alone unless you know what you are doing!

        Returns:
            Tuple[bytes, bytes]: tuple of "raw" output and "processed" (cleaned up/stripped) output

        Raises:
            N/A

        """
        self._pre_send_input(channel_input=channel_input)

        buf = b""
        bytes_channel_input = channel_input.encode()

        self.logger.info(
            "sending channel input: %s; strip_prompt: %s; eager: %s",
            channel_input,
            strip_prompt,
            eager,
        )

        async with self._channel_lock():
            self.write(channel_input=channel_input)

            if not eager_input:
                _buf_until_input = await self._read_until_input(channel_input=bytes_channel_input)

            self.send_return()

            if not eager:
                buf += await self._read_until_prompt()

        processed_buf = self._process_output(
            buf=buf,
            strip_prompt=strip_prompt,
        )
        return buf, processed_buf

    @timeout_wrapper
    async def send_input_and_read(
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
            "sending channel input and read: %s; strip_prompt: %s; "
            "expected_outputs: %s; read_duration: %s",
            channel_input,
            strip_prompt,
            expected_outputs,
            read_duration,
        )

        async with self._channel_lock():
            self.write(channel_input=channel_input)
            _buf_until_input = await self._read_until_input(channel_input=bytes_channel_input)
            self.send_return()

            buf += await self._read_until_prompt_or_time(
                channel_outputs=bytes_channel_outputs, read_duration=read_duration
            )

        processed_buf = self._process_output(
            buf=buf,
            strip_prompt=strip_prompt,
        )

        return buf, processed_buf

    @timeout_wrapper
    async def send_inputs_interact(
        self,
        interact_events: List[Tuple[str, str, Optional[bool]]],
        *,
        interaction_complete_patterns: Optional[List[str]] = None,
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
            interaction_complete_patterns: list of patterns, that if seen, indicate the interactive
                "session" has ended and we should exit the interactive session.

        Returns:
            Tuple[bytes, bytes]: output read from the channel with no whitespace trimming/cleaning,
                and the output read from the channel that has been "cleaned up"

        Raises:
            N/A

        """
        self._pre_send_inputs_interact(interact_events=interact_events)

        buf = b""
        processed_buf = b""

        async with self._channel_lock():
            for interact_event in interact_events:
                channel_input = interact_event[0]
                bytes_channel_input = channel_input.encode()
                channel_response = interact_event[1]
                prompts = [channel_response]

                if interaction_complete_patterns is not None:
                    prompts.extend(interaction_complete_patterns)

                try:
                    hidden_input = interact_event[2]
                except IndexError:
                    hidden_input = False

                _channel_input = channel_input if not hidden_input else "REDACTED"
                self.logger.info(
                    "sending interactive input: %s; expecting: %s; hidden_input: %s",
                    _channel_input,
                    channel_response,
                    hidden_input,
                )

                self.write(channel_input=channel_input, redacted=bool(hidden_input))
                if channel_response and hidden_input is not True:
                    buf += await self._read_until_input(channel_input=bytes_channel_input)
                self.send_return()
                buf += await self._read_until_explicit_prompt(prompts=prompts)

        processed_buf += self._process_output(
            buf=buf,
            strip_prompt=False,
        )

        return buf, processed_buf
