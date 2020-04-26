"""scrapli.channel.channel"""
import re
from logging import getLogger
from typing import List, Optional, Tuple

from scrapli.decorators import operation_timeout
from scrapli.helper import get_prompt_pattern, normalize_lines, strip_ansi
from scrapli.transport.transport import Transport

LOG = getLogger("channel")


CHANNEL_ARGS = (
    "transport",
    "comms_prompt_pattern",
    "comms_return_char",
    "comms_ansi",
    "timeout_ops",
)


class Channel:
    def __init__(
        self,
        transport: Transport,
        comms_prompt_pattern: str = r"^[a-z0-9.\-@()/:]{1,32}[#>$]$",
        comms_return_char: str = "\n",
        comms_ansi: bool = False,
        comms_auto_expand: bool = False,
        timeout_ops: int = 10,
    ):
        """
        Channel Object

        Args:
            transport: Transport object of any transport provider (system|telnet or a plugin)
                transport could in theory be any transport as long as it provides a read and a write
                method... obviously its probably always going to be scrapli transport though
            comms_prompt_pattern: raw string regex pattern -- use `^` and `$` for multi-line!
            comms_return_char: character to use to send returns to host
            comms_ansi: True/False strip comms_ansi characters from output
            comms_auto_expand: bool to indicate if a device auto-expands commands, for example
                juniper devices without `cli complete-on-space` disabled will convert `config` to
                `configuration` after entering a space character after `config`; because scrapli
                reads the channel until each command is entered, the command changing from `config`
                to `configuration` will cause scrapli (by default) to never think the command has
                been entered. Setting this value to `True` will force scrapli to zip the split lists
                of inputs and outputs together to determine if each read output starts with the
                corresponding input. For example, if the inputs are "sho ver" and the read output is
                "show version", scrapli will zip the split strings together and confirm that in fact
                "show" starts with "sho" and "version" starts with "ver", confirming that the
                commands that were input were input properly. This is disabled by default, as it is
                preferable to disable this type of behavior via the device itself if possible.
            timeout_ops: timeout in seconds for channel operations (reads/writes)

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.transport: Transport = transport
        self.comms_prompt_pattern = comms_prompt_pattern
        self.comms_return_char = comms_return_char
        self.comms_ansi = comms_ansi
        self.comms_auto_expand = comms_auto_expand
        self.timeout_ops = timeout_ops

    def __str__(self) -> str:
        """
        Magic str method for Channel

        Args:
            N/A

        Returns:
            str: str for class object

        Raises:
            N/A

        """
        return "scrapli Channel Object"

    def __repr__(self) -> str:
        """
        Magic repr method for Channel

        Args:
            N/A

        Returns:
            str: repr for class object

        Raises:
            N/A

        """
        class_dict = self.__dict__.copy()
        class_dict.pop("transport")
        return f"scrapli Channel {class_dict}"

    def _restructure_output(self, output: bytes, strip_prompt: bool = False) -> bytes:
        """
        Clean up preceding empty lines, and strip prompt if desired

        Args:
            output: bytes from channel
            strip_prompt: bool True/False whether to strip prompt or not

        Returns:
            bytes: output of joined output lines optionally with prompt removed

        Raises:
            N/A

        """
        output = normalize_lines(output=output)

        if not strip_prompt:
            return output

        # could be compiled elsewhere, but allow for users to modify the prompt whenever they want
        prompt_pattern = get_prompt_pattern(prompt="", class_prompt=self.comms_prompt_pattern)
        output = re.sub(pattern=prompt_pattern, repl=b"", string=output)
        return output

    def _read_chunk(self) -> bytes:
        """
        Private method to read chunk and strip comms_ansi if needed

        Args:
            N/A

        Returns:
            bytes: output read from channel

        Raises:
            N/A

        """
        new_output = self.transport.read()
        new_output = new_output.replace(b"\r", b"")
        if self.comms_ansi:
            new_output = strip_ansi(output=new_output)
        LOG.debug(f"Read: {repr(new_output)}")
        return new_output

    def _read_until_input(self, channel_input: bytes, auto_expand: Optional[bool] = None) -> bytes:
        """
        Read until all input has been entered.

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
            LOG.info(f"Read: {repr(output)}")
            return output

        if auto_expand is None:
            auto_expand = self.comms_auto_expand

        channel_input_split = channel_input.split()
        while True:
            output += self._read_chunk()
            if not auto_expand and channel_input in output:
                break
            if auto_expand and all(
                _channel_output.startswith(_channel_input)
                for _channel_input, _channel_output in zip(channel_input_split, output.split())
            ):
                break

        LOG.info(f"Read: {repr(output)}")
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
            channel_match = re.search(pattern=prompt_pattern, string=output)
            if channel_match:
                LOG.info(f"Read: {repr(output)}")
                return output

    @operation_timeout("timeout_ops", "Timed out determining prompt on device.")
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
        self.transport.set_timeout(timeout=10)
        self._send_return()
        output = b""
        while True:
            output += self._read_chunk()
            channel_match = re.search(pattern=prompt_pattern, string=output)
            if channel_match:
                self.transport.set_timeout()
                current_prompt = channel_match.group(0)
                return current_prompt.decode().strip()

    def send_input(self, channel_input: str, strip_prompt: bool = True,) -> Tuple[str, str]:
        """
        Primary entry point to send data to devices in shell mode; accept input and returns result

        Args:
            channel_input: string input to send to channel
            strip_prompt: strip prompt or not, defaults to True (yes, strip the prompt)

        Returns:
            raw_result: output read from the channel with no whitespace trimming/cleaning
            processed_result: output read from the channel that has been cleaned up

        Raises:
            TypeError: if input is anything but a string

        """
        if not isinstance(channel_input, str):
            raise TypeError(
                f"`send_input` expects a single string, got {type(channel_input)}. "
                "to send a list of inputs use the `send_inputs` method instead"
            )
        raw_result, processed_result = self._send_input(
            channel_input=channel_input, strip_prompt=strip_prompt
        )
        return raw_result.decode(), processed_result.decode()

    @operation_timeout("timeout_ops", "Timed out sending input to device.")
    def _send_input(self, channel_input: str, strip_prompt: bool) -> Tuple[bytes, bytes]:
        """
        Send input to device and return results

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
        LOG.info(f"Attempting to send input: {channel_input}; strip_prompt: {strip_prompt}")
        self.transport.write(channel_input=channel_input)
        LOG.debug(f"Write: {repr(channel_input)}")
        self._read_until_input(channel_input=bytes_channel_input)
        self._send_return()
        output = self._read_until_prompt()
        self.transport.session_lock.release()
        processed_output = self._restructure_output(output=output, strip_prompt=strip_prompt)
        # lstrip the return character out of the final result before storing, also remove any extra
        # whitespace to the right if any
        processed_output = processed_output.lstrip(self.comms_return_char.encode()).rstrip()
        return output, processed_output

    def _send_return(self) -> None:
        """
        Send return char to device

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.transport.write(channel_input=self.comms_return_char)
        LOG.debug(f"Write (sending return character): {repr(self.comms_return_char)}")

    @operation_timeout("timeout_ops", "Timed out sending interactive input to device.")
    def send_inputs_interact(
        self, interact_events: List[Tuple[str, str, Optional[bool]]]
    ) -> Tuple[str, str]:
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
            TypeError: if inputs is not tuple or list
        """
        if not isinstance(interact_events, list):
            raise TypeError(f"`interact_events` expects a List, got {type(interact_events)}")

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
            LOG.info(
                f"Attempting to send input interact: {channel_input}; "
                f"\texpecting: {channel_response};"
                f"\thidden_input: {hidden_input}"
            )
            self.transport.write(channel_input=channel_input)
            LOG.debug(f"Write: {repr(channel_input)}")
            if not channel_response or hidden_input is True:
                self._send_return()
            else:
                output += self._read_until_input(channel_input=bytes_channel_input)
                self._send_return()
            output += self._read_until_prompt(prompt=channel_response)
        # wait to release lock until after "interact" session is complete
        self.transport.session_lock.release()
        processed_output = self._restructure_output(output=output, strip_prompt=False)
        raw_result = output.decode()
        processed_result = processed_output.decode()
        return raw_result, processed_result
