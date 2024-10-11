"""scrapli.driver.generic.base_driver"""

import re
from typing import (
    TYPE_CHECKING,
    Any,
    Awaitable,
    Callable,
    Coroutine,
    List,
    Optional,
    Pattern,
    Tuple,
    Union,
)

from scrapli.exceptions import ScrapliTypeError
from scrapli.helper import resolve_file
from scrapli.response import MultiResponse, Response

if TYPE_CHECKING:
    from scrapli.driver.generic.async_driver import AsyncGenericDriver  # pragma:  no cover
    from scrapli.driver.generic.sync_driver import GenericDriver  # pragma:  no cover


class ReadCallback:
    def __init__(  # pylint: disable=R0917
        self,
        callback: Callable[
            [Union["GenericDriver", "AsyncGenericDriver"], str],
            Union[None, Coroutine[Any, Any, None]],
        ],
        contains: str = "",
        not_contains: str = "",
        contains_re: str = "",
        case_insensitive: bool = True,
        multiline: bool = True,
        reset_output: bool = True,
        only_once: bool = False,
        next_delay: float = -1.0,
        next_timeout: float = -1.0,
        complete: bool = False,
        name: str = "",
    ):
        """
        Object representing a single callback to be used with `GenericDriver` `read_callback` method

        Though the callable is typed with GenericDriver and AsyncGenericDriver, the callable can of
        course accept a NetworkDriver or AsyncNetworkDriver or any class extending those, you just
        may get some IDE/mypy complaints!

        Args:
            callback: callback function to execute, callback function must accept instance of the
                class as first argument, and the  "read_output" as second
            contains: string of text that, if in the read output, indicates to execute this callback
            not_contains: string of text that should *not* be contained in the output
            contains_re: string of a regex pattern that will be compiled and used to match the
                callback
            case_insensitive: ignored unless contains_re provided, sets re.I on compiled regex
            multiline: ignored unless contains_re provided, sets re.M on compiled regex
            reset_output: bool indicating to reset (clear) the output or to pass the output along
                to the next iteration. Sometimes you may want to clear the output to not
                accidentally continue matching on one callback over and over again. You could also
                use `only_once` to help with that
            only_once: bool indicating if this callback should only ever be executed one time
            next_delay: optional sleep between reads for next callback check
            next_timeout: optionally set the transport timeout (to timeout the read operation) for
                the subsequent callback checks -- the default value of -1.0 will tell scrapli to use
                the "normal" transport timeout for the operation
            complete: bool indicating if this is the "last" callback to execute
            name: friendly name to give the callback, will be function name if not provided

        Returns:
            N/A

        Raises:
            N/A

        """
        self.name = name
        if self.name == "":
            self.name = callback.__name__

        self.callback = callback

        self.contains = contains
        self._contains_bytes = b""

        self.not_contains = not_contains
        self._not_contains_bytes = b""

        self.contains_re = contains_re
        self._contains_re_bytes: Optional[Pattern[bytes]] = None

        self.case_insensitive = case_insensitive
        self.multiline = multiline
        self.reset_output = reset_output

        self.only_once = only_once
        self._triggered = False

        self.next_delay = next_delay
        self.next_timeout = next_timeout

        self.complete = complete

        self._read_output = b""

    @property
    def contains_bytes(self) -> bytes:
        """
        Property to encode provided not contains if requested

        Args:
            N/A

        Returns:
            bytes: encoded not contains string

        Raises:
            N/A

        """
        if self.contains and not self._contains_bytes:
            self._contains_bytes = self.contains.encode()
            if self.case_insensitive:
                self._contains_bytes = self._contains_bytes.lower()

        return self._contains_bytes

    @property
    def not_contains_bytes(self) -> bytes:
        """
        Property to encode provided contains if requested

        Args:
            N/A

        Returns:
            bytes: encoded contains string

        Raises:
            N/A

        """
        if self.not_contains and not self._not_contains_bytes:
            self._not_contains_bytes = self.not_contains.encode()
            if self.case_insensitive:
                self._not_contains_bytes = self._not_contains_bytes.lower()

        return self._not_contains_bytes

    @property
    def contains_re_bytes(self) -> Pattern[bytes]:
        """
        Property to encode provided regex contains if requested

        Args:
            N/A

        Returns:
            re.Pattern: compiled bytes pattern

        Raises:
            N/A

        """
        if not self._contains_re_bytes:
            flags = 0

            if self.case_insensitive and self.multiline:
                flags = re.I | re.M
            elif self.case_insensitive:
                flags = re.I
            elif self.multiline:
                flags = re.M

            self._contains_re_bytes = re.compile(pattern=self.contains_re.encode(), flags=flags)

        return self._contains_re_bytes

    def check(self, read_output: bytes) -> bool:
        """
        Determine if a callback has matched based on device output

        Args:
            read_output: bytes read from the device

        Returns:
            bool: True/False indicating if the callback "matches" the output

        Raises:
            N/A

        """
        self._read_output = read_output

        if self.case_insensitive:
            _read_output = read_output.lower()
        else:
            _read_output = read_output

        if (
            self.contains_bytes
            and self.contains_bytes in _read_output
            and not (self.not_contains and self.not_contains_bytes in _read_output)
        ):
            return True

        if (
            self.contains_re
            and re.search(self.contains_re_bytes, _read_output)
            and not (self.not_contains and self.not_contains_bytes in _read_output)
        ):
            return True

        return False

    def run(
        self, driver: Union["GenericDriver", "AsyncGenericDriver"]
    ) -> Union[None, Awaitable[Any]]:
        """
        Run the callback

        Args:
            driver: driver object to pass to the callback function

        Returns:
            Union[None, Awaitable[Any]]: return the result of the callable if sync or the future

        Raises:
            N/A

        """
        if self.only_once is True:
            self._triggered = True

        return self.callback(driver, self._read_output.decode())


ReadCallbackReturnable = Union[
    None,
    Callable[[List[ReadCallback], Optional[str], bytes, float], Union[None, Any]],
]


class BaseGenericDriver:
    @staticmethod
    def _pre_send_command(
        host: str, command: str, failed_when_contains: Optional[Union[str, List[str]]] = None
    ) -> Response:
        """
        Handle pre "send_command" tasks for consistency between sync/async versions

        Args:
            host: string name of the host
            command: string to send to device in privilege exec mode
            failed_when_contains: string or list of strings indicating failure if found in response

        Returns:
            Response: Scrapli Response object

        Raises:
            ScrapliTypeError: if command is anything but a string

        """
        if not isinstance(command, str):
            raise ScrapliTypeError(
                f"`send_command` expects a single string, got {type(command)}, "
                "to send a list of commands use the `send_commands` method instead."
            )

        return Response(
            host=host,
            channel_input=command,
            failed_when_contains=failed_when_contains,
        )

    @staticmethod
    def _post_send_command(
        raw_response: bytes, processed_response: bytes, response: Response
    ) -> Response:
        """
        Handle post "send_command" tasks for consistency between sync/async versions

        Args:
            raw_response: raw response returned from the channel
            processed_response: processed response returned from the channel
            response: response object to update with channel results

        Returns:
            Response: Scrapli Response object

        Raises:
            N/A

        """
        response.record_response(result=processed_response)
        response.raw_result = raw_response
        return response

    @staticmethod
    def _pre_send_commands(commands: List[str]) -> MultiResponse:
        """
        Handle pre "send_command" tasks for consistency between sync/async versions

        Args:
            commands: list of strings to send to device in privilege exec mode

        Returns:
            MultiResponse: Scrapli MultiResponse object

        Raises:
            ScrapliTypeError: if command is anything but a string

        """
        if not isinstance(commands, list):
            raise ScrapliTypeError(
                f"`send_commands` expects a list of strings, got {type(commands)}, "
                "to send a single command use the `send_command` method instead."
            )

        return MultiResponse()

    @staticmethod
    def _pre_send_from_file(file: str, caller: str) -> List[str]:
        """
        Handle pre "send_*_from_file" tasks for consistency between sync/async versions

        Args:
            file: string path to file
            caller: name of the calling method for more helpful error message

        Returns:
            list: list of commands/configs read from file

        Raises:
            ScrapliTypeError: if anything but a string is provided for `file`

        """
        if not isinstance(file, str):
            raise ScrapliTypeError(f"`{caller}` expects a string path to a file, got {type(file)}")
        resolved_file = resolve_file(file)

        with open(resolved_file, encoding="utf-8") as f:
            commands = f.read().splitlines()

        return commands

    @classmethod
    def _pre_send_interactive(
        cls,
        host: str,
        interact_events: Union[List[Tuple[str, str]], List[Tuple[str, str, bool]]],
        failed_when_contains: Optional[Union[str, List[str]]] = None,
    ) -> Response:
        """
        Handle pre "send_interactive" tasks for consistency between sync/async versions

        Args:
            host: string name of the host
            interact_events: list of tuples containing the "interactions" with the device
                each list element must have an input and an expected response, and may have an
                optional bool for the third and final element -- the optional bool specifies if the
                input that is sent to the device is "hidden" (ex: password), if the hidden param is
                not provided it is assumed the input is "normal" (not hidden)
            failed_when_contains: string or list of strings indicating failure if found in response

        Returns:
            Response: Scrapli Response object

        Raises:
            N/A

        """
        joined_input = ", ".join(event[0] for event in interact_events)
        return cls._pre_send_command(
            host=host, command=joined_input, failed_when_contains=failed_when_contains
        )
