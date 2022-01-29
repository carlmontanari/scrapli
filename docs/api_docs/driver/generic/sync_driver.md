<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/sanitize.min.css" integrity="sha256-PK9q560IAAa6WVRRh76LtCaI8pjTJ2z11v0miyNNjrs=" crossorigin>
<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/typography.min.css" integrity="sha256-7l/o7C8jubJiy74VsKTidCy1yBkRtiUGbVkYBylBqUg=" crossorigin>
<link rel="stylesheet preload" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/styles/github.min.css" crossorigin>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/highlight.min.js" integrity="sha256-Uv3H6lx7dJmRfRvH8TH6kJD1TSK1aFcwgx+mdg3epi8=" crossorigin></script>
<script>window.addEventListener('DOMContentLoaded', () => hljs.initHighlighting())</script>















#Module scrapli.driver.generic.sync_driver

scrapli.driver.generic.sync_driver

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
"""scrapli.driver.generic.sync_driver"""
import time
from io import BytesIO
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple, Union

from scrapli.decorators import TimeoutOpsModifier
from scrapli.driver import Driver
from scrapli.driver.generic.base_driver import BaseGenericDriver
from scrapli.exceptions import ScrapliTimeout, ScrapliValueError
from scrapli.response import MultiResponse, Response

if TYPE_CHECKING:
    from scrapli.driver.generic.base_driver import (  # pragma:  no cover
        ReadCallback,
        ReadCallbackReturnable,
    )


class GenericDriver(Driver, BaseGenericDriver):
    def __init__(
        self,
        host: str,
        port: Optional[int] = None,
        auth_username: str = "",
        auth_password: str = "",
        auth_private_key: str = "",
        auth_private_key_passphrase: str = "",
        auth_strict_key: bool = True,
        auth_bypass: bool = False,
        timeout_socket: float = 15.0,
        timeout_transport: float = 30.0,
        timeout_ops: float = 30.0,
        comms_prompt_pattern: str = r"^\S{0,48}[#>$~@:\]]\s*$",
        comms_return_char: str = "\n",
        ssh_config_file: Union[str, bool] = False,
        ssh_known_hosts_file: Union[str, bool] = False,
        on_init: Optional[Callable[..., Any]] = None,
        on_open: Optional[Callable[..., Any]] = None,
        on_close: Optional[Callable[..., Any]] = None,
        transport: str = "system",
        transport_options: Optional[Dict[str, Any]] = None,
        channel_log: Union[str, bool, BytesIO] = False,
        channel_log_mode: str = "write",
        channel_lock: bool = False,
        logging_uid: str = "",
    ) -> None:
        super().__init__(
            host=host,
            port=port,
            auth_username=auth_username,
            auth_password=auth_password,
            auth_private_key=auth_private_key,
            auth_private_key_passphrase=auth_private_key_passphrase,
            auth_strict_key=auth_strict_key,
            auth_bypass=auth_bypass,
            timeout_socket=timeout_socket,
            timeout_transport=timeout_transport,
            timeout_ops=timeout_ops,
            comms_prompt_pattern=comms_prompt_pattern,
            comms_return_char=comms_return_char,
            ssh_config_file=ssh_config_file,
            ssh_known_hosts_file=ssh_known_hosts_file,
            on_init=on_init,
            on_open=on_open,
            on_close=on_close,
            transport=transport,
            transport_options=transport_options,
            channel_log=channel_log,
            channel_log_mode=channel_log_mode,
            channel_lock=channel_lock,
            logging_uid=logging_uid,
        )

    def get_prompt(self) -> str:
        """
        Convenience method to fetch prompt from the underlying Channel object

        Args:
            N/A

        Returns:
            str: string of the current prompt

        Raises:
            N/A

        """
        # assigned/typed here as decorator indicates return of Any
        prompt: str = self.channel.get_prompt()
        return prompt

    @TimeoutOpsModifier()
    def _send_command(
        self,
        command: str,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        eager: bool = False,
        timeout_ops: Optional[float] = None,
    ) -> Response:
        """
        Send a command

        Private method so that we can handle `eager` w/out having to have that argument showing up
        in all the methods that super to the "normal" send_command method as we only ever want eager
        to be used for the plural options -- i.e. send_commands not send_command!

        Args:
            command: string to send to device in privilege exec mode
            strip_prompt: strip prompt or not, defaults to True (yes, strip the prompt)
            failed_when_contains: string or list of strings indicating failure if found in response
            eager: if eager is True we do not read until prompt is seen at each command sent to the
                channel. Do *not* use this unless you know what you are doing as it is possible that
                it can make scrapli less reliable!
            timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
                the duration of the operation, value is reset to initial value after operation is
                completed

        Returns:
            Response: Scrapli Response object

        Raises:
            ScrapliValueError: if _base_transport_args is None for some reason

        """
        # decorator cares about timeout_ops, but nothing else does, assign to _ to appease linters
        _ = timeout_ops

        if not self._base_transport_args:
            # should not happen! :)
            raise ScrapliValueError("driver _base_transport_args not set for some reason")

        response = self._pre_send_command(
            host=self._base_transport_args.host,
            command=command,
            failed_when_contains=failed_when_contains,
        )
        raw_response, processed_response = self.channel.send_input(
            channel_input=command, strip_prompt=strip_prompt, eager=eager
        )
        return self._post_send_command(
            raw_response=raw_response, processed_response=processed_response, response=response
        )

    def send_command(
        self,
        command: str,
        *,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        timeout_ops: Optional[float] = None,
    ) -> Response:
        """
        Send a command

        Args:
            command: string to send to device in privilege exec mode
            strip_prompt: strip prompt or not, defaults to True (yes, strip the prompt)
            failed_when_contains: string or list of strings indicating failure if found in response
            timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
                the duration of the operation, value is reset to initial value after operation is
                completed

        Returns:
            Response: Scrapli Response object

        Raises:
            N/A

        """
        response: Response = self._send_command(
            command=command,
            strip_prompt=strip_prompt,
            failed_when_contains=failed_when_contains,
            timeout_ops=timeout_ops,
        )
        return response

    def send_commands(
        self,
        commands: List[str],
        *,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        stop_on_failed: bool = False,
        eager: bool = False,
        timeout_ops: Optional[float] = None,
    ) -> MultiResponse:
        """
        Send multiple commands

        Args:
            commands: list of strings to send to device in privilege exec mode
            strip_prompt: strip prompt or not, defaults to True (yes, strip the prompt)
            failed_when_contains: string or list of strings indicating failure if found in response
            stop_on_failed: True/False stop executing commands if a command fails, returns results
                as of current execution
            eager: if eager is True we do not read until prompt is seen at each command sent to the
                channel. Do *not* use this unless you know what you are doing as it is possible that
                it can make scrapli less reliable!
            timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
                the duration of the operation, value is reset to initial value after operation is
                completed. Note that this is the timeout value PER COMMAND sent, not for the total
                of the commands being sent!

        Returns:
            MultiResponse: Scrapli MultiResponse object

        Raises:
            N/A

        """
        responses = self._pre_send_commands(commands=commands)
        for command in commands[:-1]:
            response = self._send_command(
                command=command,
                strip_prompt=strip_prompt,
                failed_when_contains=failed_when_contains,
                timeout_ops=timeout_ops,
                eager=eager,
            )
            responses.append(response)
            if stop_on_failed and response.failed is True:
                # should we find the prompt here w/ get_prompt?? or just let subsequent operations
                # deal w/ finding that? future us problem? :)
                break
        else:
            # if we did *not* break (i.e. no failure and/or no stop_on_failed) send the last command
            # with eager = False -- this way we *always* find the prompt at the end of the commands
            response = self._send_command(
                command=commands[-1],
                strip_prompt=strip_prompt,
                failed_when_contains=failed_when_contains,
                timeout_ops=timeout_ops,
                eager=False,
            )
            responses.append(response)

        return responses

    def send_commands_from_file(
        self,
        file: str,
        *,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        stop_on_failed: bool = False,
        eager: bool = False,
        timeout_ops: Optional[float] = None,
    ) -> MultiResponse:
        """
        Send command(s) from file

        Args:
            file: string path to file
            strip_prompt: True/False strip prompt from returned output
            failed_when_contains: string or list of strings indicating failure if found in response
            stop_on_failed: True/False stop executing commands if a command fails, returns results
                as of current execution
            eager: if eager is True we do not read until prompt is seen at each command sent to the
                channel. Do *not* use this unless you know what you are doing as it is possible that
                it can make scrapli less reliable!
            timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
                the duration of the operation, value is reset to initial value after operation is
                completed. Note that this is the timeout value PER COMMAND sent, not for the total
                of the commands being sent!

        Returns:
            MultiResponse: Scrapli MultiResponse object

        Raises:
            N/A

        """
        commands = self._pre_send_from_file(file=file, caller="send_commands_from_file")

        return self.send_commands(
            commands=commands,
            strip_prompt=strip_prompt,
            failed_when_contains=failed_when_contains,
            stop_on_failed=stop_on_failed,
            eager=eager,
            timeout_ops=timeout_ops,
        )

    @TimeoutOpsModifier()
    def send_and_read(
        self,
        channel_input: str,
        *,
        expected_outputs: Optional[List[str]] = None,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        timeout_ops: Optional[float] = None,
        read_duration: float = 2.5,
    ) -> Response:
        """
        Send an input and read outputs.

        Unlike "normal" scrapli behavior this method reads until the prompt(normal) OR until any of
        a list of expected outputs is seen, OR until the read duration is exceeded. This method does
        not care about/understand privilege levels. This *can* cause you some potential issues if
        not used carefully!

        Args:
            channel_input: input to send to the channel; intentionally named "channel_input" instead
                of "command" or "config" due to this method not caring about privilege levels
            expected_outputs: List of outputs to look for in device response; returns as soon as any
                of the outputs are seen
            strip_prompt: True/False strip prompt from returned output
            failed_when_contains: string or list of strings indicating failure if found in response
            timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
                the duration of the operation, value is reset to initial value after operation is
                completed
            read_duration:  float duration to read for

        Returns:
            Response: Scrapli Response object

        Raises:
            ScrapliValueError: if _base_transport_args is None for some reason

        """
        # decorator cares about timeout_ops, but nothing else does, assign to _ to appease linters
        _ = timeout_ops

        if not self._base_transport_args:
            # should not happen! :)
            raise ScrapliValueError("driver _base_transport_args not set for some reason")

        response = self._pre_send_command(
            host=self._base_transport_args.host,
            command=channel_input,
            failed_when_contains=failed_when_contains,
        )
        raw_response, processed_response = self.channel.send_input_and_read(
            channel_input=channel_input,
            strip_prompt=strip_prompt,
            expected_outputs=expected_outputs,
            read_duration=read_duration,
        )
        return self._post_send_command(
            raw_response=raw_response, processed_response=processed_response, response=response
        )

    @TimeoutOpsModifier()
    def send_interactive(
        self,
        interact_events: Union[List[Tuple[str, str]], List[Tuple[str, str, bool]]],
        *,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        privilege_level: str = "",
        timeout_ops: Optional[float] = None,
        interaction_complete_patterns: Optional[List[str]] = None,
    ) -> Response:
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
            failed_when_contains: list of strings that, if present in final output, represent a
                failed command/interaction
            privilege_level: ignored in this base class; for LSP reasons for subclasses
            timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
                the duration of the operation, value is reset to initial value after operation is
                completed. Note that this is the timeout value PER COMMAND sent, not for the total
                of the commands being sent!
            interaction_complete_patterns: list of patterns, that if seen, indicate the interactive
                "session" has ended and we should exit the interactive session.

        Returns:
            Response: scrapli Response object

        Raises:
            ScrapliValueError: if _base_transport_args is None for some reason

        """
        # decorator cares about timeout_ops, but nothing else does, assign to _ to appease linters
        _ = timeout_ops
        # privilege level only matters "up" in the network driver layer
        _ = privilege_level

        if not self._base_transport_args:
            # should not happen! :)
            raise ScrapliValueError("driver _base_transport_args not set for some reason")

        response = self._pre_send_interactive(
            host=self._base_transport_args.host,
            interact_events=interact_events,
            failed_when_contains=failed_when_contains,
        )
        raw_response, processed_response = self.channel.send_inputs_interact(
            interact_events=interact_events,
            interaction_complete_patterns=interaction_complete_patterns,
        )
        return self._post_send_command(
            raw_response=raw_response, processed_response=processed_response, response=response
        )

    def read_callback(
        self,
        callbacks: List["ReadCallback"],
        initial_input: Optional[str] = None,
        read_output: bytes = b"",
        read_delay: float = 0.1,
        read_timeout: float = -1.0,
    ) -> "ReadCallbackReturnable":
        r"""
        Read from a channel and react to the output with some callback.

        This method is kind of like an "advanced" send_interactive -- the idea is simple: send some
        "stuff" to the channel (optionally), and then read from the channel. Based on the output
        do something. The callbacks is a list of `ReadCallback` which is an object containing the
        actual callback to execute, some info about when to trigger that callback (also when *not*
        to trigger that callback), as well as some attributes to control the next (if desired)
        iteration of read_callback. You could in theory do basically everything with this method by
        chaining callbacks forever, but you probably don't want to do that for real!

        Example usage:

        ```
        from scrapli.driver.core import IOSXEDriver
        from scrapli.driver.generic.base_driver import ReadCallback
        from scrapli.driver.generic.sync_driver import GenericDriver

        device = {
            "host": "rtr1",
            "auth_strict_key": False,
            "ssh_config_file": True,
        }

        def callback_one(cls: GenericDriver, read_output: str):
            cls.acquire_priv("configuration")
            cls.channel.send_return()


        def callback_two(cls: GenericDriver, read_output: str):
            print(f"previous read output : {read_output}")

            r = cls.send_command("show run | i hostname")
            print(f"result: {r.result}")


        with IOSXEDriver(**device) as conn:
            callbacks = [
                ReadCallback(
                    contains="rtr1#",
                    callback=callback_one,
                    name="call1",
                    case_insensitive=False
                ),
                ReadCallback(
                    contains_re=r"^rtr1\(config\)#",
                    callback=callback_two,
                    complete=True,
                )
            ]
            conn.read_callback(callbacks=callbacks, initial_input="show run | i hostname")
        ```

        Args:
            callbacks: a list of ReadCallback objects
            initial_input: optional string to send to "kick off" the read_callback method
            read_output: optional bytes to append any new reads to
            read_delay: sleep interval between reads
            read_timeout: value to set the `transport_timeout` to for the duration of the reading
                portion of this method. If left default (-1.0) or set to anything below 0, the
                transport timeout value will be left alone (whatever the timeout_transport value is)
                otherwise, the provided value will be temporarily set as the timeout_transport for
                duration of the reading.

        Returns:
            ReadCallbackReturnable: either None or call to read_callback again

        Raises:
            ScrapliTimeout: if the read operation times out (base don the read_timeout value) during
                the read callback check.

        """
        if initial_input is not None:
            self.channel.write(channel_input=f"{initial_input}{self.comms_return_char}")
            return self.read_callback(callbacks=callbacks, initial_input=None)

        original_transport_timeout = self.timeout_transport

        # if the read_timeout value is -1.0 or just less than 0, that indicates we should use
        # the "normal" transport timeout and not modify anything
        self.timeout_transport = read_timeout if read_timeout >= 0 else self.timeout_transport

        _read_delay = 0.1 if read_delay <= 0 else read_delay

        while True:
            try:
                read_output += self.channel.read()
            except ScrapliTimeout as exc:
                self.timeout_transport = original_transport_timeout

                raise ScrapliTimeout("timeout during read in read_callback operation") from exc

            for callback in callbacks:
                _run_callback = callback.check(read_output=read_output)

                if (
                    callback.only_once is True
                    and callback._triggered is True  # pylint: disable=W0212
                ):
                    self.logger.warning(
                        f"callback {callback.name} matches but is set to 'only_once', "
                        "skipping this callback"
                    )

                    continue

                if _run_callback is True:
                    self.logger.info(f"callback {callback.name} matched, executing")

                    self.timeout_transport = original_transport_timeout

                    callback.run(driver=self)

                    if callback.complete:
                        self.logger.debug("callback complete is true, done with read_callback")
                        return None

                    if callback.reset_output:
                        read_output = b""

                    return self.read_callback(
                        callbacks=callbacks,
                        initial_input=None,
                        read_output=read_output,
                        read_delay=callback.next_delay,
                        read_timeout=callback.next_timeout,
                    )

            time.sleep(_read_delay)
        </code>
    </pre>
</details>




## Classes

### GenericDriver


```text
BaseDriver Object

BaseDriver is the root for all Scrapli driver classes. The synchronous and asyncio driver
base driver classes can be used to provide a semi-pexpect like experience over top of
whatever transport a user prefers. Generally, however, the base driver classes should not be
used directly. It is best to use the GenericDriver (or AsyncGenericDriver) or NetworkDriver
(or AsyncNetworkDriver) sub-classes of the base drivers.

Args:
    host: host ip/name to connect to
    port: port to connect to
    auth_username: username for authentication
    auth_private_key: path to private key for authentication
    auth_private_key_passphrase: passphrase for decrypting ssh key if necessary
    auth_password: password for authentication
    auth_strict_key: strict host checking or not
    auth_bypass: bypass "in channel" authentication -- only supported with telnet,
        asynctelnet, and system transport plugins
    timeout_socket: timeout for establishing socket/initial connection in seconds
    timeout_transport: timeout for ssh|telnet transport in seconds
    timeout_ops: timeout for ssh channel operations
    comms_prompt_pattern: raw string regex pattern -- preferably use `^` and `$` anchors!
        this is the single most important attribute here! if this does not match a prompt,
        scrapli will not work!
        IMPORTANT: regex search uses multi-line + case insensitive flags. multi-line allows
        for highly reliably matching for prompts however we do NOT strip trailing whitespace
        for each line, so be sure to add '\\s?' or similar if your device needs that. This
        should be mostly sorted for you if using network drivers (i.e. `IOSXEDriver`).
        Lastly, the case insensitive is just a convenience factor so i can be lazy.
    comms_return_char: character to use to send returns to host
    ssh_config_file: string to path for ssh config file, True to use default ssh config file
        or False to ignore default ssh config file
    ssh_known_hosts_file: string to path for ssh known hosts file, True to use default known
        file locations. Only applicable/needed if `auth_strict_key` is set to True
    on_init: callable that accepts the class instance as its only argument. this callable,
        if provided, is executed as the last step of object instantiation -- its purpose is
        primarily to provide a mechanism for scrapli community platforms to have an easy way
        to modify initialization arguments/object attributes without needing to create a
        class that extends the driver, instead allowing the community platforms to simply
        build from the GenericDriver or NetworkDriver classes, and pass this callable to do
        things such as appending to a username (looking at you RouterOS!!). Note that this
        is *always* a synchronous function (even for asyncio drivers)!
    on_open: callable that accepts the class instance as its only argument. this callable,
        if provided, is executed immediately after authentication is completed. Common use
        cases for this callable would be to disable paging or accept any kind of banner
        message that prompts a user upon connection
    on_close: callable that accepts the class instance as its only argument. this callable,
        if provided, is executed immediately prior to closing the underlying transport.
        Common use cases for this callable would be to save configurations prior to exiting,
        or to logout properly to free up vtys or similar
    transport: name of the transport plugin to use for the actual telnet/ssh/netconf
        connection. Available "core" transports are:
            - system
            - telnet
            - asynctelnet
            - ssh2
            - paramiko
            - asyncssh
        Please see relevant transport plugin section for details. Additionally third party
        transport plugins may be available.
    transport_options: dictionary of options to pass to selected transport class; see
        docs for given transport class for details of what to pass here
    channel_lock: True/False to lock the channel (threading.Lock/asyncio.Lock) during
        any channel operations, defaults to False
    channel_log: True/False or a string path to a file of where to write out channel logs --
        these are not "logs" in the normal logging module sense, but only the output that is
        read from the channel. In other words, the output of the channel log should look
        similar to what you would see as a human connecting to a device
    channel_log_mode: "write"|"append", all other values will raise ValueError,
        does what it sounds like it should by setting the channel log to the provided mode
    logging_uid: unique identifier (string) to associate to log messages; useful if you have
        multiple connections to the same device (i.e. one console, one ssh, or one to each
        supervisor module, etc.)

Returns:
    None

Raises:
    N/A
```

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
class GenericDriver(Driver, BaseGenericDriver):
    def __init__(
        self,
        host: str,
        port: Optional[int] = None,
        auth_username: str = "",
        auth_password: str = "",
        auth_private_key: str = "",
        auth_private_key_passphrase: str = "",
        auth_strict_key: bool = True,
        auth_bypass: bool = False,
        timeout_socket: float = 15.0,
        timeout_transport: float = 30.0,
        timeout_ops: float = 30.0,
        comms_prompt_pattern: str = r"^\S{0,48}[#>$~@:\]]\s*$",
        comms_return_char: str = "\n",
        ssh_config_file: Union[str, bool] = False,
        ssh_known_hosts_file: Union[str, bool] = False,
        on_init: Optional[Callable[..., Any]] = None,
        on_open: Optional[Callable[..., Any]] = None,
        on_close: Optional[Callable[..., Any]] = None,
        transport: str = "system",
        transport_options: Optional[Dict[str, Any]] = None,
        channel_log: Union[str, bool, BytesIO] = False,
        channel_log_mode: str = "write",
        channel_lock: bool = False,
        logging_uid: str = "",
    ) -> None:
        super().__init__(
            host=host,
            port=port,
            auth_username=auth_username,
            auth_password=auth_password,
            auth_private_key=auth_private_key,
            auth_private_key_passphrase=auth_private_key_passphrase,
            auth_strict_key=auth_strict_key,
            auth_bypass=auth_bypass,
            timeout_socket=timeout_socket,
            timeout_transport=timeout_transport,
            timeout_ops=timeout_ops,
            comms_prompt_pattern=comms_prompt_pattern,
            comms_return_char=comms_return_char,
            ssh_config_file=ssh_config_file,
            ssh_known_hosts_file=ssh_known_hosts_file,
            on_init=on_init,
            on_open=on_open,
            on_close=on_close,
            transport=transport,
            transport_options=transport_options,
            channel_log=channel_log,
            channel_log_mode=channel_log_mode,
            channel_lock=channel_lock,
            logging_uid=logging_uid,
        )

    def get_prompt(self) -> str:
        """
        Convenience method to fetch prompt from the underlying Channel object

        Args:
            N/A

        Returns:
            str: string of the current prompt

        Raises:
            N/A

        """
        # assigned/typed here as decorator indicates return of Any
        prompt: str = self.channel.get_prompt()
        return prompt

    @TimeoutOpsModifier()
    def _send_command(
        self,
        command: str,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        eager: bool = False,
        timeout_ops: Optional[float] = None,
    ) -> Response:
        """
        Send a command

        Private method so that we can handle `eager` w/out having to have that argument showing up
        in all the methods that super to the "normal" send_command method as we only ever want eager
        to be used for the plural options -- i.e. send_commands not send_command!

        Args:
            command: string to send to device in privilege exec mode
            strip_prompt: strip prompt or not, defaults to True (yes, strip the prompt)
            failed_when_contains: string or list of strings indicating failure if found in response
            eager: if eager is True we do not read until prompt is seen at each command sent to the
                channel. Do *not* use this unless you know what you are doing as it is possible that
                it can make scrapli less reliable!
            timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
                the duration of the operation, value is reset to initial value after operation is
                completed

        Returns:
            Response: Scrapli Response object

        Raises:
            ScrapliValueError: if _base_transport_args is None for some reason

        """
        # decorator cares about timeout_ops, but nothing else does, assign to _ to appease linters
        _ = timeout_ops

        if not self._base_transport_args:
            # should not happen! :)
            raise ScrapliValueError("driver _base_transport_args not set for some reason")

        response = self._pre_send_command(
            host=self._base_transport_args.host,
            command=command,
            failed_when_contains=failed_when_contains,
        )
        raw_response, processed_response = self.channel.send_input(
            channel_input=command, strip_prompt=strip_prompt, eager=eager
        )
        return self._post_send_command(
            raw_response=raw_response, processed_response=processed_response, response=response
        )

    def send_command(
        self,
        command: str,
        *,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        timeout_ops: Optional[float] = None,
    ) -> Response:
        """
        Send a command

        Args:
            command: string to send to device in privilege exec mode
            strip_prompt: strip prompt or not, defaults to True (yes, strip the prompt)
            failed_when_contains: string or list of strings indicating failure if found in response
            timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
                the duration of the operation, value is reset to initial value after operation is
                completed

        Returns:
            Response: Scrapli Response object

        Raises:
            N/A

        """
        response: Response = self._send_command(
            command=command,
            strip_prompt=strip_prompt,
            failed_when_contains=failed_when_contains,
            timeout_ops=timeout_ops,
        )
        return response

    def send_commands(
        self,
        commands: List[str],
        *,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        stop_on_failed: bool = False,
        eager: bool = False,
        timeout_ops: Optional[float] = None,
    ) -> MultiResponse:
        """
        Send multiple commands

        Args:
            commands: list of strings to send to device in privilege exec mode
            strip_prompt: strip prompt or not, defaults to True (yes, strip the prompt)
            failed_when_contains: string or list of strings indicating failure if found in response
            stop_on_failed: True/False stop executing commands if a command fails, returns results
                as of current execution
            eager: if eager is True we do not read until prompt is seen at each command sent to the
                channel. Do *not* use this unless you know what you are doing as it is possible that
                it can make scrapli less reliable!
            timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
                the duration of the operation, value is reset to initial value after operation is
                completed. Note that this is the timeout value PER COMMAND sent, not for the total
                of the commands being sent!

        Returns:
            MultiResponse: Scrapli MultiResponse object

        Raises:
            N/A

        """
        responses = self._pre_send_commands(commands=commands)
        for command in commands[:-1]:
            response = self._send_command(
                command=command,
                strip_prompt=strip_prompt,
                failed_when_contains=failed_when_contains,
                timeout_ops=timeout_ops,
                eager=eager,
            )
            responses.append(response)
            if stop_on_failed and response.failed is True:
                # should we find the prompt here w/ get_prompt?? or just let subsequent operations
                # deal w/ finding that? future us problem? :)
                break
        else:
            # if we did *not* break (i.e. no failure and/or no stop_on_failed) send the last command
            # with eager = False -- this way we *always* find the prompt at the end of the commands
            response = self._send_command(
                command=commands[-1],
                strip_prompt=strip_prompt,
                failed_when_contains=failed_when_contains,
                timeout_ops=timeout_ops,
                eager=False,
            )
            responses.append(response)

        return responses

    def send_commands_from_file(
        self,
        file: str,
        *,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        stop_on_failed: bool = False,
        eager: bool = False,
        timeout_ops: Optional[float] = None,
    ) -> MultiResponse:
        """
        Send command(s) from file

        Args:
            file: string path to file
            strip_prompt: True/False strip prompt from returned output
            failed_when_contains: string or list of strings indicating failure if found in response
            stop_on_failed: True/False stop executing commands if a command fails, returns results
                as of current execution
            eager: if eager is True we do not read until prompt is seen at each command sent to the
                channel. Do *not* use this unless you know what you are doing as it is possible that
                it can make scrapli less reliable!
            timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
                the duration of the operation, value is reset to initial value after operation is
                completed. Note that this is the timeout value PER COMMAND sent, not for the total
                of the commands being sent!

        Returns:
            MultiResponse: Scrapli MultiResponse object

        Raises:
            N/A

        """
        commands = self._pre_send_from_file(file=file, caller="send_commands_from_file")

        return self.send_commands(
            commands=commands,
            strip_prompt=strip_prompt,
            failed_when_contains=failed_when_contains,
            stop_on_failed=stop_on_failed,
            eager=eager,
            timeout_ops=timeout_ops,
        )

    @TimeoutOpsModifier()
    def send_and_read(
        self,
        channel_input: str,
        *,
        expected_outputs: Optional[List[str]] = None,
        strip_prompt: bool = True,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        timeout_ops: Optional[float] = None,
        read_duration: float = 2.5,
    ) -> Response:
        """
        Send an input and read outputs.

        Unlike "normal" scrapli behavior this method reads until the prompt(normal) OR until any of
        a list of expected outputs is seen, OR until the read duration is exceeded. This method does
        not care about/understand privilege levels. This *can* cause you some potential issues if
        not used carefully!

        Args:
            channel_input: input to send to the channel; intentionally named "channel_input" instead
                of "command" or "config" due to this method not caring about privilege levels
            expected_outputs: List of outputs to look for in device response; returns as soon as any
                of the outputs are seen
            strip_prompt: True/False strip prompt from returned output
            failed_when_contains: string or list of strings indicating failure if found in response
            timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
                the duration of the operation, value is reset to initial value after operation is
                completed
            read_duration:  float duration to read for

        Returns:
            Response: Scrapli Response object

        Raises:
            ScrapliValueError: if _base_transport_args is None for some reason

        """
        # decorator cares about timeout_ops, but nothing else does, assign to _ to appease linters
        _ = timeout_ops

        if not self._base_transport_args:
            # should not happen! :)
            raise ScrapliValueError("driver _base_transport_args not set for some reason")

        response = self._pre_send_command(
            host=self._base_transport_args.host,
            command=channel_input,
            failed_when_contains=failed_when_contains,
        )
        raw_response, processed_response = self.channel.send_input_and_read(
            channel_input=channel_input,
            strip_prompt=strip_prompt,
            expected_outputs=expected_outputs,
            read_duration=read_duration,
        )
        return self._post_send_command(
            raw_response=raw_response, processed_response=processed_response, response=response
        )

    @TimeoutOpsModifier()
    def send_interactive(
        self,
        interact_events: Union[List[Tuple[str, str]], List[Tuple[str, str, bool]]],
        *,
        failed_when_contains: Optional[Union[str, List[str]]] = None,
        privilege_level: str = "",
        timeout_ops: Optional[float] = None,
        interaction_complete_patterns: Optional[List[str]] = None,
    ) -> Response:
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
            failed_when_contains: list of strings that, if present in final output, represent a
                failed command/interaction
            privilege_level: ignored in this base class; for LSP reasons for subclasses
            timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
                the duration of the operation, value is reset to initial value after operation is
                completed. Note that this is the timeout value PER COMMAND sent, not for the total
                of the commands being sent!
            interaction_complete_patterns: list of patterns, that if seen, indicate the interactive
                "session" has ended and we should exit the interactive session.

        Returns:
            Response: scrapli Response object

        Raises:
            ScrapliValueError: if _base_transport_args is None for some reason

        """
        # decorator cares about timeout_ops, but nothing else does, assign to _ to appease linters
        _ = timeout_ops
        # privilege level only matters "up" in the network driver layer
        _ = privilege_level

        if not self._base_transport_args:
            # should not happen! :)
            raise ScrapliValueError("driver _base_transport_args not set for some reason")

        response = self._pre_send_interactive(
            host=self._base_transport_args.host,
            interact_events=interact_events,
            failed_when_contains=failed_when_contains,
        )
        raw_response, processed_response = self.channel.send_inputs_interact(
            interact_events=interact_events,
            interaction_complete_patterns=interaction_complete_patterns,
        )
        return self._post_send_command(
            raw_response=raw_response, processed_response=processed_response, response=response
        )

    def read_callback(
        self,
        callbacks: List["ReadCallback"],
        initial_input: Optional[str] = None,
        read_output: bytes = b"",
        read_delay: float = 0.1,
        read_timeout: float = -1.0,
    ) -> "ReadCallbackReturnable":
        r"""
        Read from a channel and react to the output with some callback.

        This method is kind of like an "advanced" send_interactive -- the idea is simple: send some
        "stuff" to the channel (optionally), and then read from the channel. Based on the output
        do something. The callbacks is a list of `ReadCallback` which is an object containing the
        actual callback to execute, some info about when to trigger that callback (also when *not*
        to trigger that callback), as well as some attributes to control the next (if desired)
        iteration of read_callback. You could in theory do basically everything with this method by
        chaining callbacks forever, but you probably don't want to do that for real!

        Example usage:

        ```
        from scrapli.driver.core import IOSXEDriver
        from scrapli.driver.generic.base_driver import ReadCallback
        from scrapli.driver.generic.sync_driver import GenericDriver

        device = {
            "host": "rtr1",
            "auth_strict_key": False,
            "ssh_config_file": True,
        }

        def callback_one(cls: GenericDriver, read_output: str):
            cls.acquire_priv("configuration")
            cls.channel.send_return()


        def callback_two(cls: GenericDriver, read_output: str):
            print(f"previous read output : {read_output}")

            r = cls.send_command("show run | i hostname")
            print(f"result: {r.result}")


        with IOSXEDriver(**device) as conn:
            callbacks = [
                ReadCallback(
                    contains="rtr1#",
                    callback=callback_one,
                    name="call1",
                    case_insensitive=False
                ),
                ReadCallback(
                    contains_re=r"^rtr1\(config\)#",
                    callback=callback_two,
                    complete=True,
                )
            ]
            conn.read_callback(callbacks=callbacks, initial_input="show run | i hostname")
        ```

        Args:
            callbacks: a list of ReadCallback objects
            initial_input: optional string to send to "kick off" the read_callback method
            read_output: optional bytes to append any new reads to
            read_delay: sleep interval between reads
            read_timeout: value to set the `transport_timeout` to for the duration of the reading
                portion of this method. If left default (-1.0) or set to anything below 0, the
                transport timeout value will be left alone (whatever the timeout_transport value is)
                otherwise, the provided value will be temporarily set as the timeout_transport for
                duration of the reading.

        Returns:
            ReadCallbackReturnable: either None or call to read_callback again

        Raises:
            ScrapliTimeout: if the read operation times out (base don the read_timeout value) during
                the read callback check.

        """
        if initial_input is not None:
            self.channel.write(channel_input=f"{initial_input}{self.comms_return_char}")
            return self.read_callback(callbacks=callbacks, initial_input=None)

        original_transport_timeout = self.timeout_transport

        # if the read_timeout value is -1.0 or just less than 0, that indicates we should use
        # the "normal" transport timeout and not modify anything
        self.timeout_transport = read_timeout if read_timeout >= 0 else self.timeout_transport

        _read_delay = 0.1 if read_delay <= 0 else read_delay

        while True:
            try:
                read_output += self.channel.read()
            except ScrapliTimeout as exc:
                self.timeout_transport = original_transport_timeout

                raise ScrapliTimeout("timeout during read in read_callback operation") from exc

            for callback in callbacks:
                _run_callback = callback.check(read_output=read_output)

                if (
                    callback.only_once is True
                    and callback._triggered is True  # pylint: disable=W0212
                ):
                    self.logger.warning(
                        f"callback {callback.name} matches but is set to 'only_once', "
                        "skipping this callback"
                    )

                    continue

                if _run_callback is True:
                    self.logger.info(f"callback {callback.name} matched, executing")

                    self.timeout_transport = original_transport_timeout

                    callback.run(driver=self)

                    if callback.complete:
                        self.logger.debug("callback complete is true, done with read_callback")
                        return None

                    if callback.reset_output:
                        read_output = b""

                    return self.read_callback(
                        callbacks=callbacks,
                        initial_input=None,
                        read_output=read_output,
                        read_delay=callback.next_delay,
                        read_timeout=callback.next_timeout,
                    )

            time.sleep(_read_delay)
        </code>
    </pre>
</details>


#### Ancestors (in MRO)
- scrapli.driver.base.sync_driver.Driver
- scrapli.driver.base.base_driver.BaseDriver
- scrapli.driver.generic.base_driver.BaseGenericDriver
#### Descendants
- scrapli.driver.network.sync_driver.NetworkDriver
#### Methods

    

##### get_prompt
`get_prompt(self) ‑> str`

```text
Convenience method to fetch prompt from the underlying Channel object

Args:
    N/A

Returns:
    str: string of the current prompt

Raises:
    N/A
```



    

##### read_callback
`read_callback(self, callbacks: List[ForwardRef('ReadCallback')], initial_input: Optional[str] = None, read_output: bytes = b'', read_delay: float = 0.1, read_timeout: float = -1.0) ‑> ReadCallbackReturnable`

```text
Read from a channel and react to the output with some callback.

This method is kind of like an "advanced" send_interactive -- the idea is simple: send some
"stuff" to the channel (optionally), and then read from the channel. Based on the output
do something. The callbacks is a list of `ReadCallback` which is an object containing the
actual callback to execute, some info about when to trigger that callback (also when *not*
to trigger that callback), as well as some attributes to control the next (if desired)
iteration of read_callback. You could in theory do basically everything with this method by
chaining callbacks forever, but you probably don't want to do that for real!

Example usage:

```
from scrapli.driver.core import IOSXEDriver
from scrapli.driver.generic.base_driver import ReadCallback
from scrapli.driver.generic.sync_driver import GenericDriver

device = {
    "host": "rtr1",
    "auth_strict_key": False,
    "ssh_config_file": True,
}

def callback_one(cls: GenericDriver, read_output: str):
    cls.acquire_priv("configuration")
    cls.channel.send_return()


def callback_two(cls: GenericDriver, read_output: str):
    print(f"previous read output : {read_output}")

    r = cls.send_command("show run | i hostname")
    print(f"result: {r.result}")


with IOSXEDriver(**device) as conn:
    callbacks = [
        ReadCallback(
            contains="rtr1#",
            callback=callback_one,
            name="call1",
            case_insensitive=False
        ),
        ReadCallback(
            contains_re=r"^rtr1\(config\)#",
            callback=callback_two,
            complete=True,
        )
    ]
    conn.read_callback(callbacks=callbacks, initial_input="show run | i hostname")
```

Args:
    callbacks: a list of ReadCallback objects
    initial_input: optional string to send to "kick off" the read_callback method
    read_output: optional bytes to append any new reads to
    read_delay: sleep interval between reads
    read_timeout: value to set the `transport_timeout` to for the duration of the reading
        portion of this method. If left default (-1.0) or set to anything below 0, the
        transport timeout value will be left alone (whatever the timeout_transport value is)
        otherwise, the provided value will be temporarily set as the timeout_transport for
        duration of the reading.

Returns:
    ReadCallbackReturnable: either None or call to read_callback again

Raises:
    ScrapliTimeout: if the read operation times out (base don the read_timeout value) during
        the read callback check.
```



    

##### send_and_read
`send_and_read(self, channel_input: str, *, expected_outputs: Optional[List[str]] = None, strip_prompt: bool = True, failed_when_contains: Union[str, List[str], ForwardRef(None)] = None, timeout_ops: Optional[float] = None, read_duration: float = 2.5) ‑> scrapli.response.Response`

```text
Send an input and read outputs.

Unlike "normal" scrapli behavior this method reads until the prompt(normal) OR until any of
a list of expected outputs is seen, OR until the read duration is exceeded. This method does
not care about/understand privilege levels. This *can* cause you some potential issues if
not used carefully!

Args:
    channel_input: input to send to the channel; intentionally named "channel_input" instead
        of "command" or "config" due to this method not caring about privilege levels
    expected_outputs: List of outputs to look for in device response; returns as soon as any
        of the outputs are seen
    strip_prompt: True/False strip prompt from returned output
    failed_when_contains: string or list of strings indicating failure if found in response
    timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
        the duration of the operation, value is reset to initial value after operation is
        completed
    read_duration:  float duration to read for

Returns:
    Response: Scrapli Response object

Raises:
    ScrapliValueError: if _base_transport_args is None for some reason
```



    

##### send_command
`send_command(self, command: str, *, strip_prompt: bool = True, failed_when_contains: Union[str, List[str], ForwardRef(None)] = None, timeout_ops: Optional[float] = None) ‑> scrapli.response.Response`

```text
Send a command

Args:
    command: string to send to device in privilege exec mode
    strip_prompt: strip prompt or not, defaults to True (yes, strip the prompt)
    failed_when_contains: string or list of strings indicating failure if found in response
    timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
        the duration of the operation, value is reset to initial value after operation is
        completed

Returns:
    Response: Scrapli Response object

Raises:
    N/A
```



    

##### send_commands
`send_commands(self, commands: List[str], *, strip_prompt: bool = True, failed_when_contains: Union[str, List[str], ForwardRef(None)] = None, stop_on_failed: bool = False, eager: bool = False, timeout_ops: Optional[float] = None) ‑> scrapli.response.MultiResponse`

```text
Send multiple commands

Args:
    commands: list of strings to send to device in privilege exec mode
    strip_prompt: strip prompt or not, defaults to True (yes, strip the prompt)
    failed_when_contains: string or list of strings indicating failure if found in response
    stop_on_failed: True/False stop executing commands if a command fails, returns results
        as of current execution
    eager: if eager is True we do not read until prompt is seen at each command sent to the
        channel. Do *not* use this unless you know what you are doing as it is possible that
        it can make scrapli less reliable!
    timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
        the duration of the operation, value is reset to initial value after operation is
        completed. Note that this is the timeout value PER COMMAND sent, not for the total
        of the commands being sent!

Returns:
    MultiResponse: Scrapli MultiResponse object

Raises:
    N/A
```



    

##### send_commands_from_file
`send_commands_from_file(self, file: str, *, strip_prompt: bool = True, failed_when_contains: Union[str, List[str], ForwardRef(None)] = None, stop_on_failed: bool = False, eager: bool = False, timeout_ops: Optional[float] = None) ‑> scrapli.response.MultiResponse`

```text
Send command(s) from file

Args:
    file: string path to file
    strip_prompt: True/False strip prompt from returned output
    failed_when_contains: string or list of strings indicating failure if found in response
    stop_on_failed: True/False stop executing commands if a command fails, returns results
        as of current execution
    eager: if eager is True we do not read until prompt is seen at each command sent to the
        channel. Do *not* use this unless you know what you are doing as it is possible that
        it can make scrapli less reliable!
    timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
        the duration of the operation, value is reset to initial value after operation is
        completed. Note that this is the timeout value PER COMMAND sent, not for the total
        of the commands being sent!

Returns:
    MultiResponse: Scrapli MultiResponse object

Raises:
    N/A
```



    

##### send_interactive
`send_interactive(self, interact_events: Union[List[Tuple[str, str]], List[Tuple[str, str, bool]]], *, failed_when_contains: Union[str, List[str], ForwardRef(None)] = None, privilege_level: str = '', timeout_ops: Optional[float] = None, interaction_complete_patterns: Optional[List[str]] = None) ‑> scrapli.response.Response`

```text
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
    failed_when_contains: list of strings that, if present in final output, represent a
        failed command/interaction
    privilege_level: ignored in this base class; for LSP reasons for subclasses
    timeout_ops: timeout ops value for this operation; only sets the timeout_ops value for
        the duration of the operation, value is reset to initial value after operation is
        completed. Note that this is the timeout value PER COMMAND sent, not for the total
        of the commands being sent!
    interaction_complete_patterns: list of patterns, that if seen, indicate the interactive
        "session" has ended and we should exit the interactive session.

Returns:
    Response: scrapli Response object

Raises:
    ScrapliValueError: if _base_transport_args is None for some reason
```