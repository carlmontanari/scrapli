CHANGELOG
=======

# 2020.04.04
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