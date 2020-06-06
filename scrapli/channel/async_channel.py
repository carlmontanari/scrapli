"""scrapli.channel.async_channel"""
import re
from typing import Any, List, Optional, Tuple

from scrapli.channel.base_channel import ChannelBase
from scrapli.decorators import operation_timeout
from scrapli.helper import get_prompt_pattern, strip_ansi
from scrapli.transport.async_transport import AsyncTransport


class AsyncChannel(ChannelBase):
    def __init__(self, transport: AsyncTransport, **kwargs: Any) -> None:
        """
        AsyncChannel Object

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
        # AsyncChannel, transport will always be async
        self.transport: AsyncTransport

    async def _read_chunk(self) -> bytes:
        """
        Private method to async read chunk

        Args:
            N/A

        Returns:
            bytes: output read from channel

        Raises:
            N/A

        """
        new_output = await self.transport.read()
        new_output = new_output.replace(b"\r", b"")
        self.logger.debug(f"Read: {repr(new_output)}")
        return new_output

    async def _read_until_input(
        self, channel_input: bytes, auto_expand: Optional[bool] = None
    ) -> bytes:
        """
        Async read until all input has been entered.

        Args:
            channel_input: string to write to channel
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

        while True:
            output += await self._read_chunk()
            if not auto_expand and channel_input in output:
                break
            if auto_expand and self._process_auto_expand(
                output=output, channel_input=channel_input
            ):
                break

        self.logger.info(f"Read: {repr(output)}")
        return output

    async def _read_until_prompt(self, output: bytes = b"", prompt: str = "") -> bytes:
        """
        Async read until expected prompt is seen.

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
            output += await self._read_chunk()
            if self.comms_ansi:
                output = strip_ansi(output=output)
            channel_match = re.search(pattern=prompt_pattern, string=output)
            if channel_match:
                self.logger.info(f"Read: {repr(output)}")
                return output

    @operation_timeout("timeout_ops", "Timed out determining prompt on device.")
    async def get_prompt(self) -> str:
        """
        Async get current channel prompt

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        prompt_pattern = get_prompt_pattern(prompt="", class_prompt=self.comms_prompt_pattern)
        self.transport.set_timeout(timeout=10)
        self._send_return()
        output = b""
        while True:
            output += await self._read_chunk()
            if self.comms_ansi:
                output = strip_ansi(output=output)
            channel_match = re.search(pattern=prompt_pattern, string=output)
            if channel_match:
                self.transport.set_timeout()
                current_prompt = channel_match.group(0)
                return current_prompt.decode().strip()

    async def send_input(self, channel_input: str, strip_prompt: bool = True) -> Tuple[str, str]:
        """
        Primary entry point to send data to devices in async shell mode; accept input, return result

        Args:
            channel_input: string input to send to channel
            strip_prompt: strip prompt or not, defaults to True (yes, strip the prompt)

        Returns:
            raw_result: output read from the channel with no whitespace trimming/cleaning
            processed_result: output read from the channel that has been cleaned up

        Raises:
            N/A

        """
        self._pre_send_input(channel_input=channel_input)
        raw_result, processed_result = await self._async_send_input(
            channel_input=channel_input, strip_prompt=strip_prompt
        )
        return raw_result.decode(), processed_result.decode()

    @operation_timeout("timeout_ops", "Timed out sending input to device.")
    async def _async_send_input(
        self, channel_input: str, strip_prompt: bool
    ) -> Tuple[bytes, bytes]:
        """
        Async send input to device and return results

        Note that write operations are sync, but all read ops are async, so this method must be
        async

        Args:
            channel_input: string input to write to channel
            strip_prompt: bool True/False for whether or not to strip prompt

        Returns:
            raw_result: output read from the channel with no whitespace trimming/cleaning
            processed_result: output read from the channel that has been cleaned up

        Raises:
            N/A

        """
        bytes_channel_input = channel_input.encode()
        self.transport.session_lock.acquire()
        self.logger.info(f"Attempting to send input: {channel_input}; strip_prompt: {strip_prompt}")
        self.transport.write(channel_input=channel_input)
        self.logger.debug(f"Write: {repr(channel_input)}")
        await self._read_until_input(channel_input=bytes_channel_input)
        self._send_return()
        output = await self._read_until_prompt()
        self.transport.session_lock.release()
        processed_output = self._restructure_output(output=output, strip_prompt=strip_prompt)
        # lstrip the return character out of the final result before storing, also remove any extra
        # whitespace to the right if any
        processed_output = processed_output.lstrip(self.comms_return_char.encode()).rstrip()
        return output, processed_output

    @operation_timeout("timeout_ops", "Timed out sending interactive input to device.")
    async def send_inputs_interact(
        self, interact_events: List[Tuple[str, str, Optional[bool]]]
    ) -> Tuple[str, str]:
        """
        Async interact with a device with changing prompts per input.

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

        self.transport.session_lock.acquire()
        output = b""
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
                output += await self._read_until_input(channel_input=bytes_channel_input)
                self._send_return()
            output += await self._read_until_prompt(prompt=channel_response)
        # wait to release lock until after "interact" session is complete
        self.transport.session_lock.release()
        return self._post_send_inputs_interact(output=output)
