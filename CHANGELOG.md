CHANGELOG
=======

# 2020.XX.XX
- Converted all priv levels to be kwargs instead of just args for setup -- simple thing but makes it more readable IMO.
- Added to the Juniper prompt pattern to include matching the RE prompt that is on the line "above" the "normal
" prompt as this was getting included in command output instead of being seen as part of the prompt by scrapli.
- Convert driver privilege escalation prompts to use regex to match upper and lower case "P" in password prompt
- Fix core drivers to actually allow for users to pass `failed_when_contains`, `textfsm_platform`, `genie_platform
`, and `default_desired_privilege_level`
- Add better exception/message for attempting to send command/config to a connection object that has not been opened
- Add testing for on open/close methods of core drivers
- Add `send_config` method to send a single configuration string -- this will automagically handle sending a full
 configuration, breaking it into a list of configs, sending that list with `send_configs` and then joining the
  responses into a single `Response` object... or of course you can just send a single config line with it too!
- Add better handling/logging for `SystemSSH` transport when key exchange cannot be negotiated
- Convert the `_failed()` method of `MultiResponse` to be a property so users can check `.failed` on a `MultiResponse`
 object more intuitively/sanely
- ASYNC ALL THE THINGS... basically only an internal change, but hugely modified the guts of scrapli to try to be
 able to best support asyncio while still having the same api for sync and async. Again, if you dont care about
  aysncio this probably doesnt matter at all as all the "public" stuff has not changed for sync versions of things.
- Completely overhaul unit tests -- unit tests now spin up an SSH server using asyncssh, this server is a very basic
 implementation of an IOSXE device. This fake IOSXE device allows for connecting/sending commands/handling log on
  stuff like disabling paging all in as close to the real thing as possible while being completely self contained and
   completely in python. Additionally since there was a lot of changes to break things out to be more granular with the
    async implementation the testing has evolved to support this.
- Increased all hostname patterns to match up to 63 characters -- this is the hostname length limit for Cisco IOSXE
 at least and should be a reasonable value that hopefully doesnt really ever need to be changed/expanded now
- Changing logging to create a logger associated with each object instance and include the name/ip of the host in the
 log name -- should make things a lot nicer with threads/asyncio/etc.
- Moved from tox to using nox for handling tests/linting; originally this was because of some of the unit testing
 failing when ran via tox (now I believe this was because there was no TERM env var set in tox), but at this point
  nox is quite nice so we'll stick with it!
- Added exception to be raised when users try to use system transport on Windows
- Added underscores to hostname patterns for IOSXE, IOSXR, NXOS, and Junos (not valid in EOS at least in my testing)
- No more Windows testing, not worth the effort.

# 2020.05.09
- Add underscores to EOS config prompt matching
- Actually fixed on_close methods that I could have sworn were fixed.... *gremlins*! (was sending prompt pattern
 instead of a return char... for copypasta reasons probably)
- No longer "exit" config mode... given that send_command like methods already check to ensure they are in the right
 priv level there is no reason to exit config mode... just leave it when you need to. Should be a minor speed up if
  using send_configs more than once in a row, and otherwise should be basically exactly the same.
- For NetworkDrivers we no longer set the channel prompt pattern depending on the priv level -- it is now *always
* the combined pattern that matches all priv levels... this should make doing manual things where you change
 privileges and don't use scrapli's built in methods a little easier. Scrapli still checks that the current prompt
  matches where it thinks it should be (i.e. config mode vs privileged exec) though, so nothing should change from a
   user perspective.
- Improve (fix?) the abort config setup for IOSXR/Junos
- Add more helpful exception if ssh key permissions are too open
- Convert PrivilegeLevel from a namedtuple to a class with slots... better for typing and is also mutable so users
 can more easily update the pattern for a given privilege level if so desired
- Minor clean up stuff for all the core platforms and network driver, all internal, mostly just about organization!
- Add "configuration_exclusive" privilege level for IOSXRDriver, add "configuration_private" and
 "configuration_exclusive" for JunosDriver, modify some of the privilege handling to support these modes -- these can
  be accessed by simply passing `privilege_level="configuration_exclusive"` when using `send_configs` method
- Add support for configuration sessions for EOS/NXOS. At this time sessions need to be "registered" as a privilege
 level, and then are requestable like any other privilege level, and can be used when sending configs by passing
  the name of your session as the privilege level argument for send config methods
- Add a space to EOS prompts -- it seems its very easy to add one to the prompts and scrapli did not enjoy that
 previously!
- Give users the option to pass in their own privilege levels for network drivers, and also throw a warning if users
 try to pass `comms_prompt_pattern` when using network drivers (as this should all be handled by priv levels)
- Created `MultiResponse` object to use instead of a generic list for grouping multiple `Response` objects 
- Added `raise_for_status` methods to `Response` and `MultiResponse` -- copying the `requests` style method here to
 raise an exception if any elements were failed
- BUGFIX: fixed an issue with IOSXEDriver not matching the config mode pattern for ssh pub key entries.


# 2020.04.30
- Continued improvement around `SystemSSHTransport` connection/auth failure logging
- Fix for very intermittent issue where pty fd is not available for reading on SystemSSH/Telnet connections, now we
 loop over the select statement checking the fd instead of failing if it isn't immediately readable
- Implement atexit function if keepalives are enabled -- this originally just lived in the ssh2 transport, but needs
 to be here in the base `Transport` class as the issue affected all transport types
- Added `send_commands_from_file` method... does what it sounds like it does...
- Added `send_configs_from_file` method (`NetworkDriver` and sub-classes)... also does what it sounds like it does
- Simplified privilege levels and overhauled how auth escalation/deescalation works. Its still probably a bit more
 complex than it should be, but its a bit more efficient and at least a little simpler/more flexible.
- Removed `comms_prompt_pattern` from Network drivers and now build this as a big pattern matching all of the priv
 levels for that device type. This is used only for initial connection/finding prompt then scrapli still sets the
  explicit prompt for the particular privilege level.
- Implemented lru_cache on some places where we have repetitive tasks... probably unmeasurable difference, but in
 theory its a little faster now in some places
- Moved some Network driver things into the  base `NetworkDriver` class to clean things up a bit.
- Added an `_abort_config` method to abort configurations for IOSXR/Juniper, this is ignored on the other core platforms
- *BREAKING CHANGE*: (minor) Removed now unneeded exception `CouldNotAcquirePrivLevel`
- Made the `get_prompt_pattern` helper a little worse... should revisit to improve/make its use more clear
- Fixed a screw up that had ridiculous transport timeouts -- at one point timeouts were in seconds, then milliseconds
... went back to seconds, but left things setting millisecond values... fixed :D 
- Added `transport_options` to base `Scrape` class -- this is a dict of arguments that can be passed down to your
 selected transport class... for now this is very limited and is just for passing additional "open_cmd" arguments to
  `SystemSSHTransport`. The current use case is adding args such as ciphers/kex to your ssh command so you don't need
   to rely on having this in an ssh config file.

# 2020.04.19
- Increase character count for base prompt pattern for `Scrape`, `GenericDriver`, and core drivers. Example:
`r"^[a-z0-9.\-@()/:]{1,32}[#>$]$"` for the base `IOSXEDriver` `comms_prompt_pattern` has been increased to:
`r"^[a-z0-9.\-@()/:]{1,48}[#>$]$"`
- Improve the logging for `SystemSSHTransport` authentication
- Fixed an issue where `SystemSSHTransport` auth would fail due to a login banner having the word `password` in the
 banner/text
- Significantly increase the base `timeout_ops` value -- as this is not a timer that is going to cause things to
 block, it may as well be much higher for the default value to help prevent issues
- Fixed an issue w/ ssh config file not parsing the last host entry
- Added super basic tests for most of the examples -- just making sure they don't blow up... in general that should
 keep them in decent shape!
- Removed cssh2 and miko transports from scrapli core. These have been migrated to their own repositories. From a
 users perspective nothing really should change -- you can still `pip install scrapli[paramiko]` to install the
  paramiko transport and the requirements (paramiko), and the actual usage (setting `"transport" = "paramiko
  "`) remains the same! This is mostly about keeping the core of scrapli as simple as possible, and also will
   hopefully help to illustrate that `SystemSSH` is the development priority for scrapli.
- Convert many function calls to use keyword args for better readability throughout
- Add a `comms_auto_expand` argument to the `Channel`; for now this is mostly not used, but may be useful in the
 future. The purpose of this is to handle devices that auto expand input commands to their full canonical name.
- Hopefully(?) fixed a bit of an idiosyncrasy where the `timeout_transport` was being used to decorate read/write
 operations for telnet/system transports. This is no longer the case, the read/write methods are NOT decorated now
 , instead we rely on the `timeout_ops` to time these operations out OR the `timeout_transport` being set to the
  timeout value (telnet) or `ServerAliveInterval` value for system ssh.

# 2020.04.11
- *BREAKING CHANGE*: modify `send_interact` to just make more sense in general... now it supports 1->N "events" to
 interact with -- see the "handling prompts" section of README for updated example
- Moved `record_response` of `Response` object to be a private method, shouldn't really be needed publicly
- Moved `authenticate` and `isauthenticated` methods of ssh2/paramiko transports to private methods
- Add `auth_bypass` option to ignore ssh auth for weird devices such as Cisco WLC -- currently only supported on
 system transport.
- Bump timeout_transport up to 10 seconds after finding some issues for some users.
- Add example for "non-standard" device type (Cisco WLC) demo-ing the auth_bypass, custom on_open method, custom
 comms_prompt_pattern and just general non-standard device stuff.
- Add option (and make it the default) to have textfsm data returned in list of dict form with the headers being the
 keys and of course the row values as the values, should be much nicer on the eyes this way!
- Added terminal width settings for the core drivers to set things as wide as possible so long commands don't have
 issues
- Teeny tiny improvements that may make things a tick faster in Channel by using str methods instead of re
- Create a draft of public api status doc -- this should be useful on a quick glance to see if/when any public
 methods change, obviously as development simmers down things should be stable but inevitably stuff *will* change
 , so the goal here is to just document when methods were introduced and the last time they were changed
- Move some imports around so that scrapli works on windows (with paramiko/ssh2 transports)

# 2020.03.29
- Add support for `parse_genie` to Response object; obviously really only for Cisco devices at this point unless
 there are parsers floating around out there for other platforms I don't know about!
- Add an `atexit` function for the ssh2 transport which forcibly closes the connection. This fixes a bug where if a
 user did not manually close the connection (or use a context manager for the connection) the script would hang open
  until an interrupt.
- Added a `GenericDriver` for those with non-core platforms. The `GenericDriver` has a really broad prompt pattern
 match, doesn't know about privilege levels or any other device specific stuff, but does provide the `send_command
 `, `send_commands`, `send_interact`, and `get_prompt` methods just like the "core" drivers do. This should be a
  decent starting point for anyone working on non-core platforms!
- Minor unit test improvement to cover send_commands (plural) and to cover the new `GenericDriver`
- Improved auth failure handling for systemssh using pty auth (username/pass auth)
- Add "failed_when" strings to the core drivers; these are used in the response object to help indicate if the
 channel input failed or succeeded. For scrapli not super super helpful, but nornir_scrapli will benefit from this as
  well!
- Modify `NetworkDriver` to inherit from `GenericDriver` -- this allowed for some clean up of how/where `Response
` objects get created/returned from. `Channel` now is much more de-coupled from whatever sits on top of it (this will
 be important for some netconf testing happening soon!). 
- Minor test de-duplication around ssh config/known hosts file gathering.
- Added a few simple examples for structured data (textfsm/genie) and updated existing examples a bit.