"""scrapli.channel.base_channel"""
import re
from abc import ABC
from logging import getLogger
from threading import Lock
from typing import List, Optional, Tuple, Union

from scrapli.helper import attach_duplicate_log_filter, get_prompt_pattern, normalize_lines
from scrapli.transport.async_transport import AsyncTransport
from scrapli.transport.transport import Transport

CHANNEL_ARGS = (
    "transport",
    "comms_prompt_pattern",
    "comms_return_char",
    "comms_ansi",
    "timeout_ops",
)


class ChannelBase(ABC):
    def __init__(
        self,
        transport: Union[Transport, AsyncTransport],
        comms_prompt_pattern: str = r"^[a-z0-9.\-@()/:]{1,32}[#>$]$",
        comms_return_char: str = "\n",
        comms_ansi: bool = False,
        comms_auto_expand: bool = False,
        timeout_ops: float = 10,
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
        self.logger = getLogger(f"scrapli.channel-{transport.host}")
        attach_duplicate_log_filter(logger=self.logger)

        self.transport = transport
        self.comms_prompt_pattern = comms_prompt_pattern
        self.comms_return_char = comms_return_char
        self.comms_ansi = comms_ansi
        self.comms_auto_expand = comms_auto_expand
        self.timeout_ops = timeout_ops

        self.session_lock = Lock()

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
        class_dict["session_lock"] = self.session_lock.locked()
        class_dict["logger"] = self.logger.name
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

        if strip_prompt:
            # could be compiled elsewhere, but allow users to modify the prompt whenever they want
            prompt_pattern = get_prompt_pattern(prompt="", class_prompt=self.comms_prompt_pattern)
            output = re.sub(pattern=prompt_pattern, repl=b"", string=output)

        # lstrip the return character out of the final result before storing, also remove any extra
        # whitespace to the right if any
        output = output.lstrip(self.comms_return_char.encode()).rstrip()
        return output

    @staticmethod
    def _process_auto_expand(output: bytes, channel_input: bytes) -> bool:
        """
        Determine if output has been auto expanded to canonical syntax

        Args:
            output: output from the device
            channel_input: command input to the device

        Returns:
            bool: True if it appears the output was auto-expanded, otherwise False

        Raises:
            N/A

        """
        channel_input_split = channel_input.split()
        return all(
            _channel_output.startswith(_channel_input)
            for _channel_input, _channel_output in zip(channel_input_split, output.split())
        )

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
        self.logger.debug(f"Write (sending return character): {repr(self.comms_return_char)}")

    @staticmethod
    def _pre_send_input(channel_input: str) -> None:
        """
        Handle pre "send_input" tasks for consistency between sync/async versions

        Args:
            channel_input: string input to send to channel

        Returns:
            N/A  # noqa: DAR202

        Raises:
            TypeError: if input is anything but a string

        """
        if not isinstance(channel_input, str):
            raise TypeError(f"`send_input` expects a single string, got {type(channel_input)}.")

    @staticmethod
    def _pre_send_inputs_interact(interact_events: List[Tuple[str, str, Optional[bool]]]) -> None:
        """
        Handle pre "send_inputs_interact" tasks for consistency between sync/async versions

        Args:
            interact_events: interact events passed to `send_inputs_interact`

        Returns:
            N/A  # noqa: DAR202

        Raises:
            TypeError: if input is anything but a string

        """
        if not isinstance(interact_events, list):
            raise TypeError(f"`interact_events` expects a List, got {type(interact_events)}")

    def _post_send_inputs_interact(self, output: bytes) -> Tuple[bytes, bytes]:
        """
        Handle pre "send_inputs_interact" tasks for consistency between sync/async versions

        Args:
            output: output from `send_inputs_interact` method

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        processed_output = self._restructure_output(output=output, strip_prompt=False)
        raw_result = output
        processed_result = processed_output
        return raw_result, processed_result
