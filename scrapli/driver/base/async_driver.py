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
