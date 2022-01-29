<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/sanitize.min.css" integrity="sha256-PK9q560IAAa6WVRRh76LtCaI8pjTJ2z11v0miyNNjrs=" crossorigin>
<link rel="preload stylesheet" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/10up-sanitize.css/11.0.1/typography.min.css" integrity="sha256-7l/o7C8jubJiy74VsKTidCy1yBkRtiUGbVkYBylBqUg=" crossorigin>
<link rel="stylesheet preload" as="style" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/styles/github.min.css" crossorigin>
<script defer src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/10.1.1/highlight.min.js" integrity="sha256-Uv3H6lx7dJmRfRvH8TH6kJD1TSK1aFcwgx+mdg3epi8=" crossorigin></script>
<script>window.addEventListener('DOMContentLoaded', () => hljs.initHighlighting())</script>















#Module scrapli.driver.base.async_driver

scrapli.driver.base.async_driver

<details class="source">
    <summary>
        <span>Expand source code</span>
    </summary>
    <pre>
        <code class="python">
"""scrapli.driver.base.async_driver"""
from types import TracebackType
from typing import Any, Optional, Type

from scrapli.channel import AsyncChannel
from scrapli.driver.base.base_driver import BaseDriver
from scrapli.exceptions import ScrapliValueError
from scrapli.transport import ASYNCIO_TRANSPORTS


class AsyncDriver(BaseDriver):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

        if self.transport_name not in ASYNCIO_TRANSPORTS:
            raise ScrapliValueError(
                "provided transport is *not* an asyncio transport, must use an async transport with"
                " the AsyncDriver(s)"
            )

        self.channel = AsyncChannel(
            transport=self.transport,
            base_channel_args=self._base_channel_args,
        )

    async def __aenter__(self) -> "AsyncDriver":
        """
        Enter method for context manager

        Args:
            N/A

        Returns:
            AsyncDriver: opened AsyncDriver object

        Raises:
            N/A

        """
        await self.open()
        return self

    async def __aexit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """
        Exit method to cleanup for context manager

        Args:
            exception_type: exception type being raised
            exception_value: message from exception being raised
            traceback: traceback from exception being raised

        Returns:
            None

        Raises:
            N/A

        """
        await self.close()

    async def open(self) -> None:
        """
        Open the scrapli connection

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        self._pre_open_closing_log(closing=False)

        await self.transport.open()
        self.channel.open()

        if (
            self.transport_name
            in (
                "telnet",
                "asynctelnet",
            )
            and not self.auth_bypass
        ):
            await self.channel.channel_authenticate_telnet(
                auth_username=self.auth_username, auth_password=self.auth_password
            )

        if self.on_open:
            await self.on_open(self)

        self._post_open_closing_log(closing=False)

    async def close(self) -> None:
        """
        Close the scrapli connection

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        self._post_open_closing_log(closing=True)

        if self.on_close:
            await self.on_close(self)

        self.transport.close()
        self.channel.close()

        self._post_open_closing_log(closing=True)

    async def commandeer(self, conn: "AsyncDriver", execute_on_open: bool = True) -> None:
        """
        Commandeer an existing connection

        See docstring in sync version for more details: `scrapli.driver.base.sync_driver.commandeer`

        Args:
            conn: connection to commandeer
            execute_on_open: execute the `on_open` function of the current object once the existing
                connection has been commandeered

        Returns:
            None

        Raises:
            N/A

        """
        original_logger = conn.logger
        original_transport = conn.transport
        original_transport_logger = conn.transport.logger
        original_channel_logger = conn.channel.logger
        original_channel_channel_log = conn.channel.channel_log

        self.logger = original_logger
        self.channel.logger = original_channel_logger
        self.channel.transport = original_transport
        self.transport = original_transport
        self.transport.logger = original_transport_logger

        if original_channel_channel_log is not None:
            # if the original connection had a channel log we also commandeer that; note that when
            # the new connection is closed this will also close the channel log; see docstring.
            self.channel.channel_log = original_channel_channel_log

        if execute_on_open and self.on_open is not None:
            await self.on_open(self)

    @staticmethod
    def ___getwide___() -> None:  # pragma: no cover
        """
        Dumb inside joke easter egg :)

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        wide = r"""
KKKXXXXXXXXXXNNNNNNNNNNNNNNNWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW
000000000000KKKKKKKKKKXXXXXXXXXXXXXXXXXNNXXK0Okxdoolllloodxk0KXNNWWNWWWWWWWWWWWWWWWWWWWWWWWWWWWWNNNN
kkkkkkkOOOOOOOOOOO00000000000000000000kdl:,...              ..';coxOKKKKKKKKKKKKXKKXXKKKXXXXXKKKK000
kkkkkkkOOOOOOOOOOOO000000000000000Od:,.                            .,cdOKKKKKKKKKKKK0000OOOOOOOOOOOO
kkkkkkkkOOOOOOOOOOO0000000000000kc'                                    .:d0KKKKKKKKK0KKOkOOOOOOOOOO0
kkkkkkkkOOOOOOOOOOOO00000000000o'                                         ,o0KKKKKKKKKKOkOOOOOOOOO00
kkkkkkkkOOOOOOOOOOOOO000000000o.                                            ;kKKKKKKKKKOkOOOOOOOOO00
OOOOOOOOOO0000000000000000K0Kk'                                              'xKKKKKKKKOkOOOOOOOOO00
KKKKKKKKKXXXXXXXXXXXXXXNNNNNNd.                                               cXNNNNNNNK0000O00O0000
KKKKKKKKKXXXXXXXXXXXXNNNNNNNXl        ...............                         :XWWWWWWWX000000000000
KKKKKKKKKXXXXXXXXXXXXXXNNNNNXc     ...''',,,,,,;;,,,,,,'''......             .xWWWWWWWWX000000000000
KKKKKKKKKKKXXXXXXXXXXXXXNNNNK;    ...',,,,;;;;;;;:::::::;;;;;;,,'.          .oNWWWWWWWNK000000OOOO00
KKKKKKKKKKKKXXXXXXXXXXXXXXXN0,  ...'',,,;;;;;;:::::::::::::::;;;;,'.       .dNWWWWWWWWNK0000OOOOOOOO
0000KKKKKKKKKKKKKXXXXXXXXXXN0, ..'',,,,;;;;;;:::::::::::::::::;;;;,,..    ;ONNNNNWWWWWNK00OOOOOOOOOO
kkkkkkOOOOOOOOOOOOOOOOOOO000k; ..,,,,,,'',,;;::::::::::::::::;;;;;;,'.  .lOKKKKXXKXXKK0OOOOOOOOOOOOO
xxxkkkkkkkkkkkkkkkkkkOOOOkdll;..',,,,,,,''...';::ccccc:::::::::;;;;;,...o0000000000000OkkOOOkkOOOOOO
xxxxxxkkkkkkkkkkkkkkkkkkOd:;;,..,;;;;;;;;;;,'',,;:ccccccccc:::;;;;;;,..cO0000000000000Oxkkkkkkkkkkkk
xxxxxxxxkkkkkkkkkkkkkkkkkl:;;,'';;;;;,'''''',,,,,;::ccc::;,,'.'''',;,,lO00000000000000kxkkkkkkkkkkkk
xxxxxxxxkkkkkkkkkkkkkkkkko::;'';;;;;;,''....,'',,,,;:c:;,,'''',,;;;;,:x00000000000000Okxkkkkkkkkkkkk
xxxxxxxxxxkkkkkkkkkkkkkkkxl;,,;;;;:::;;;,,,,,,,,,,,,:c:;,'....''',;;,;cxO000000000000Okxkkkkkkkkkkkk
kkkkOOOOOOOOOOOOOO00000000x:;;;;;:::c::::::;;;;;;;;;:c:;,,,,'',,',;:::lOKKKKKKXXXXXXKKOkkkkkkkkkkkkk
000000000000000KKKKKKKKKKK0dc;,;;:::ccccccc::::;;;;;:cc:;;;;:::::::::lOXXXXXNNNNNNNNXX0Okkkkkkkkkkkk
OO00000000000000000KKKKKKKK0d::;;;::ccccccccc:;;;;;;;:c:;::ccccccc::cOXXXXXXXXXNNNNNXX0kkkkkkkkkkkkk
OOO00000000000000000000KKKKKOxxc;;;::ccccccc:;;;;;;;:ccc:::cccllcc;:kKXXXXXXXXXXXXXXXKOkkkkkkkkkkkkk
OOOOO00000000000000000000KKK0kdl;;;;;:ccccc::;,,,,;;:clc:::cclllcc:oKXXXXXXXXXXXXXXXXKOkkkkkkkkkkkkk
OOOOOOO0000000000000000Okxdlc;,,;;::;;::cc::;;,,,,,;:::;;:cccccc::clxkO00KKKKKKKKKXKK0kkkkkkkkkkkxkk
kkkkkkkkkkkkkkkkkkkxdoc:,''.....,;:::;;;::;;;;;;;;;;;;;;;:ccc:::;,',;;:clodxkOOOOOOOOkxxxxxxxxxxxxxx
ddddddddddddddoolc;,'''..........,;;:;;;::;,,,,,;;;;;::::::c:::;'.',,;;;;;::clodxkkkkxdxxxxxxxxxxxxx
dddddddoolc::;,'''.......      ..',;;;;;;;;,'........',;::::::;;,,;;;;;;;;:::::ccloddddxxxxxxxxxxxxx
dollc:;,,''.........         ..'''',,,,;;;;;,'''.....'',::::;,,;;;::::;;,,;;;;;;;;;::cldxxxxxxdxxdxx
l;'''.''......             ..'',,''',,,,;;;::;;,,,,,,;;::;;'.....',;;,,''',,,,,,'',,,',:odxddddddddd
.............             .'',,,,,''',,,;;;;::::;::::::;;;........'''''''..'.....,,'...';cdddddddddd
. .......                .',,,,,;,,'',,,,;;;::::::::::;;cc. .....''...'''.......','......':odxdddddd
   ...                  .',,;;;;;;,'',;;,,,;;;::::::::;cxo....................''''.......'';lddddddd
    ..                  .,;,;;;;;;,,,',;;;,,,,;;;;;;;;:dKO:..................''''.. .......',cdddddd
                         ,:;;;;;,,,,;,,;::;,,,,,;::::::dK0c..................'''..  ........',codddd
                         .;:;;;;;,,;;;,,;:;;:;,,;:::::clc,...   ...........'''.... ....  .....':oddd
                          .',;;;;;;;;;,,;:;;;;,;::::::;'......       ......'.........   .....'',cood
                            ..,;;;;;;;;;;;:;;;;:::::;'.    .         ..............       ...''',:od
                              ..',;;;;:;;;:::::::,,'.              ...............        ....''.':o
                                 ...',,;;,,;,,'..                 ...............        ..  .....'c
               __              _     __....                      ................     ....   ......'
   ____ ____  / /_   _      __(_)___/ /__                    ..............   ..    ...     .......
  / __ `/ _ \/ __/  | | /| / / / __  / _ \                 ................    .             ......
 / /_/ /  __/ /_    | |/ |/ / / /_/ /  __/                .................                  ......
 \__, /\___/\__/    |__/|__/_/\__,_/\___/                  ...............                   ......
/____/                                                     ...............  ..             ........
"""
        print(wide)
        </code>
    </pre>
</details>




## Classes

### AsyncDriver


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
class AsyncDriver(BaseDriver):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)

        if self.transport_name not in ASYNCIO_TRANSPORTS:
            raise ScrapliValueError(
                "provided transport is *not* an asyncio transport, must use an async transport with"
                " the AsyncDriver(s)"
            )

        self.channel = AsyncChannel(
            transport=self.transport,
            base_channel_args=self._base_channel_args,
        )

    async def __aenter__(self) -> "AsyncDriver":
        """
        Enter method for context manager

        Args:
            N/A

        Returns:
            AsyncDriver: opened AsyncDriver object

        Raises:
            N/A

        """
        await self.open()
        return self

    async def __aexit__(
        self,
        exception_type: Optional[Type[BaseException]],
        exception_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """
        Exit method to cleanup for context manager

        Args:
            exception_type: exception type being raised
            exception_value: message from exception being raised
            traceback: traceback from exception being raised

        Returns:
            None

        Raises:
            N/A

        """
        await self.close()

    async def open(self) -> None:
        """
        Open the scrapli connection

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        self._pre_open_closing_log(closing=False)

        await self.transport.open()
        self.channel.open()

        if (
            self.transport_name
            in (
                "telnet",
                "asynctelnet",
            )
            and not self.auth_bypass
        ):
            await self.channel.channel_authenticate_telnet(
                auth_username=self.auth_username, auth_password=self.auth_password
            )

        if self.on_open:
            await self.on_open(self)

        self._post_open_closing_log(closing=False)

    async def close(self) -> None:
        """
        Close the scrapli connection

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        self._post_open_closing_log(closing=True)

        if self.on_close:
            await self.on_close(self)

        self.transport.close()
        self.channel.close()

        self._post_open_closing_log(closing=True)

    async def commandeer(self, conn: "AsyncDriver", execute_on_open: bool = True) -> None:
        """
        Commandeer an existing connection

        See docstring in sync version for more details: `scrapli.driver.base.sync_driver.commandeer`

        Args:
            conn: connection to commandeer
            execute_on_open: execute the `on_open` function of the current object once the existing
                connection has been commandeered

        Returns:
            None

        Raises:
            N/A

        """
        original_logger = conn.logger
        original_transport = conn.transport
        original_transport_logger = conn.transport.logger
        original_channel_logger = conn.channel.logger
        original_channel_channel_log = conn.channel.channel_log

        self.logger = original_logger
        self.channel.logger = original_channel_logger
        self.channel.transport = original_transport
        self.transport = original_transport
        self.transport.logger = original_transport_logger

        if original_channel_channel_log is not None:
            # if the original connection had a channel log we also commandeer that; note that when
            # the new connection is closed this will also close the channel log; see docstring.
            self.channel.channel_log = original_channel_channel_log

        if execute_on_open and self.on_open is not None:
            await self.on_open(self)

    @staticmethod
    def ___getwide___() -> None:  # pragma: no cover
        """
        Dumb inside joke easter egg :)

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        wide = r"""
KKKXXXXXXXXXXNNNNNNNNNNNNNNNWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW
000000000000KKKKKKKKKKXXXXXXXXXXXXXXXXXNNXXK0Okxdoolllloodxk0KXNNWWNWWWWWWWWWWWWWWWWWWWWWWWWWWWWNNNN
kkkkkkkOOOOOOOOOOO00000000000000000000kdl:,...              ..';coxOKKKKKKKKKKKKXKKXXKKKXXXXXKKKK000
kkkkkkkOOOOOOOOOOOO000000000000000Od:,.                            .,cdOKKKKKKKKKKKK0000OOOOOOOOOOOO
kkkkkkkkOOOOOOOOOOO0000000000000kc'                                    .:d0KKKKKKKKK0KKOkOOOOOOOOOO0
kkkkkkkkOOOOOOOOOOOO00000000000o'                                         ,o0KKKKKKKKKKOkOOOOOOOOO00
kkkkkkkkOOOOOOOOOOOOO000000000o.                                            ;kKKKKKKKKKOkOOOOOOOOO00
OOOOOOOOOO0000000000000000K0Kk'                                              'xKKKKKKKKOkOOOOOOOOO00
KKKKKKKKKXXXXXXXXXXXXXXNNNNNNd.                                               cXNNNNNNNK0000O00O0000
KKKKKKKKKXXXXXXXXXXXXNNNNNNNXl        ...............                         :XWWWWWWWX000000000000
KKKKKKKKKXXXXXXXXXXXXXXNNNNNXc     ...''',,,,,,;;,,,,,,'''......             .xWWWWWWWWX000000000000
KKKKKKKKKKKXXXXXXXXXXXXXNNNNK;    ...',,,,;;;;;;;:::::::;;;;;;,,'.          .oNWWWWWWWNK000000OOOO00
KKKKKKKKKKKKXXXXXXXXXXXXXXXN0,  ...'',,,;;;;;;:::::::::::::::;;;;,'.       .dNWWWWWWWWNK0000OOOOOOOO
0000KKKKKKKKKKKKKXXXXXXXXXXN0, ..'',,,,;;;;;;:::::::::::::::::;;;;,,..    ;ONNNNNWWWWWNK00OOOOOOOOOO
kkkkkkOOOOOOOOOOOOOOOOOOO000k; ..,,,,,,'',,;;::::::::::::::::;;;;;;,'.  .lOKKKKXXKXXKK0OOOOOOOOOOOOO
xxxkkkkkkkkkkkkkkkkkkOOOOkdll;..',,,,,,,''...';::ccccc:::::::::;;;;;,...o0000000000000OkkOOOkkOOOOOO
xxxxxxkkkkkkkkkkkkkkkkkkOd:;;,..,;;;;;;;;;;,'',,;:ccccccccc:::;;;;;;,..cO0000000000000Oxkkkkkkkkkkkk
xxxxxxxxkkkkkkkkkkkkkkkkkl:;;,'';;;;;,'''''',,,,,;::ccc::;,,'.'''',;,,lO00000000000000kxkkkkkkkkkkkk
xxxxxxxxkkkkkkkkkkkkkkkkko::;'';;;;;;,''....,'',,,,;:c:;,,'''',,;;;;,:x00000000000000Okxkkkkkkkkkkkk
xxxxxxxxxxkkkkkkkkkkkkkkkxl;,,;;;;:::;;;,,,,,,,,,,,,:c:;,'....''',;;,;cxO000000000000Okxkkkkkkkkkkkk
kkkkOOOOOOOOOOOOOO00000000x:;;;;;:::c::::::;;;;;;;;;:c:;,,,,'',,',;:::lOKKKKKKXXXXXXKKOkkkkkkkkkkkkk
000000000000000KKKKKKKKKKK0dc;,;;:::ccccccc::::;;;;;:cc:;;;;:::::::::lOXXXXXNNNNNNNNXX0Okkkkkkkkkkkk
OO00000000000000000KKKKKKKK0d::;;;::ccccccccc:;;;;;;;:c:;::ccccccc::cOXXXXXXXXXNNNNNXX0kkkkkkkkkkkkk
OOO00000000000000000000KKKKKOxxc;;;::ccccccc:;;;;;;;:ccc:::cccllcc;:kKXXXXXXXXXXXXXXXKOkkkkkkkkkkkkk
OOOOO00000000000000000000KKK0kdl;;;;;:ccccc::;,,,,;;:clc:::cclllcc:oKXXXXXXXXXXXXXXXXKOkkkkkkkkkkkkk
OOOOOOO0000000000000000Okxdlc;,,;;::;;::cc::;;,,,,,;:::;;:cccccc::clxkO00KKKKKKKKKXKK0kkkkkkkkkkkxkk
kkkkkkkkkkkkkkkkkkkxdoc:,''.....,;:::;;;::;;;;;;;;;;;;;;;:ccc:::;,',;;:clodxkOOOOOOOOkxxxxxxxxxxxxxx
ddddddddddddddoolc;,'''..........,;;:;;;::;,,,,,;;;;;::::::c:::;'.',,;;;;;::clodxkkkkxdxxxxxxxxxxxxx
dddddddoolc::;,'''.......      ..',;;;;;;;;,'........',;::::::;;,,;;;;;;;;:::::ccloddddxxxxxxxxxxxxx
dollc:;,,''.........         ..'''',,,,;;;;;,'''.....'',::::;,,;;;::::;;,,;;;;;;;;;::cldxxxxxxdxxdxx
l;'''.''......             ..'',,''',,,,;;;::;;,,,,,,;;::;;'.....',;;,,''',,,,,,'',,,',:odxddddddddd
.............             .'',,,,,''',,,;;;;::::;::::::;;;........'''''''..'.....,,'...';cdddddddddd
. .......                .',,,,,;,,'',,,,;;;::::::::::;;cc. .....''...'''.......','......':odxdddddd
   ...                  .',,;;;;;;,'',;;,,,;;;::::::::;cxo....................''''.......'';lddddddd
    ..                  .,;,;;;;;;,,,',;;;,,,,;;;;;;;;:dKO:..................''''.. .......',cdddddd
                         ,:;;;;;,,,,;,,;::;,,,,,;::::::dK0c..................'''..  ........',codddd
                         .;:;;;;;,,;;;,,;:;;:;,,;:::::clc,...   ...........'''.... ....  .....':oddd
                          .',;;;;;;;;;,,;:;;;;,;::::::;'......       ......'.........   .....'',cood
                            ..,;;;;;;;;;;;:;;;;:::::;'.    .         ..............       ...''',:od
                              ..',;;;;:;;;:::::::,,'.              ...............        ....''.':o
                                 ...',,;;,,;,,'..                 ...............        ..  .....'c
               __              _     __....                      ................     ....   ......'
   ____ ____  / /_   _      __(_)___/ /__                    ..............   ..    ...     .......
  / __ `/ _ \/ __/  | | /| / / / __  / _ \                 ................    .             ......
 / /_/ /  __/ /_    | |/ |/ / / /_/ /  __/                .................                  ......
 \__, /\___/\__/    |__/|__/_/\__,_/\___/                  ...............                   ......
/____/                                                     ...............  ..             ........
"""
        print(wide)
        </code>
    </pre>
</details>


#### Ancestors (in MRO)
- scrapli.driver.base.base_driver.BaseDriver
#### Descendants
- scrapli.driver.generic.async_driver.AsyncGenericDriver
#### Methods

    

##### close
`close(self) ‑> None`

```text
Close the scrapli connection

Args:
    N/A

Returns:
    None

Raises:
    N/A
```



    

##### commandeer
`commandeer(self, conn: AsyncDriver, execute_on_open: bool = True) ‑> None`

```text
Commandeer an existing connection

See docstring in sync version for more details: `scrapli.driver.base.sync_driver.commandeer`

Args:
    conn: connection to commandeer
    execute_on_open: execute the `on_open` function of the current object once the existing
        connection has been commandeered

Returns:
    None

Raises:
    N/A
```



    

##### open
`open(self) ‑> None`

```text
Open the scrapli connection

Args:
    N/A

Returns:
    None

Raises:
    N/A
```