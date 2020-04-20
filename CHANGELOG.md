CHANGELOG
=======

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