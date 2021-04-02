"""scrapli.channel.base_channel"""
import re
from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
from typing import BinaryIO, List, Optional, Pattern, Tuple, Union

from scrapli.exceptions import ScrapliAuthenticationFailed, ScrapliTypeError, ScrapliValueError
from scrapli.logging import get_instance_logger
from scrapli.transport.base import AsyncTransport, Transport


@dataclass()
class BaseChannelArgs:
    """
    Dataclass for all base Channel arguments

    Args:
        comms_prompt_pattern: comms_prompt_pattern to assign to the channel; should generally be
            created/passed from the driver class
        comms_return_char: comms_return_char to assign to the channel, see above
        comms_prompt_search_depth: depth of the buffer to search in for searching for the prompt
            in "read_until_prompt"; smaller number here will generally be faster, though may be less
            reliable; default value is 1000
        comms_ansi: comms_ansi to assign to the channel, see above
        timeout_ops: timeout_ops to assign to the channel, see above
        channel_log: log "channel" output -- this would be the output you would normally see on a
            terminal. If `True` logs to `scrapli_channel.log`, if a string is provided, logs to
            wherever that string points
        channel_log_mode: "write"|"append", all other values will raise ValueError,
            does what it sounds like it should by setting the channel log to the provided mode
        channel_lock: bool indicated if channel lock should be used for all read/write operations

    Returns:
        None

    Raises:
        N/A

    """

    comms_prompt_pattern: str = r"^[a-z0-9.\-@()/:]{1,32}[#>$]$"
    comms_return_char: str = "\n"
    comms_prompt_search_depth: int = 1000
    comms_ansi: bool = False
    timeout_ops: float = 30.0
    channel_log: Union[str, bool, BytesIO] = False
    channel_log_mode: str = "write"
    channel_lock: bool = False

    def __post_init__(self) -> None:
        """
        Validate dataclass arguments at end of initialization

        Args:
            N/A

        Returns:
            None

        Raises:
            ScrapliValueError: if invalid channel_log_mode provided

        """
        if self.channel_log_mode.lower() not in (
            "write",
            "append",
        ):
            raise ScrapliValueError(
                f"provided channel_log_mode '{self.channel_log_mode}' is not valid, mode must be "
                f"one of: 'write', 'append'"
            )

        if self.channel_log_mode.lower() == "write":
            self.channel_log_mode = "w"
        else:
            self.channel_log_mode = "a"


class BaseChannel:
    def __init__(
        self,
        transport: Union[AsyncTransport, Transport],
        base_channel_args: BaseChannelArgs,
    ):
        """
        BaseChannel Object -- provides convenience methods to both sync and async Channels

        Args:
            transport: initialized scrapli Transport/AsyncTransport object
            base_channel_args: BaseChannelArgs object

        Returns:
            None

        Raises:
            N/A

        """
        self.transport = transport
        self._base_channel_args = base_channel_args

        self.logger = get_instance_logger(
            instance_name="scrapli.channel",
            host=self.transport._base_transport_args.host,
            port=self.transport._base_transport_args.port,
            uid=self.transport._base_transport_args.logging_uid,
        )

        self.channel_log: Optional[BinaryIO] = None

    def open(self) -> None:
        """
        Channel open method

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        if self._base_channel_args.channel_log:
            if isinstance(self._base_channel_args.channel_log, BytesIO):
                self.channel_log = self._base_channel_args.channel_log
            else:
                channel_log_destination = "scrapli_channel.log"
                if isinstance(self._base_channel_args.channel_log, str):
                    channel_log_destination = self._base_channel_args.channel_log
                self.logger.info(
                    f"channel log enabled, logging channel output to '{channel_log_destination}'"
                )
                # have to ignore type due to mypy not wanting to read the mode from formatted string
                # if you change the mode --> "wb" or "ab" it works as you would hope/expect; those
                # are the only values it can possibly be at this point though so we can safely
                # ignore here
                self.channel_log = open(
                    channel_log_destination,
                    mode=f"{self._base_channel_args.channel_log_mode}b",  # type: ignore
                )

    def close(self) -> None:
        """
        Channel close method

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        if self.channel_log:
            self.channel_log.close()

    def write(self, channel_input: str, redacted: bool = False) -> None:
        """
        Write input to the underlying Transport session

        Args:
            channel_input: string of input to send
            redacted: redact channel input from log or not

        Returns:
            None

        Raises:
            N/A

        """
        log_output = "REDACTED" if redacted else repr(channel_input)
        self.logger.debug(f"write: {log_output}")

        self.transport.write(channel_input=channel_input.encode())

    def send_return(self) -> None:
        """
        Convenience method to send return char

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        self.write(channel_input=self._base_channel_args.comms_return_char)

    @staticmethod
    def _join_and_compile(channel_outputs: Optional[List[bytes]]) -> Pattern[bytes]:
        """
        Convenience method for read_until_prompt_or_time to join channel inputs into a regex pattern

        Args:
            channel_outputs: list of bytes channel inputs to join into a regex pattern

        Returns:
            Pattern: joined regex pattern or an empty pattern (empty bytes)

        Raises:
            N/A

        """
        regex_channel_outputs = b""
        if channel_outputs:
            regex_channel_outputs = b"|".join(
                [b"(" + channel_output + b")" for channel_output in channel_outputs]
            )
        regex_channel_outputs_pattern = re.compile(pattern=regex_channel_outputs, flags=re.I | re.M)

        return regex_channel_outputs_pattern

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
            msg = "Host key verification failed"
        elif b"operation timed out" in output.lower() or b"connection timed out" in output.lower():
            msg = "Timed out connecting to host"
        elif b"no route to host" in output.lower():
            msg = "No route to host"
        elif b"no matching key exchange" in output.lower():
            msg = "No matching key exchange found for host"
            key_exchange_pattern = re.compile(
                pattern=rb"their offer: ([a-z0-9\-,]*)", flags=re.M | re.I
            )
            offered_key_exchanges_match = re.search(pattern=key_exchange_pattern, string=output)
            if offered_key_exchanges_match:
                offered_key_exchanges = offered_key_exchanges_match.group(1).decode()
                msg += f", their offer: {offered_key_exchanges}"
        elif b"no matching cipher" in output.lower():
            msg = "No matching cipher found for host"
            ciphers_pattern = re.compile(pattern=rb"their offer: ([a-z0-9\-,]*)", flags=re.M | re.I)
            offered_ciphers_match = re.search(pattern=ciphers_pattern, string=output)
            if offered_ciphers_match:
                offered_ciphers = offered_ciphers_match.group(1).decode()
                msg += f", their offer: {offered_ciphers}"
        elif b"bad configuration" in output.lower():
            msg = "Bad SSH configuration option(s) for host"
            configuration_pattern = re.compile(
                pattern=rb"bad configuration option: ([a-z0-9\+\=,]*)", flags=re.M | re.I
            )
            configuration_issue_match = re.search(pattern=configuration_pattern, string=output)
            if configuration_issue_match:
                configuration_issues = configuration_issue_match.group(1).decode()
                msg += f", bad option(s): {configuration_issues}"
        elif b"WARNING: UNPROTECTED PRIVATE KEY FILE!" in output:
            msg = "Permissions for private key are too open, authentication failed!"
        elif b"could not resolve hostname" in output.lower():
            msg = "Could not resolve address for host"
        if msg:
            self.logger.critical(msg)
            raise ScrapliAuthenticationFailed(msg)

    @staticmethod
    @lru_cache()
    def _get_prompt_pattern(class_pattern: str, pattern: Optional[str] = None) -> Pattern[bytes]:
        """
        Return compiled prompt pattern

        Given a potential prompt and the Channel class' prompt, return compiled prompt pattern

        Args:
            class_pattern: comms_prompt_pattern from the class itself; must be passed so that the
                arguments are recognized in lru cache; this way if a user changes the pattern during
                normal scrapli operations the lru cache can "notice" the pattern changed!
            pattern: optional regex pattern to compile, if not provided we use the class' pattern

        Returns:
            pattern: compiled regex pattern to use to search for a prompt in output data

        Raises:
            N/A

        """
        if not pattern:
            return re.compile(class_pattern.encode(), flags=re.M | re.I)

        bytes_pattern = pattern.encode()
        if bytes_pattern.startswith(b"^") and bytes_pattern.endswith(b"$"):
            return re.compile(bytes_pattern, flags=re.M | re.I)
        return re.compile(re.escape(bytes_pattern))

    def _process_output(self, buf: bytes, strip_prompt: bool) -> bytes:
        """
        Process output received form the device

        Remove inputs and prompts if desired

        Args:
            buf: bytes output from the device
            strip_prompt: True/False strip the prompt from the device output

        Returns:
            bytes: cleaned up byte string

        Raises:
            N/A

        """
        buf = b"\n".join([line.rstrip() for line in buf.splitlines()])

        if strip_prompt:
            prompt_pattern = self._get_prompt_pattern(
                class_pattern=self._base_channel_args.comms_prompt_pattern
            )
            buf = re.sub(pattern=prompt_pattern, repl=b"", string=buf)

        buf = buf.lstrip(self._base_channel_args.comms_return_char.encode()).rstrip()
        return buf

    @staticmethod
    def _strip_ansi(buf: bytes) -> bytes:
        """
        Strip ansi characters from output

        Args:
            buf: bytes from previous reads if needed

        Returns:
            bytes: bytes output read from channel with ansi characters removed

        Raises:
            N/A

        """
        ansi_escape_pattern = re.compile(rb"\x1b(\[.*?[@-~]|\].*?(\x07|\x1b\\))")
        buf = re.sub(pattern=ansi_escape_pattern, repl=b"", string=buf)
        return buf

    @staticmethod
    def _pre_send_input(channel_input: str) -> None:
        """
        Handle pre "send_input" tasks for consistency between sync/async versions

        Args:
            channel_input: string input to send to channel

        Returns:
            bytes: current channel buffer

        Raises:
            ScrapliTypeError: if input is anything but a string

        """
        if not isinstance(channel_input, str):
            raise ScrapliTypeError(
                f"`send_input` expects a single string, got {type(channel_input)}."
            )

    @staticmethod
    def _pre_send_inputs_interact(interact_events: List[Tuple[str, str, Optional[bool]]]) -> None:
        """
        Handle pre "send_inputs_interact" tasks for consistency between sync/async versions

        Args:
            interact_events: interact events passed to `send_inputs_interact`

        Returns:
            None

        Raises:
            ScrapliTypeError: if input is anything but a string

        """
        if not isinstance(interact_events, list):
            raise ScrapliTypeError(f"`interact_events` expects a List, got {type(interact_events)}")
