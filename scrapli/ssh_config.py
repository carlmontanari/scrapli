"""scrapli.ssh_config"""
import os
import re
import shlex
import sys
from copy import deepcopy
from typing import Dict, Optional

from scrapli.exceptions import ScrapliTypeError

if sys.version_info >= (3, 8):
    Match = re.Match
else:
    from typing import Match  # pragma:  no cover

HOST_ATTRS = (
    "port",
    "user",
    "address_family",
    "bind_address",
    "connect_timeout",
    "identities_only",
    "identity_file",
    "keyboard_interactive",
    "password_authentication",
    "preferred_authentication",
)


class SSHConfig:
    def __init__(self, ssh_config_file: str) -> None:
        """
        Initialize SSHConfig Object

        Parse OpenSSH config file

        Try to load the following data for all entries in config file:
            Host
            HostName
            Port
            User
            *AddressFamily
            *BindAddress
            *ConnectTimeout
            IdentitiesOnly
            IdentityFile
            *KbdInteractiveAuthentication
            *PasswordAuthentication
            *PreferredAuthentications

        * items are mostly ready to load but are unused in scrapli right now so are not being set
        at this point.

        NOTE: this does *not* accept duplicate "*" entries -- the final "*" entry will overwrite any
        previous "*" entries. In general for system transport this shouldn't matter much because
        scrapli only cares about parsing the config file to see if a key (any key) exists for a
        given host (we care about that because ideally we use "pipes" auth, but this is only an
        option if we have a key to auth with).

        Args:
            ssh_config_file: string path to ssh configuration file

        Returns:
            None

        Raises:
            ScrapliTypeError: if non-string value provided for ssh_config_file

        """
        if not isinstance(ssh_config_file, str):
            raise ScrapliTypeError(f"`ssh_config_file` expected str, got {type(ssh_config_file)}")

        self.ssh_config_file = os.path.expanduser(ssh_config_file)
        if self.ssh_config_file:
            with open(self.ssh_config_file, "r") as f:
                self.ssh_config = f.read()
            self.hosts = self._parse()
            if not self.hosts:
                self.hosts = {}
            if "*" not in self.hosts.keys():
                self.hosts["*"] = Host()
                self.hosts["*"].hosts = "*"
        else:
            self.hosts = {}
            self.hosts["*"] = Host()
            self.hosts["*"].hosts = "*"

        # finally merge all args from less specific hosts into the more specific hosts, preserving
        # the options from the more specific hosts of course
        self._merge_hosts()

    def __str__(self) -> str:
        """
        Magic str method for SSHConfig class

        Args:
            N/A

        Returns:
            str: string representation of object

        Raises:
            N/A

        """
        return "SSHConfig Object"

    def __repr__(self) -> str:
        """
        Magic repr method for SSHConfig class

        Args:
            N/A

        Returns:
            str: repr for class object

        Raises:
            N/A

        """
        class_dict = self.__dict__.copy()
        del class_dict["ssh_config"]
        return f"SSHConfig {class_dict}"

    def __bool__(self) -> bool:
        """
        Magic bool method; return True if ssh_config_file

        Args:
            N/A

        Returns:
            bool: True/False if ssh_config_file

        Raises:
            N/A

        """
        if self.ssh_config:
            return True
        return False

    @staticmethod
    def _strip_comments(line: str) -> str:
        """
        Strip out comments from ssh config file lines

        Args:
            line: to strip comments from

        Returns:
            str: rejoined ssh config file line after stripping comments

        Raises:
            N/A

        """
        line = " ".join(shlex.split(line, comments=True))
        return line

    def _parse(self) -> Dict[str, "Host"]:
        """
        Parse SSH configuration file

        Args:
            N/A

        Returns:
            discovered_hosts: dict of host objects discovered in ssh config file

        Raises:
            N/A

        """
        # uncomment next line and handle global patterns (stuff before hosts) at some point
        # global_config_pattern = re.compile(r"^.*?\b(?=host)", flags=re.I | re.S)
        # use word boundaries with a positive lookahead to get everything between the word host
        # need to do this as whitespace/formatting is not really a thing in ssh_config file
        # match host\s to ensure we don't pick up hostname and split things there accidentally
        host_pattern = re.compile(r"\bhost.*?\b(?=host\s|\s+$|$)", flags=re.I | re.S)
        host_entries = re.findall(pattern=host_pattern, string=self.ssh_config)

        discovered_hosts: Dict[str, Host] = {}
        if not host_entries:
            return discovered_hosts

        # do we need to add whitespace between match and end of line to ensure we match correctly?
        hosts_pattern = re.compile(r"^\s*host[\s=]+(.*)$", flags=re.I | re.M)
        hostname_pattern = re.compile(r"^\s*hostname[\s=]+([\w.-]*)$", flags=re.I | re.M)
        port_pattern = re.compile(r"^\s*port[\s=]+([\d]*)$", flags=re.I | re.M)
        user_pattern = re.compile(r"^\s*user[\s=]+([\w]*)$", flags=re.I | re.M)
        # address_family_pattern = None
        # bind_address_pattern = None
        # connect_timeout_pattern = None
        identities_only_pattern = re.compile(
            r"^\s*identitiesonly[\s=]+(yes|no)$", flags=re.I | re.M
        )
        identity_file_pattern = re.compile(
            r"^\s*identityfile[\s=]+([\w.\/\@~-]*)$", flags=re.I | re.M
        )
        # keyboard_interactive_pattern = None
        # password_authentication_pattern = None
        # preferred_authentication_pattern = None

        for host_entry in host_entries:
            host = Host()
            host_line = re.search(pattern=hosts_pattern, string=host_entry)
            if isinstance(host_line, Match):
                host.hosts = self._strip_comments(host_line.groups()[0])
            else:
                host.hosts = ""
            hostname = re.search(pattern=hostname_pattern, string=host_entry)
            if isinstance(hostname, Match):
                host.hostname = self._strip_comments(hostname.groups()[0])
            port = re.search(pattern=port_pattern, string=host_entry)
            if isinstance(port, Match):
                host.port = int(self._strip_comments(port.groups()[0]))
            user = re.search(pattern=user_pattern, string=host_entry)
            if isinstance(user, Match):
                host.user = self._strip_comments(user.groups()[0])
            # address_family = re.search(user_pattern, host_entry[0])
            # bind_address = re.search(user_pattern, host_entry[0])
            # connect_timeout = re.search(user_pattern, host_entry[0])
            identities_only = re.search(pattern=identities_only_pattern, string=host_entry)
            if isinstance(identities_only, Match):
                host.identities_only = self._strip_comments(identities_only.groups()[0])
            identity_file = re.search(pattern=identity_file_pattern, string=host_entry)
            if isinstance(identity_file, Match):
                host.identity_file = os.path.expanduser(
                    self._strip_comments(identity_file.groups()[0])
                )
            # keyboard_interactive = re.search(user_pattern, host_entry[0])
            # password_authentication = re.search(user_pattern, host_entry[0])
            # preferred_authentication = re.search(user_pattern, host_entry[0])
            discovered_hosts[host.hosts] = host
        return discovered_hosts

    def _merge_hosts(self) -> None:
        """
        Merge less specific host pattern data into a given host

        Args:
            N/A

        Returns:
            None

        Raises:
            N/A

        """
        for host in self.hosts:
            _current_hosts = deepcopy(self.hosts)
            while True:
                fuzzy_match = self._lookup_fuzzy_match(host=host, hosts=_current_hosts)
                for attr in HOST_ATTRS:
                    if not getattr(self.hosts[host], attr):
                        setattr(self.hosts[host], attr, getattr(self.hosts[fuzzy_match], attr))
                try:
                    _current_hosts.pop(fuzzy_match)
                except KeyError:
                    # this means we hit the "*" entry twice and we can bail out
                    break

    def _lookup_fuzzy_match(self, host: str, hosts: Optional[Dict[str, "Host"]] = None) -> str:
        """
        Look up fuzzy matched hosts

        Get the best match ssh config Host entry for a given host; this allows for using
        the splat and question-mark operators in ssh config file

        Args:
            host: host to lookup in discovered_hosts dict
            hosts: hosts dict to operate on; used for passing in partial dict of hosts while
                performing merge operations

        Returns:
            str: Nearest match (if applicable) host or `*` if none found

        Raises:
            N/A

        """
        hosts = hosts or self.hosts

        possible_matches = []
        for host_entry in hosts.keys():
            host_list = host_entry.split()
            for host_pattern in host_list:
                # replace periods with literal period
                # replace asterisk (match 0 or more things) with appropriate regex
                # replace question mark (match one thing) with appropriate regex
                cleaned_host_pattern = (
                    host_pattern.replace(".", r"\.").replace("*", r"(.*)").replace("?", r"(.)")
                )
                # compile with case insensitive
                search_pattern = re.compile(cleaned_host_pattern, flags=re.I)
                result = re.search(pattern=search_pattern, string=host)
                # if we get a result, append it and the original pattern to the possible matches
                if result:
                    possible_matches.append((result, host_entry))

        # initialize a None best match
        current_match = None
        for match in possible_matches:
            if current_match is None:
                current_match = match
            # count how many chars were replaced to get regex to work
            chars_replaced = 0
            for start_char, end_char in match[0].regs[1:]:
                chars_replaced += end_char - start_char
            # count how many chars were replaced to get regex to work on best match
            best_match_chars_replaced = 0
            for start_char, end_char in current_match[0].regs[1:]:
                best_match_chars_replaced += end_char - start_char
            # if match replaced less chars than "best_match" we have a new best match
            if chars_replaced < best_match_chars_replaced:
                current_match = match
        if current_match is not None:
            best_match = current_match[1]
        else:
            best_match = "*"
        return best_match

    def lookup(self, host: str) -> "Host":
        """
        Lookup a given host

        Args:
            host: host to lookup in discovered_hosts dict

        Returns:
            Host: best matched host from parsed ssh config file hosts, "*" if no better match found

        Raises:
            N/A

        """
        # return exact 1:1 match if exists
        if host in self.hosts.keys():
            return self.hosts[host]
        # return match if given host is an exact match for a host entry
        for host_entry in self.hosts:
            host_list = host_entry.split()
            if host in host_list:
                return self.hosts[host_entry]
        # otherwise need to select the most correct host entry
        fuzzy_match = self._lookup_fuzzy_match(host)
        return self.hosts[fuzzy_match]


class Host:
    def __init__(self) -> None:
        """
        Host Object

        Create a Host object based on ssh config file information
        """
        self.hosts: str = ""
        self.hostname: Optional[str] = None
        self.port: Optional[int] = None
        self.user: str = ""
        self.address_family: Optional[str] = None
        self.bind_address: Optional[str] = None
        self.connect_timeout: Optional[str] = None
        self.identities_only: Optional[str] = None
        self.identity_file: Optional[str] = None
        self.keyboard_interactive: Optional[str] = None
        self.password_authentication: Optional[str] = None
        self.preferred_authentication: Optional[str] = None

    def __str__(self) -> str:
        """
        Magic str method for HostEntry class

        Args:
            N/A

        Returns:
            str: string for class object

        Raises:
            N/A

        """
        return f"Host: {self.hosts}"

    def __repr__(self) -> str:
        """
        Magic repr method for HostEntry class

        Args:
            N/A

        Returns:
            str: repr for class object

        Raises:
            N/A

        """
        class_dict = self.__dict__.copy()
        return f"Host {class_dict}"


class SSHKnownHosts:
    def __init__(self, ssh_known_hosts_file: str) -> None:
        """
        Initialize SSHKnownHosts Object

        Parse OpenSSH known hosts file

        Try to load the following data for all entries in known hosts file:
            Host
            Key Type
            Public Key

        Args:
            ssh_known_hosts_file: string path to ssh known hosts file

        Returns:
            None

        Raises:
            TypeError: if non-string value provided for ssh_known_hosts

        """
        if not isinstance(ssh_known_hosts_file, str):
            raise TypeError(
                f"`ssh_known_hosts_file` expected str, got {type(ssh_known_hosts_file)}"
            )

        self.ssh_known_hosts_file = os.path.expanduser(ssh_known_hosts_file)
        if self.ssh_known_hosts_file:
            with open(self.ssh_known_hosts_file, "r") as f:
                self.ssh_known_hosts = f.read()
            self.hosts = self._parse()
            if not self.hosts:
                self.hosts = {}
        else:
            self.hosts = {}

    def _parse(self) -> Dict[str, Dict[str, str]]:
        """
        Parse SSH configuration file

        Args:
            N/A

        Returns:
            discovered_hosts: dict of host objects discovered in known hosts file

        Raises:
            N/A

        """
        # match any non whitespace from start of the line... this should cover v4/v6/names
        # skip a space and match any word (also w/ hyphen) to get key type, lastly
        # match any non whitespace to the end of the line to get the public key
        host_pattern = re.compile(r"^\S+\s[\w\-]+\s\S+$", flags=re.I | re.M)
        host_entries = re.findall(pattern=host_pattern, string=self.ssh_known_hosts)

        known_hosts: Dict[str, Dict[str, str]] = {}
        for host_entry in host_entries:
            host, key_type, public_key = host_entry.split()
            # to simplify lookups down the line, split any list of hosts and just create a unique
            # entry per host
            for individual_host in host.split(","):
                known_hosts[individual_host] = {}
                known_hosts[individual_host]["key_type"] = key_type
                known_hosts[individual_host]["public_key"] = public_key

        return known_hosts
