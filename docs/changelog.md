Changelog
=========

## 2022.01.30.post1

- Remove newline anchor in in-channel auth password pattern. Felt like a good/smart idea but Cisco in their infinite 
  wisdom have some awful banner on IOL (CML/VIRL) things that doesn't end with a newline and too many people will 
  hit that.


## 2022.01.30

- Removed deprecated `comms_ansi` argument
- Improved error handling/error message for insufficient permissions when opening ssh config/known hosts file 
  (system transport)
- Added support for hashed entries in known hosts file thanks to @kangtastic work in #174
- Improved "in channel" SSH and Telnet authentication handling; better consistency between sync and async, patterns 
  are now compiled only if/when needed
- Added option to *enable* echo in PTYProcess (was originally removed from vendor'd code) -- should only be 
  useful/necessary with netconf #165
- Allow users to build their own `open_cmd` for system transport -- users can override this to do things like 
  `kubectl exec -it args args args` or `docker exec -it args args args` to connect to containers in k8s/docker #166
- Updated/fixed(?) Juniper shell patterns for "normal" and root shells #170
- Support transport options being passed to asyncssh transport thanks to @cuong-nguyenduy work in #178 and #183
- A handful of nice readability/simplicity improvements throughout the codebase thanks to @yezz123 in #188
- Fix (add) missing kwarg for `channel_log_mode` in the driver layers "above" base driver
- Update NXOS config pattern to include "+" to not break when entering TACACS config mode
- Added support for encrypted SSH keys with ssh2 transport in #192 thanks to @shnurty
- Fix/improve in channel SSH auth password prompt pattern to match scrapligo (which handles user@host password: strings)
- Update ssh2-python requirements now that 3.10/Darwin release is available
- Better exception/exception message for auth failures escalating privilege (network drivers)
- Added a global `Settings` object -- for now only has an attribute for "SUPPRESS_USER_WARNINGS" to... suppress user 
  warnings
- Added `read_callback` method to `GenericDriver`/`AsyncGenericDriver` -- basically this is a fancier version of 
  send interactive that lets you assign callbacks to things that scrapli reads rather than having to follow prompts 
  in a linear fashion.
- Dropped Python3.6 support as it is now EOL! Of course, scrapli probably still works just fine with 3.6 (if you 
  install the old 3.6 requirements), but we won't test/support it anymore.
- Added `enable_rsa2` setting to paramiko transport options -- basically 2.9.0+ paramiko enables rsa2 support by 
  default which causes key auth to fail on the test network devices, so we disable that by default, but exposet his 
  flag so users can enable it if desired!


## 2021.07.30

- Added "% Unavailable command" to EOS `failed_when_contains`
- Moved core platform `failed_when_contains` to base to not have to duplicate them in sync and async platforms
- Add `file_mode` to the `enable_basic_logging` function, can now choose "append" or "write" for logfile
- Add `channel_log_mode` to the base driver arguments; you can now choose "append" or "write" for this as well!
- Improve reading until prompt methods; no longer use re.search on the entire received byte string, now only checks 
  for prompt on the last N chars where N is governed by the base channel args `comms_prompt_search_depth` attribute..
  . this fixes an issue where scrapli could be wayyyyyy slow for very very large outputs (like full tables show bgp)
- Fix bug (or just terrible initial idea!?) in asynctelnet that reset a timer back to a very small value that was used 
  for testing; *most* people shouldn't have noticed an issue here, but if you had slow devices this could cause 
  issues that "looked" like an authentication issue due to scrapli not having responded to all telnet control 
  characters before punting to auth
- Added `commandeer` to driver object; this is used to "commandeer" an existing connection but treat it like the new 
  connection object (prompt patterns, methods, etc.) -- generally this would be used for using `GenericDriver` to 
  connect to a console server, then "commandeering" that connection and turning it into an IOSXR/IOSXE/etc. 
  connection object so you have all the "normal" behavior of scrapli
- Add missing timeout on the asynctelnet open method
- Add py.typed to hopefully do typing more correctly :P
- BUGFIX: network drivers aborted configuration sessions if responses were failed even if the `stop_on_failed` arg 
  was set to False; this has been fixed now so that sessions are only aborted if the response is failed *and*
- Improved typing for `send_interactive`
- Remove napalm dev requirement -- switch to scrapli-cfg for dev environment config management; something something 
  eating dog food or whatever.
- Deprecate `comms_ansi` -- if there is an ANSI escape sequence we will now just strip it out automagically; this is 
  *not* currently a breaking change, but will be -- there is a deprecation warning now and `comms_ansi` will be 
  fully removed in the 2022.01.30 release (and pre-releases).
- Removed a sleep that was in the default `on_open` for IOSXR devices... this has been there a while and I *think* 
  it was just a hold over from early early versions of scrapli that perhaps had a less robust in channel 
  authentication handler. 1 second faster IOSXR for free! Yay!
- Fixed an issue with system transport where the transport would get closed twice causing an unhandled exception -- 
  thank you to Alex Lardschneider for finding this!
- Added an example for the `enable_basic_logging` function as well as the `commandeer` method
- Improved priv level handling -- if you try to acquire "parallel" privileges (ex. configuration and configuration 
  exclusive in IOSXR) previously we would say things worked, but we would just stay in configuration mode. This has 
  been fixed (hopefully)!
- Move ansi escape pattern to compile globally, so it only compiles once (why it was never like that before... who knows)
- Simplify the `collect` bits for integration tests... this is still not used heavily but hopefully will be soon!
- Replace vrnetlab creds in examples with scrapli (felt confusing to have vrnetlab creds everywhere, plus functional 
  testing is moving away from (but still supporting) vrnetlab test environment)
- Crank up the rows/cols for system transport -> 80 rows, 256 cols -- this to align with scrapligo and to make it 
  less common that users need to modify these values.
- BUGFIX: fixed blocking read in async channel telnet authentication (thank you Dmitry Figol!)
- Added `not_contains` field to privilege levels... this will help greatly simplify the necessary regex patterns, as 
  well as allow us to ditch look arounds which go does not support... step one to a standardized community platform 
  that works with python -or- go!
- Simplified (at least a little... more would be good) patterns for privilege levels for core platforms.
- Added `_generic_driver_mode` to  the `NetworkDriver` classes -- this is a private mode as it should probably be used
   cautiously -- the idea here is that you can send any strings you want and scrapli will not care about privilege
  levels at all. See the discussion about this [here](https://github.com/carlmontanari/scrapli/discussions/128).
- BUGFIX: fixed asynctelnet issue with control character handling, thank you to [@davaeron](https://github.com/davaeron) 
  -- see #147
- *BREAKING CHANGE* removed the `transport.username_prompt` and `transport.password_prompt` attributes of the telnet 
  transports. All authentication has been moved into the channel, so it made no sense to leave these attributes on 
  the transports. This may cause an issue for users that had explicitly set their prompts to something non-standard.
- Finally added logic to auto set port to 23 for telnet :)
- BUGFIX: fixed a rare issue where decoding bytes received from the channel (in the response object) would raise a 
  `UnicodedecodEerror`; we now catch this exception and decode with `ISO-8859-1` encoding which seems to be much 
  less picky about what it decodes. Thanks to Alex Lardschneider for yet another good catch and fix!
- Added `interaction_complete_patterns` to all "interactive" methods -- this argument accepts a list of 
  strings/patterns; will be re-escape'd if each string does *not* start with and end with "^" and "$" (line anchors),
  otherwise will be compiled with the standard scrapli case-insensitive and multiline flags. If the interactive 
  event finds any of these pattenrs during the course of the interacting it will terminate the interactive session. 
  Note that this is entirely optional and is a keyword only argument so no changes are necessary to any existing 
  scrapli programs.


## 2021.01.30

- *BREAKING CHANGE* `PrivilegeLevel` import location changed -- this will break things! 
- `timeout_exit` deprecated; will always close connection on timeout now
- All exceptions rationalized/changed -- all exceptions now rooted in `ScrapliException` and scrapli should not 
  raise any exception that is not rooted in this! It is of course possible that non-scrapli exceptions will get 
  raised at some point, but all "common" exceptions will now follow this pattern.
- Added opinionated logging option -- should be used only for debugging/testing, otherwise use your own logging setup!
- Moved "in channel" auth into channel (for telnet/system ssh authentication)
- Added `channel_lock` option, defaults to false
- Added `channel_log` option
- Decorators got reswizzled a little, no more requires open as the transports handle this. There is now a dedicated 
  ChannelTimeout and TransportTimeout to keep things simpler.
- All transport plugins are now in scrapli "core"
- All (ok, most...) channel and transport args are now properties of the driver class -- this should remove 
  confusion about where to update what timeout/value
- `Response._record_response` is now public but only for linting reasons, people generally should ignore this anyway!
- Python 3.6 will now require dataclasses backport
- All driver methods now have only the "main" argument as an allowable positional argument, the rest of the 
  arguments are keyword-only! For example, `send_command` you can pass a positional argument for `command`, but 
  `strip_prompt` and any additional arguments *must* be keyword arguments!
- *BREAKING CHANGE* `Scrape`/`AsyncScrape` renamed --> `Driver`/`AsyncDriver` -- given most folks should not be using 
  these directly there will be no alias for this, just a hard change!
- More improvements to IOSXE tclsh pattern handling; handles tclsh in exec or privilege exec mode now
- `read_until_prompt_or_time` now supports regex patterns in the `channel_outputs` list (pass as a string, will be 
  compiled for you)
- Big improvements to Factory for users of IDEs -- factories now have proper typing data so you will have nice auto 
  completion things there/typing will be much happier


## 2020.12.31
- Make log messages for textfsm and genie parsers failing to parse consistent as `log.warning`
- Add factory example
- Add "root" priv level to junos driver -- probably should be considered experimental for now :)
- Fix issue where `send_config` unified result did not have finish time set
- **POSSIBLY BREAKING CHANGE:** logger names have changed to be easier to get/make more sense -- the logger for each 
  instance used to look like: "scrapli-channel-{{ HOST }}" which kinda was not really smart :). Loggers now look 
  like: "scrapli.{{ HOST }}:{{ PORT }}.channel" -- can be channel|driver|transport!
- Changes to test environment:
  - ~~Support running devices on localhost w/ nat'd management ports -- in "vrouter" mode (poorly named) -- this is 
    enabled with the `SCRAPLI_VROUTER` environment variable set to on/true/something~~ **Update 2022.01.30** - renamed 
    to `SCRAPLI_BOXEN` but does the same thing!
  - Added bootvar into nxos base config -- when missing causes qemu nxosv to boot into loader prompt so thats no good
  - Replace resource settings in vdc in nxos to account for nxos instances with differing resources (memory/cpu)
  - Got rid of static license udi in iosxe config, replaced more certificate stuff so show run comparisons are 
    easier on iosxe
- **NEW TRANSPORT** `asynctelnet` transport is built using standard library asyncio, as such it is part of scrapli core
  - Should be considered beta for a while :)
  - Added a bunch of tests mocking streamreader/writer to ensure that this driver is well tested
- Added asynctelnet support in nxos and juniper drivers (to change prompt for those platforms)
- Support asynctelnet in base driver
- `auth_bypass` for both telnet drivers completely bypasses not only auth (as it did previously) but also the auth 
  validation where we confirm we got logged in successfully -- reason being is that for console servers and such you 
  may not care about that, you may just want to log in and read data.
- Removed unnecessary re-checking/verifying of ssh config file in system transport (was basically duplicated from 
  base transport, so was pointless!)
- Bumped all the default timeout values up as they were probably a bit on the aggressive side
- Added `eager` argument to send commands/commands from file and config/configs/configs from file methods -- 
  basically this `eager` mode will *not* look for a prompt between lines of commands/configs. This means that things 
  have a tiny potential to get out of whack because we will just send things as fast as possible. In order to not 
  totally break things we *will* (whether you like it or not!) wait and find the prompt on the last command/config 
  in the list though -- that way we dont get too out of whack. This now means we can use `eager` to configure 
  banners and macros and things and we no longer need to do the dirty send interactive workaround.
- Added `ScrapliConnectionLost` exception and raise it if we get EOF in system transport -- with a message that is 
  more clear than just "EOF" and some obscure line in ptyprocess!
- Added `tclsh` privilege level for IOSXE
- Fixed a bug that would prevent going to "parallel" privilege levels -- i.e. going from tclsh to configuration or 
  visa versa in IOSXE or from configuration to configuration_exclusive in IOSXR
- If no `failed_when_contains` is passed to `send_interactive` network drivers will now use the network drivers 
  `failed_when_contains` attribute to bring it inline with the normal command/config methods
- Added `timeout_ops` to `send_interactive` and wrap those methods with the `TimeoutModifier` decorator
- Add logic to properly fetch socket address family type so we can handle IPv6 hosts (w/ scrapli-ssh2/scrapli-paramiko)
- Added `tclsh` privilege level for NXOS, didn't even know that existed before!


## 2020.11.15
- Fix a regex that sometimes caused a failed functional IOSXR test
- Add `ptyprocess` transport options for system transport -- sounds like this may be needed for huawei community
 platform to be able to set the pty process terminal size -- also added some basic testing for this
- Update scrapli-ssh2 pin to latest version -- now supports keyboard interactive auth; also un-skipped all related
 EOS tests now that this works
- Fix missing acquire priv in default on_open methods for nxos and eos async version
- Fix incorrect `textfsm_platform` for iosxr (was cisco_iosxr, now is cisco_xr)
- Remove unnecessary decorator on write operations for systemssh and telnet -- this operation shouldn't block so this
 was unnecessary; any issue here should raise some exception from the lower level library.
- Playing around w/ adding coverage reports with Codecov


## 2020.10.10
- Improve logging in helper functions - especially around resolving ssh config/known hosts
- Add `ttp_parse_output` method to Response object; add `ttp_parse` function in helper
- Load requirements from requirements files and parse them for setup.py -- stop me from forgetting to update in one
 place or another!
- Slacken the IOSXE configuration prompt pattern -- `hostname(ipsec-profile)` was not being caught by the pattern as
 it was expecting the part in parenthesis to start with "conf" - thank you Talha Javaid for bringing this up on ntc
  slack, and Alex Lardschneider for confirming the "fix" should be good to go!
- Add `community` pip extra to install scrapli community
- Minor README house keeping!
- Made transport `set_timeout` saner -- I genuinely don't know what I was doing with that before... this included the
 base class as well as updating telnet and systemssh... in theory this could be a breaking change if you were just
  calling `set_timeout` for some reason without passing an argument... you probably weren't doing that... because why
   would you? There was *some* precedent for doing it like this before but it isn't worth caring about now :)
- Did smarter things with imports in helper, added tests to make sure the warnings are correct
- Dramatically simplified session locking... this had just gotten out of hand over time... now only the channel locks
. This means that basically all inputs/outputs should go through the channel and/or you should acquire the lock
 yourself if you wish to read/write directly to the transport. Critically this means that all the external transport
  plugins AND scrapli-netconf need to be updated as well -- this means that you *must* update all of these if you are
   using this release! (requirements are of course pinned to make sure this is the case)
- **BREAKING CHANGE:** removed **ALL** keepalive stuff... for now. This will probably get added back, but AFAIK nobody
 uses it right now and the implementation of it is frankly not very good... keeping it around right now added complexity
  for little gain. Keepalives will be back and improved hopefully in the next release. If you need them, please just
   pin to 2020.09.26!


## 2020.09.26
- Improved error handling/exceptions for scrapli `Factory`
- Fixed issue where `system` transport did not properly close/kill SSH connections
- Added 3.9-dev testing to GitHub Actions
- Added initial testing/support of `on_init` callable to base driver -- the idea for `on_init` is mostly to allow
 `scrapli_community` platform creators to be able to add an additional callable to be executed after initialization
  of the scrapli object, but before any `open` method is called
- Added initial testing/support of `scrapli_community` driver classes -- this would allow `scrapli_community
` platform creators to create driver classes so that they can implement custom methods for each platform type if
 desired
- Minor improvements to `telnet` transport to improve logging as well as authentication validation (are we
 authenticated); this also makes `telnet` look/feel a lot more like `system` which is nice for consistency reasons
- Fix regression that caused scrapli to spam a bajillion log entries -- now a filter gets applied in both `Channel
` and `Transport` base classes to snag the filter from the root `scrapli` logger and apply it to the base/channel
 loggers
- Fully give into the warm embrace of dependabot and pin all the dev requirements to specific versions... dependabot
 can keep us up to date and this lets us not worry about builds failing because of dev requirements getting changed
  around
- Fix ptyprocess file object closing issue


## 2020.08.28
- Added Packet Pushers scrapli episode to the README!!
- Added NXOS and Junos mock ssh servers and created tests for open/close methods (silly tests but just ensures we
 send what we think we should be sending)
- Created a property `timeout_ops` on the driver class -- this property will also set the `timeout_ops` value of the
 channel as well, this is just to make it so users don't have to do `conn.channel.timeout_ops` to set the timeout
  value... that was not super intuitive!
- Update dev/test requirements to finally have pylama 2.6! This means that isort can be unpinned and free to update!
- Add `send_and_read` method to `GenericDriver` -- this method allows you to send an input (at the current priv level
) and wait for a prompt, an expected output, or a duration.
- Add `eager` flag to the channel `send_input` method -- this probably should *not* be used by many folks, but can be
 used to *not* read until the prompt pattern is seen. In other words, this will send an input, read the input off the
  channel and then return.
- All exceptions that are raised due to catching an internal exception should now be raising "from" the caught
 exception -- mostly this is to appease Pylama, but may end up being nicer on the eyes/easier to see whats going on
  in some scenarios. 
- IOSXE now catches "Enable password:" for an escalation pattern from exec to privilege exec -- fixes [#45](https://github.com/carlmontanari/scrapli/issues/45)
- The "requires open" decorator has been updated/fixed to play nice with asyncio
- `timeout_ops` has been converted from an int to a float to allow for more granular timeout control (the other
 timeouts remain as integers)
- Few minor docstring fixes from copypasta issues :)
- Update black pin/re-run black


## 2020.07.26
- Fixed the same `get_prompt` issue from the last release, but this time managed to actually fix it in async version!
- Better handling of `read_until_input` -- stripping some characters out that may get inserted (backspace char), and
 compares a normalized whitespace version of the read output to the a normalized whitespace version of the input
 , fixes [#36](https://github.com/carlmontanari/scrapli/issues/36).
- Improved system transport ssh error handling -- catch cipher/kex errors better, catch bad configuration messages.
- Now raise an exception if trying to use an invalid transport class for the base driver type -- i.e. if using
 asyncssh transport plugin with the "normal" sync driver class.
- Added links to the other projects in the scrapli "family" to the readme.
- Created first draft of the scrapli "factory" -- this will allow users to provide the platform name as a string to a
 single `Scrapli` or `AsyncScrapli` class and it will automagically get the right platform driver selected and such
 . This is also the first support for `scrapli_community`, which will allow users to contribute non "core" platforms
  and have them be usable in scrapli just like "normal".
- Overhaul decorators for timeouts into a single class (for sync and async), prefer to use signals timeout method
 where possible, fall back to multiprocessing timeout where required (multiprocessing is slower/more cpu intensive so
  dont use it if we dont have to).


## 2020.07.12
- Fixed a silly issue where `get_prompt` was setting the transport timeout to 10s causing user defined timeouts to be
 effectively ignored.
- Improved telnet authentication handling -- previously if a return character was needed to get the auth prompts to
 kick into gear this could break auth.
- Added "auth_bypass" to telnet transport.
- Probably BUGFIX -- async functions were being decorated by the "normal" `operation_timeout` decorator -- created a
 mostly duplicated async version of the timeout decorator to wrap the `AsyncChannel` methods. 
- Fixed a maybe regression that caused drivers to try to authenticate (via interactive methods) even if a
 `auth_secondary` is not set. Added tests to make sure that we raise a warning if there is no secondary password set
 , but try to increase privilege without authentication, and of course if there is an auth secondary set, we
  obviously try to auth in the normal fashion.
- Started thinning down the PtyProcess stuff to simplify and and remove all unnecessary parts, as well as add typing
 and docstrings... not done yet, but some progress!
- Added additional asyncio example
- Added blurb about versioning in README
- Fixed a few README issues (incorrect methods/typos)
- Updated notes about auth_bypass to include telnet support
- Added `SSHNotFound` exception for system SSH/PtyProcess if ssh binary can't be found


## 2020.07.04
- Updated IOSXE base config to include netconf setup for consistency w/ scrapli_netconf
- Removed "pipes" authentication for system ssh -- this is mostly an internal change that simplifies the way that
 system transport authenticates. We lose the ability to very easily read out of stderr what is going on so even if we
  auth with a key now we have to "confirm" that we are authenticated, but this removes a fair bit of code and unifies
   things as well as allows for the next line item...
- Added support for `auth_private_key_passphrase` to system transport -- allows for entering ssh key passphrase to
 decrypt ssh keys
- Added an example on how to deal with "weird" things like banners and macros -- these types of things change how the
 ssh channel works in that they are pseudo "interactive" -- meaning the prompt is modified/removed so scrapli can't
  ever "know" when a command is done inserting. It would be possible to support these types of config items more
   "natively" but doing so would lose some of the smarts about how scrapli enters/confirms inputs sent, so for now
    (and probably for forever) these will need to be configured in a "special" fashion
- Updated IOSXE for functional tests to use 16.12.03 -- this includes updates to the base config/expected configs
... AFAIK there is some better netconf/restconf support in this version which may be handy for tests for scrapli-netconf
- Update channel/drivers to never decode bytes -- this now only happens in the response object; primary motivation
 for this is to not have to decode/re-encode in general, and in scrapli-netconf in particular


## 2020.06.06
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
- BUGFIX: Added underscores to hostname patterns for IOSXE, IOSXR, NXOS, and Junos (not valid in EOS at least in my
 testing)
- No more Windows testing, not worth the effort
- BUGFIX: Added functionality to merge less specific (but matching) host entry data for ssh config file hosts
 -- meaning that we can now merge attributes from a "*" entry into a more specific host entry (see #21)
- Add dependabot to see how we like having that friend around...


## 2020.05.09
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


## 2020.04.30
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


## 2020.04.19
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


## 2020.04.11
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


## 2020.03.29
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