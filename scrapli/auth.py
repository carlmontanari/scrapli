"""scrapli.auth"""

from ctypes import c_char_p
from dataclasses import dataclass, field
from typing import Optional

from scrapli.exceptions import OptionsException
from scrapli.ffi_mapping import LibScrapliMapping
from scrapli.ffi_types import (
    DriverPointer,
    to_c_string,
)


@dataclass
class LookupKeyValue:
    """
    Options a "lookup" key/value pair.

    Used in conjuection with platform definition templating like `__lookup::enable` where "enable"
    is the key to "lookup" in the list of lookup key/values.

    Args:
        key: the name of the lookup key
        value: the value of the lookup key

    Returns:
        None

    Raises:
        N/A

    """

    key: str
    value: str

    _key: Optional[c_char_p] = field(init=False, default=None, repr=False)
    _value: Optional[c_char_p] = field(init=False, default=None, repr=False)

    def _get_c_strings(self) -> tuple[c_char_p, c_char_p]:
        self._key = to_c_string(self.key)
        self._value = to_c_string(self.value)

        return self._key, self._value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(key='{self.key}', value='REDACTED')"


@dataclass
class Options:  # pylint: disable=too-many-instance-attributes
    """
    Options holds auth related options to pass to the ffi layer.

    All arguments are optional, though you will almost certainly need to provide *some* -- for
    example a username and password or key.

    Args:
        username: the username to use for the connection
        password: the password to use for the connection
        private_key_path: filepath to the ssh private key to use
        private_key_passphrase: the private key passphrase if set
        lookups: a list of key/values that can be "looked up" from a connection -- used in
            conjunction with platform definition templating like `__lookup::enable` where "enable"
            is the key to "lookup" in the list of lookup key/values.
        in_session_auth_bypass: whether to bypass attempting in session authentication -- only
             applicable to "bin" and "telnet" transports.
        username_pattern: the regex pattern to use to look for a username prompt
        password_pattern: the regex pattern to use to look for a password prompt
        private_key_passphrase_pattern: the regex pattern to use to look for a passphrase prompt

    Returns:
        None

    Raises:
        N/A

    """

    username: Optional[str] = None
    password: Optional[str] = None
    private_key_path: Optional[str] = None
    private_key_passphrase: Optional[str] = None
    lookups: Optional[list[LookupKeyValue]] = None
    in_session_auth_bypass: Optional[bool] = None
    username_pattern: Optional[str] = None
    password_pattern: Optional[str] = None
    private_key_passphrase_pattern: Optional[str] = None

    _username: Optional[c_char_p] = field(init=False, default=None, repr=False)
    _password: Optional[c_char_p] = field(init=False, default=None, repr=False)
    _private_key_path: Optional[c_char_p] = field(init=False, default=None, repr=False)
    _private_key_passphrase: Optional[c_char_p] = field(init=False, default=None, repr=False)
    _username_pattern: Optional[c_char_p] = field(init=False, default=None, repr=False)
    _password_pattern: Optional[c_char_p] = field(init=False, default=None, repr=False)
    _private_key_passphrase_pattern: Optional[c_char_p] = field(
        init=False, default=None, repr=False
    )

    def apply(  # pylint: disable=too-many-branches
        self, ffi_mapping: LibScrapliMapping, ptr: DriverPointer
    ) -> None:
        """
        Applies the options to the given driver pointer.

        Should not be called directly/by users.

        Args:
            ffi_mapping: the handle to the ffi mapping singleton
            ptr: the pointer to the underlying cli or netconf object

        Returns:
            None

        Raises:
            OptionsException: if any option apply returns a non-zero return code.

        """
        if self.username is not None:
            self._username = to_c_string(self.username)

            status = ffi_mapping.options_mapping.auth.set_username(ptr, self._username)
            if status != 0:
                raise OptionsException("failed to set auth username")

        if self.password is not None:
            self._password = to_c_string(self.password)

            status = ffi_mapping.options_mapping.auth.set_password(ptr, self._password)
            if status != 0:
                raise OptionsException("failed to set auth password")

        if self.private_key_path is not None:
            self._private_key_path = to_c_string(self.private_key_path)

            status = ffi_mapping.options_mapping.auth.set_private_key_path(
                ptr, self._private_key_path
            )
            if status != 0:
                raise OptionsException("failed to set auth private key path")

        if self.private_key_passphrase is not None:
            self._private_key_passphrase = to_c_string(self.private_key_passphrase)

            status = ffi_mapping.options_mapping.auth.set_private_key_passphrase(
                ptr, self._private_key_passphrase
            )
            if status != 0:
                raise OptionsException("failed to set auth private key passphrase")

        if self.lookups is not None:
            for lookup in self.lookups:
                status = ffi_mapping.options_mapping.auth.set_lookup_key_value(
                    ptr, *lookup._get_c_strings()  # pylint: disable=protected-access
                )
                if status != 0:
                    raise OptionsException("failed to set auth lookup key/value")

        if self.in_session_auth_bypass is not None:
            status = ffi_mapping.options_mapping.auth.set_in_session_auth_bypass(ptr)
            if status != 0:
                raise OptionsException("failed to set session in session auth bypass")

        if self.username_pattern is not None:
            self._username_pattern = to_c_string(self.username_pattern)

            status = ffi_mapping.options_mapping.auth.set_username_pattern(
                ptr, self._username_pattern
            )
            if status != 0:
                raise OptionsException("failed to set auth username pattern")

        if self.password_pattern is not None:
            self._password_pattern = to_c_string(self.password_pattern)

            status = ffi_mapping.options_mapping.auth.set_password_pattern(
                ptr, self._password_pattern
            )
            if status != 0:
                raise OptionsException("failed to set auth password pattern")

        if self.private_key_passphrase_pattern is not None:
            self._private_key_passphrase_pattern = to_c_string(self.private_key_passphrase_pattern)

            status = ffi_mapping.options_mapping.auth.set_private_key_passphrase_pattern(
                ptr, self._private_key_passphrase_pattern
            )
            if status != 0:
                raise OptionsException("failed to set auth private key passphrase pattern")

    def __repr__(self) -> str:
        """
        Magic repr method for Options object

        Args:
            N/A

        Returns:
            str: repr for Options object

        Raises:
            N/A

        """
        return (
            # it will probably be "canonical" to import Options as AuthOptions, so we'll make
            # the repr do that too
            f"Auth{self.__class__.__name__}("
            f"username={self.username!r}, "
            "password=REDACTED, "
            f"private_key_path={self.private_key_path!r} "
            f"private_key_passphrase={self.private_key_passphrase!r} "
            f"lookups={self.lookups!r}) "
            f"in_session_auth_bypass={self.in_session_auth_bypass!r}) "
            f"username_pattern={self.username_pattern!r}) "
            f"password_pattern={self.password_pattern!r}) "
            f"private_key_passphrase_pattern={self.private_key_passphrase_pattern!r}) "
        )
