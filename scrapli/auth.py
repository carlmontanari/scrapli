"""scrapli.auth"""

from ctypes import Array, c_bool, c_char_p, c_size_t, c_uint16, pointer
from dataclasses import dataclass, field

from scrapli.ffi_options import DriverOptionsPointer
from scrapli.ffi_types import to_c_string


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

    _key: c_char_p | None = field(init=False, default=None, repr=False)
    _value: c_char_p | None = field(init=False, default=None, repr=False)

    def _get_c_strings(self) -> tuple[c_char_p, c_char_p]:
        self._key = to_c_string(self.key)
        self._value = to_c_string(self.value)

        return self._key, self._value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(key='{self.key}', value='REDACTED')"


@dataclass
class Options:
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
        force_in_session_auth: unconditionally force the in session auth process.
        bypass_in_session_auth: skip in session auth even if transport (telnet/bin) expect it.
        username_pattern: the regex pattern to use to look for a username prompt
        password_pattern: the regex pattern to use to look for a password prompt
        private_key_passphrase_pattern: the regex pattern to use to look for a passphrase prompt

    Returns:
        None

    Raises:
        N/A

    """

    username: str | None = None
    password: str | None = None
    private_key_path: str | None = None
    private_key_passphrase: str | None = None
    lookups: list[LookupKeyValue] | None = None
    force_in_session_auth: bool | None = None
    bypass_in_session_auth: bool | None = None
    username_pattern: str | None = None
    password_pattern: str | None = None
    private_key_passphrase_pattern: str | None = None

    _username: c_char_p | None = field(init=False, default=None, repr=False)
    _password: c_char_p | None = field(init=False, default=None, repr=False)
    _private_key_path: c_char_p | None = field(init=False, default=None, repr=False)
    _private_key_passphrase: c_char_p | None = field(init=False, default=None, repr=False)
    _username_pattern: c_char_p | None = field(init=False, default=None, repr=False)
    _password_pattern: c_char_p | None = field(init=False, default=None, repr=False)
    _private_key_passphrase_pattern: c_char_p | None = field(init=False, default=None, repr=False)

    _lookup_map_keys: Array[c_char_p] | None = field(init=False, default=None, repr=False)
    _lookup_map_key_lens: Array[c_uint16] | None = field(init=False, default=None, repr=False)
    _lookup_map_vals: Array[c_char_p] | None = field(init=False, default=None, repr=False)
    _lookup_map_val_lens: Array[c_uint16] | None = field(init=False, default=None, repr=False)

    def apply(self, *, options: DriverOptionsPointer) -> None:  # noqa: C901
        """
        Applies the options to the given options struct.

        Should not be called directly/by users.

        Args:
            options: the options struct to write set options to

        Returns:
            None

        Raises:
            N/A

        """
        if self.username is not None:
            self._username = to_c_string(self.username)

            options.contents.auth.username = self._username
            options.contents.auth.username_len = c_size_t(len(self.username))

        if self.password is not None:
            self._password = to_c_string(self.password)

            options.contents.auth.password = self._password
            options.contents.auth.password_len = c_size_t(len(self.password))

        if self.private_key_path is not None:
            self._private_key_path = to_c_string(self.private_key_path)

            options.contents.auth.private_key_path = self._private_key_path
            options.contents.auth.private_key_path_len = c_size_t(len(self.private_key_path))

        if self.private_key_passphrase is not None:
            self._private_key_passphrase = to_c_string(self.private_key_passphrase)

            options.contents.auth.private_key_passphrase = self._private_key_passphrase
            options.contents.auth.private_key_passphrase_len = c_size_t(
                len(self.private_key_passphrase)
            )

        if self.lookups is not None:
            count = len(self.lookups)

            self._lookup_map_keys = (c_char_p * count)()
            self._lookup_map_key_lens = (c_uint16 * count)()
            self._lookup_map_vals = (c_char_p * count)()
            self._lookup_map_val_lens = (c_uint16 * count)()

            for i, lookup in enumerate(self.lookups):
                k, v = lookup._get_c_strings()

                self._lookup_map_keys[i] = k
                self._lookup_map_key_lens[i] = c_uint16(len(lookup.key))

                self._lookup_map_vals[i] = v
                self._lookup_map_val_lens[i] = c_uint16(len(lookup.value))

            options.contents.auth.lookups.keys = self._lookup_map_keys
            options.contents.auth.lookups.key_lens = self._lookup_map_key_lens

            options.contents.auth.lookups.vals = self._lookup_map_vals
            options.contents.auth.lookups.val_lens = self._lookup_map_val_lens

            options.contents.auth.lookups.count = c_size_t(len(self.lookups))

        if self.force_in_session_auth is not None:
            options.contents.auth.force_in_session_auth = pointer(
                c_bool(self.force_in_session_auth)
            )

        if self.bypass_in_session_auth is not None:
            options.contents.auth.bypass_in_session_auth = pointer(
                c_bool(self.bypass_in_session_auth)
            )

        if self.username_pattern is not None:
            self._username_pattern = to_c_string(self.username_pattern)

            options.contents.auth.username_pattern = self._username_pattern
            options.contents.auth.username_pattern_len = c_size_t(len(self.username_pattern))

        if self.password_pattern is not None:
            self._password_pattern = to_c_string(self.password_pattern)

            options.contents.auth.password_pattern = self._password_pattern
            options.contents.auth.password_pattern_len = c_size_t(len(self.password_pattern))

        if self.private_key_passphrase_pattern is not None:
            self._private_key_passphrase_pattern = to_c_string(self.private_key_passphrase_pattern)

            options.contents.auth.private_key_passphrase_pattern = (
                self._private_key_passphrase_pattern
            )
            options.contents.auth.private_key_passphrase_pattern_len = c_size_t(
                len(self.private_key_passphrase_pattern)
            )

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
            f"force_in_session_auth={self.force_in_session_auth!r}) "
            f"bypass_in_session_auth={self.bypass_in_session_auth!r}) "
            f"username_pattern={self.username_pattern!r}) "
            f"password_pattern={self.password_pattern!r}) "
            f"private_key_passphrase_pattern={self.private_key_passphrase_pattern!r}) "
        )
