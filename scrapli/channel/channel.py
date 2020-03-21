"""scrapli.channel.channel"""
import re
from logging import getLogger
from typing import List, Tuple

from scrapli.decorators import operation_timeout
from scrapli.helper import get_prompt_pattern, normalize_lines, strip_ansi
from scrapli.response import Response
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
        timeout_ops: int = 10,
    ):
        """
        Channel Object

        Args:
            transport: Transport object of any transport provider (ssh2|paramiko|system|telnetlib)
                transport could in theory be any transport as long as it provides a read and a write
                method... obviously its probably always going to be scrapli transport though
            comms_prompt_pattern: raw string regex pattern -- use `^` and `$` for multi-line!
            comms_return_char: character to use to send returns to host
            comms_ansi: True/False strip comms_ansi characters from output
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
        output = normalize_lines(output)

        if not strip_prompt:
            return output

        # could be compiled elsewhere, but allow for users to modify the prompt whenever they want
        prompt_pattern = get_prompt_pattern("", self.comms_prompt_pattern)
        output = re.sub(prompt_pattern, b"", output)
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
        new_output = re.sub(b"\r", b"", new_output)
        if self.comms_ansi:
            new_output = strip_ansi(new_output)
        LOG.debug(f"Read: {repr(new_output)}")
        return new_output

    def _read_until_input(self, channel_input: bytes) -> bytes:
        """
        Read until all input has been entered.

        Args:
            channel_input: string to write to channel

        Returns:
            bytes: output read from channel

        Raises:
            N/A

        """
        output = b""
        while channel_input not in output:
            output += self._read_chunk()
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
        prompt_pattern = get_prompt_pattern(prompt, self.comms_prompt_pattern)

        while True:
            output += self._read_chunk()
            channel_match = re.search(prompt_pattern, output)
            if channel_match:
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
        prompt_pattern = get_prompt_pattern("", self.comms_prompt_pattern)
        self.transport.set_timeout(1000)
        self.transport.write(self.comms_return_char)
        LOG.debug(f"Write (sending return character): {repr(self.comms_return_char)}")
        output = b""
        while True:
            output += self._read_chunk()
            channel_match = re.search(prompt_pattern, output)
            if channel_match:
                self.transport.set_timeout()
                current_prompt = channel_match.group(0)
                return current_prompt.decode().strip()

    def send_input(self, channel_input: str, strip_prompt: bool = True) -> Response:
        """
        Primary entry point to send data to devices in shell mode; accept input and returns result

        Args:
            channel_input: string input to send to channel
            strip_prompt: strip prompt or not, defaults to True (yes, strip the prompt)

        Returns:
            Response: list of Response object(s)

        Raises:
            TypeError: if input is anything but a string

        """
        if not isinstance(channel_input, str):
            raise TypeError(
                f"`send_input` expects a single string, got {type(channel_input)}. "
                "to send a list of inputs use the `send_inputs` method instead"
            )
        response = Response(self.transport.host, channel_input)
        raw_result, processed_result = self._send_input(channel_input, strip_prompt)
        response.raw_result = raw_result.decode()
        response.record_response(processed_result.decode())
        return response

    def send_inputs(self, channel_inputs: List[str], strip_prompt: bool = True) -> List[Response]:
        """
        Primary entry point to send data to devices in shell mode; accept inputs and return results

        Args:
            channel_inputs: list of string inputs to send to channel
            strip_prompt: strip prompt or not, defaults to True (yes, strip the prompt)

        Returns:
            responses: list of Response object(s)

        Raises:
            TypeError: if anything but a list is passed for channel_inputs

        """
        if not isinstance(channel_inputs, list):
            raise TypeError(
                f"`send_inputs` expects a list of strings, got {type(channel_inputs)}. "
                "to send a single input use the `send_input` method instead"
            )

        responses = []
        for channel_input in channel_inputs:
            response = Response(self.transport.host, channel_input)
            raw_result, processed_result = self._send_input(channel_input, strip_prompt)
            response.raw_result = raw_result.decode()
            response.record_response(processed_result.decode())
            responses.append(response)
        return responses

    @operation_timeout("timeout_ops", "Timed out sending input to device.")
    def _send_input(self, channel_input: str, strip_prompt: bool) -> Tuple[bytes, bytes]:
        """
        Send input to device and return results

        Args:
            channel_input: string input to write to channel
            strip_prompt: bool True/False for whether or not to strip prompt

        Returns:
            result: output read from the channel

        Raises:
            N/A

        """
        bytes_channel_input = channel_input.encode()
        self.transport.session_lock.acquire()
        LOG.debug(f"Attempting to send input: {channel_input}; strip_prompt: {strip_prompt}")
        self.transport.write(channel_input)
        LOG.debug(f"Write: {repr(channel_input)}")
        self._read_until_input(bytes_channel_input)
        self._send_return()
        output = self._read_until_prompt()
        self.transport.session_lock.release()
        processed_output = self._restructure_output(output, strip_prompt=strip_prompt)
        # lstrip the return character out of the final result before storing, also remove any extra
        # whitespace to the right if any
        processed_output = processed_output.lstrip(self.comms_return_char.encode()).rstrip()
        return output, processed_output

    def send_inputs_interact(
        self, channel_inputs: List[str], hidden_response: bool = False
    ) -> Response:
        """
        Send inputs in an interactive fashion, used to handle prompts that occur after an input.

        Args:
            channel_inputs: list of four string elements representing...
                channel_input - initial input to send
                expected_prompt - prompt to expect after initial input
                response - response to prompt
                final_prompt - final prompt to expect
            hidden_response: True/False response is hidden (i.e. password input)

        Returns:
            Response: scrapli Response object

        Raises:
            TypeError: if inputs is not tuple or list

        """
        if not isinstance(channel_inputs, list):
            raise TypeError(f"`send_inputs_interact` expects a List, got {type(channel_inputs)}")
        channel_input, expectation, channel_response, finale = channel_inputs
        response = Response(
            self.transport.host,
            channel_input,
            expectation=expectation,
            channel_response=channel_response,
            finale=finale,
        )
        raw_result, processed_result = self._send_input_interact(
            channel_input, expectation, channel_response, finale, hidden_response
        )
        response.raw_result = raw_result.decode()
        response.record_response(processed_result.decode().strip())
        return response

    @operation_timeout("timeout_ops", "Timed out sending interactive input to device.")
    def _send_input_interact(
        self,
        channel_input: str,
        expectation: str,
        channel_response: str,
        finale: str,
        hidden_response: bool = False,
    ) -> Tuple[bytes, bytes]:
        """
        Respond to a single "staged" prompt and return results.

        Args:
            channel_input: string input to write to channel
            expectation: string of what to expect from channel
            channel_response: string what to respond to the `expectation`, or empty string to send
                return character only
            finale: string of prompt to look for to know when `done`
            hidden_response: True/False response is hidden (i.e. password input)

        Returns:
            output: output read from the channel

        Raises:
            N/A

        """
        bytes_channel_input = channel_input.encode()
        self.transport.session_lock.acquire()
        LOG.debug(
            f"Attempting to send input interact: {channel_input}; "
            f"\texpecting: {expectation};"
            f"\tresponding: {channel_response};"
            f"\twith a finale: {finale};"
            f"\thidden_response: {hidden_response}"
        )
        self.transport.write(channel_input)
        LOG.debug(f"Write: {repr(channel_input)}")
        self._read_until_input(bytes_channel_input)
        self._send_return()
        output = self._read_until_prompt(prompt=expectation)
        # if response is simply a return; add that so it shows in output likewise if response is
        # "hidden" (i.e. password input), add return, otherwise, skip
        if not channel_response or hidden_response is True:
            output += self.comms_return_char.encode()
        self.transport.write(channel_response)
        LOG.debug(f"Write: {repr(channel_response)}")
        self._send_return()
        LOG.debug(f"Write (sending return character): {repr(self.comms_return_char)}")
        output += self._read_until_prompt(prompt=finale)
        self.transport.session_lock.release()
        processed_output = self._restructure_output(output, strip_prompt=False)
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
        self.transport.write(self.comms_return_char)
        LOG.debug(f"Write (sending return character): {repr(self.comms_return_char)}")
