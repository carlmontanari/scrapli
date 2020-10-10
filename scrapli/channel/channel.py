"""scrapli.channel.channel"""
import re
import time
from typing import Any, List, Optional, Tuple

from scrapli.channel.base_channel import ChannelBase
from scrapli.decorators import OperationTimeout
from scrapli.exceptions import ScrapliTimeout
from scrapli.helper import get_prompt_pattern, strip_ansi
from scrapli.transport.transport import Transport


class Channel(ChannelBase):
    def __init__(self, transport: Transport, **kwargs: Any) -> None:
        """
        Channel Object

        Args:
            transport: Scrapli Transport class
            kwargs: keyword arguments to pass to ChannelBase

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        super().__init__(transport, **kwargs)

        # ChannelBase supports union of Transport and AsyncTransport, but as this is the
        # "normal" (sync) Channel, transport will always be async
        self.transport: Transport

    def _read_chunk(self) -> bytes:
        """
        Private method to read chunk from channel

        Args:
            N/A

        Returns:
            bytes: output read from channel

        Raises:
            N/A

        """
        new_output = self.transport.read()
        new_output = new_output.replace(b"\r", b"")
        self.logger.debug(f"Read: {repr(new_output)}")
        return new_output

    def _read_until_input(self, channel_input: bytes, auto_expand: Optional[bool] = None) -> bytes:
        """
        Read until all input has been entered.

        Args:
            channel_input: bytes to write to channel
            auto_expand: bool to indicate if a device auto-expands commands, for example juniper
                devices without `cli complete-on-space` disabled will convert `config` to
                `configuration` after entering a space character after `config`; because scrapli
                reads the channel until each command is entered, the command changing from `config`
                to `configuration` will cause scrapli (by default) to never think the command has
                been entered.

        Returns:
            bytes: output read from channel

        Raises:
            N/A

        """
        output = b""

        if not channel_input:
            self.logger.info(f"Read: {repr(output)}")
            return output

        if auto_expand is None:
            auto_expand = self.comms_auto_expand

        # squish all channel input words together and cast to lower to make comparison easier
        processed_channel_input = b"".join(channel_input.lower().split())

        while True:
            output += self._read_chunk()

            # replace any backspace chars (particular problem w/ junos), and remove any added spaces
            # this is just for comparison of the inputs to what was read from channel
            if not auto_expand and processed_channel_input in b"".join(
                output.lower().replace(b"\x08", b"").split()
            ):
                break
            if auto_expand and self._process_auto_expand(
                output=output, channel_input=channel_input
            ):
                break

        self.logger.info(f"Read: {repr(output)}")
        return output

    def _read_until_prompt(self, output: bytes = b"", prompt: str = "") -> bytes:
        """
        Read until expected prompt is seen.

        Args:
            output: bytes from previous reads if needed
            prompt: prompt to look for if not looking for base prompt (self.comms_prompt_pattern)

        Returns:
            bytes: output read from channel

        Raises:
            N/A

        """
        prompt_pattern = get_prompt_pattern(prompt=prompt, class_prompt=self.comms_prompt_pattern)

        while True:
            output += self._read_chunk()
            if self.comms_ansi:
                output = strip_ansi(output=output)
            channel_match = re.search(pattern=prompt_pattern, string=output)
            if channel_match:
                self.logger.info(f"Read: {repr(output)}")
                return output

    def _read_until_prompt_or_time(
        self,
        output: bytes = b"",
        channel_outputs: Optional[List[bytes]] = None,
        read_duration: Optional[float] = None,
    ) -> bytes:
        """
        Read until expected prompt is seen, outputs are seen, or for duration, whichever comes first

        As transport reading may block, transport timeout is temporarily set to the read_duration
        and any `ScrapliTimeout` that is raised while reading is ignored.

        Args:
            output: bytes from previous reads if needed
            channel_outputs: List of bytes to search for in channel output, if any are seen, return
                read output
            read_duration: duration to read from channel for

        Returns:
            bytes: output read from channel

        Raises:
            N/A

        """
        prompt_pattern = get_prompt_pattern(prompt="", class_prompt=self.comms_prompt_pattern)

        if channel_outputs is None:
            channel_outputs = []
        if read_duration is None:
            read_duration = 2.5

        previous_timeout_transport = self.transport.timeout_transport
        self.transport.timeout_transport = int(read_duration)

        start = time.time()
        while True:
            try:
                output += self._read_chunk()
            except ScrapliTimeout:
                pass

            if self.comms_ansi:
                output = strip_ansi(output=output)

            if (time.time() - start) > read_duration:
                break
            if any([channel_output in output for channel_output in channel_outputs]):
                break
            if re.search(pattern=prompt_pattern, string=output):
                break

        self.transport.timeout_transport = previous_timeout_transport

        self.logger.info(f"Read: {repr(output)}")
        return output

    @OperationTimeout(attribute="timeout_ops", message="Timed out determining prompt on device.")
    def get_prompt(self) -> str:
        """
        Get current channel prompt

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        prompt_pattern = get_prompt_pattern(prompt="", class_prompt=self.comms_prompt_pattern)
        self._send_return()
        output = b""
        while True:
            output += self._read_chunk()
            if self.comms_ansi:
                output = strip_ansi(output=output)
            channel_match = re.search(pattern=prompt_pattern, string=output)
            if channel_match:
                current_prompt = channel_match.group(0)
                return current_prompt.decode().strip()

    @OperationTimeout(attribute="timeout_ops", message="Timed out sending input to device.")
    def send_input(
        self, channel_input: str, strip_prompt: bool = True, eager: bool = False
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
            raw_result: output read from the channel with no whitespace trimming/cleaning
            processed_result: output read from the channel that has been cleaned up

        Raises:
            N/A

        """
        self._pre_send_input(channel_input=channel_input)

        bytes_channel_input = channel_input.encode()

        with self.session_lock:
            self.logger.info(
                f"Attempting to send input: {channel_input}; strip_prompt: {strip_prompt}"
            )
            self.transport.write(channel_input=channel_input)
            self.logger.debug(f"Write: {repr(channel_input)}")
            output = self._read_until_input(channel_input=bytes_channel_input)
            self._send_return()
            if not eager:
                output = self._read_until_prompt()
        processed_output = self._restructure_output(output=output, strip_prompt=strip_prompt)

        return output, processed_output

    @OperationTimeout(attribute="timeout_ops", message="Timed out sending and reading to device.")
    def send_input_and_read(
        self,
        channel_input: str,
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
            raw_result: output read from the channel with no whitespace trimming/cleaning
            processed_result: output read from the channel that has been cleaned up

        Raises:
            N/A

        """
        self._pre_send_input(channel_input=channel_input)

        bytes_channel_input = channel_input.encode()
        bytes_channel_outputs = [
            channel_output.encode() for channel_output in expected_outputs or []
        ]

        with self.session_lock:
            self.transport.write(channel_input=channel_input)
            self.logger.debug(f"Write: {repr(channel_input)}")
            self._read_until_input(channel_input=bytes_channel_input)
            self._send_return()
            output = self._read_until_prompt_or_time(
                channel_outputs=bytes_channel_outputs, read_duration=read_duration
            )
        processed_output = self._restructure_output(output=output, strip_prompt=strip_prompt)
        return output, processed_output

    @OperationTimeout(
        attribute="timeout_ops", message="Timed out sending interactive input to device."
    )
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

        ```
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
        ```

        To accomplish this we can use the following:

        ```
        interact = conn.channel.send_inputs_interact(
            [
                ("copy flash: scp:", "Source filename []?", False),
                ("test1.txt", "Address or name of remote host []?", False),
                ("172.31.254.100", "Destination username [carl]?", False),
                ("carl", "Password:", False),
                ("super_secure_password", prompt, True),
            ]
        )
        ```

        If we needed to deal with more prompts we could simply continue adding tuples to the list of
        interact "events".

        Args:
            interact_events: list of tuples containing the "interactions" with the device
                each list element must have an input and an expected response, and may have an
                optional bool for the third and final element -- the optional bool specifies if the
                input that is sent to the device is "hidden" (ex: password), if the hidden param is
                not provided it is assumed the input is "normal" (not hidden)

        Returns:
            raw_result: output read from the channel with no whitespace trimming/cleaning
            processed_result: output read from the channel that has been cleaned up

        Raises:
            N/A

        """
        self._pre_send_inputs_interact(interact_events=interact_events)

        output = b""
        with self.session_lock:
            for interact_event in interact_events:
                channel_input = interact_event[0]
                bytes_channel_input = channel_input.encode()
                channel_response = interact_event[1]
                try:
                    hidden_input = interact_event[2]
                except IndexError:
                    hidden_input = False
                self.logger.info(
                    f"Attempting to send input interact: {channel_input}; "
                    f"\texpecting: {channel_response};"
                    f"\thidden_input: {hidden_input}"
                )
                self.transport.write(channel_input=channel_input)
                self.logger.debug(f"Write: {repr(channel_input)}")
                if not channel_response or hidden_input is True:
                    self._send_return()
                else:
                    output += self._read_until_input(channel_input=bytes_channel_input)
                    self._send_return()
                output += self._read_until_prompt(prompt=channel_response)

        return self._post_send_inputs_interact(output=output)
