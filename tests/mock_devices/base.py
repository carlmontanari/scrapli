"""mock_devices.base"""
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

import asyncssh


class BaseSSHServerSession(ABC, asyncssh.SSHServerSession):  # type: ignore
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        SSH Server Session class

        Inherits from asyncssh and provides some extra context/setup for the mock network devices

        Args:
            args: positional args to pass to base class
            kwargs: keyword args to pass to base class

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        super().__init__(*args, **kwargs)

        self._chan: asyncssh.editor.SSHLineEditorChannel

        self._hide_input = False
        self._interacting = False

        self.terminal_length = 80
        self.terminal_width = 80

        self.priv_levels: Dict[str, str] = {}
        self.priv_level = ""
        self.invalid_input = ""
        self.paging_prompt = ""

        self.command_mapper: Dict[Callable[..., Any], List[str]] = {
            self.handle_open: [],
            self.handle_close: [],
            self.handle_priv: [],
            self.handle_show: [],
            self.handle_interactive: [],
        }

        self.show_command_output = ""

        self._redirect_to_handler: Optional[Callable[..., Any]] = None

    def connection_made(self, chan: asyncssh.editor.SSHLineEditorChannel) -> None:
        """
        SSH Connection made!

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self._chan = chan

    def shell_requested(self) -> bool:
        """
        Handle shell requested; always return True

        Args:
            N/A

        Returns:
            bool: always True!

        Raises:
            N/A

        """
        return True

    def session_started(self) -> None:
        """
        SSH session started

        Initial SSH session started; present user with the priv level set at priv_level

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self._chan.write(self.priv_levels.get(self.priv_level))

    @abstractmethod
    def handle_open(self, channel_input: str) -> None:
        """
        Handle "open" commands sent to the ssh channel

        Args:
            channel_input: command sent to the ssh channel

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """

    @abstractmethod
    def handle_close(self, channel_input: str) -> None:
        """
        Handle "close" commands sent to the ssh channel

        Args:
            channel_input: command sent to the ssh channel

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """

    @abstractmethod
    def handle_priv(self, channel_input: str) -> None:
        """
        Handle "privilege" commands sent to the ssh channel

        Args:
            channel_input: command sent to the ssh channel

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """

    def handle_invalid(self, channel_input: str) -> None:
        """
        Handle "invalid" commands sent to the ssh channel

        Args:
            channel_input: command sent to the ssh channel

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        _ = channel_input  # maybe care about this in the future or for some platforms
        self._chan.write(self.invalid_input)
        self.repaint_prompt()

    def handle_show(self, channel_input: str) -> None:
        """
        Handle "show" commands sent to the ssh channel

        Args:
            channel_input: command sent to the ssh channel

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        _ = channel_input  # we dont care about this, we only support one show command anyway :)
        if self.terminal_length:
            channel_output = "\n".join(
                self.show_command_output.splitlines()[: self.terminal_length]
            )
            channel_output += self.paging_prompt
        else:
            channel_output = self.show_command_output
            channel_output += f"\n{self.priv_levels.get(self.priv_level)}"
        self._chan.write(channel_output)

    @abstractmethod
    def handle_interactive(self, channel_input: str) -> None:
        """
        Handle "interactive" commands sent to the ssh channel

        Args:
            channel_input: command sent to the ssh channel

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """

    def repaint_prompt(self) -> None:
        """
        Paint the prompt to the ssh channel

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self._chan.write(self.priv_levels.get(self.priv_level))

    @abstractmethod
    def data_received(self, data: str, datatype: None) -> None:
        """
        Handle data received on ssh channel

        Args:
            data: string of data sent to channel
            datatype: dunno! in base class though :)

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """

    def eof_received(self) -> None:
        """
        Handle eof

        Args:
            N/A

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self._chan.exit(0)

    def break_received(self, msec: float) -> None:
        """
        Handle break

        Args:
            msec: dunno, but in base class implementation :)

        Returns:
            N/A  # noqa: DAR202

        Raises:
            N/A

        """
        self.eof_received()


class BaseServer(asyncssh.SSHServer):  # type: ignore
    def session_requested(self) -> asyncssh.SSHServerSession:
        """
        Session requested; return ServerSession object

        `ServerSession` set in `run` to be the appropriate SSHServerSession type for a given
        platform, i.e. `IOSXESSHServerSession`

        Args:
            N/A

        Returns:
            asyncssh.SSHServerSession: SSHServerSession

        Raises:
            N/A

        """
        return self.ServerSession()

    def begin_auth(self, username: str) -> bool:
        """
        Begin auth; always returns True

        Args:
            username: username for auth

        Returns:
            bool: always True

        Raises:
            N/A

        """
        return True

    def password_auth_supported(self) -> bool:
        """
        Password auth supported; always return True

        Args:
            N/A

        Returns:
            bool: always True

        Raises:
            N/A

        """
        return True

    def public_key_auth_supported(self) -> bool:
        """
        Public key auth supported; always return True

        Args:
            N/A

        Returns:
            bool: always True

        Raises:
            N/A

        """
        return True

    def validate_password(self, username: str, password: str) -> bool:
        """
        Validate provided username/password

        Args:
            username: username to check for auth
            password: password to check for auth

        Returns:
            bool: True if user/password is correct (scrapli/scrapli)

        Raises:
            N/A

        """
        if username == password == "scrapli":
            return True
        return False

    def validate_public_key(
        self, username: str, key: asyncssh.rsa._RSAKey  # pylint: disable=W0212
    ) -> bool:
        """
        Validate provided public key

        Args:
            username: username to check for auth
            key: asyncssh RSAKey to check for auth

        Returns:
            bool: True if ssh key is correct

        Raises:
            N/A

        """
        if (
            username == "scrapli"
            and key.get_fingerprint() == "SHA256:rb1CVtQCkWBAzm1AxV7xR7BLBawUwFUlUVFVu+QYQBM"
        ):
            return True
        return False
