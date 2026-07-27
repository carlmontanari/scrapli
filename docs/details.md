# Library Details

This section aims to outline some core concepts about scrapli as well as outline the available methods for both Cli and NETCONF connections.


## Concepts

### Transports

scrapli supports multiple *transports* -- that is, the thing that does the actual sending and receiving of data to/from the server. Those transports are `telnet`, `bin` and `ssh2`.

The `telnet` transport is of course for connecting to Cli devices via telnet -- no surprises there. This transport is a custom telnet driver written in zig that is effectively a port of the since deprecated Python standard library `telnetlib` package.

The default transport for everything *not* telnet is the `bin` transport. This transport is a pty-wrapper around a binary, typically `/bin/ssh`.  The primary benefit of this transport is that you natively get 100% support/coverage of openssh features -- things like ProxyJump, ControlPersist, handling ciphers, key exchanges, and every other flag/feature. The binary can also be swapped to something else entirely -- so you could slot in something like `docker exec` or perhaps a binary to talk to devices over some vendor serial port or something similar.

Lastly, there is the `ssh2` transport -- this transport is a zig wrapper around the `libssh2` library compiled with openssl for crypto functionality. The biggest benefit to this transport is that there is no need to have openssh available for it to work -- so this transport can easily be ran inside of a container for example. Functionality is somewhat limited as only the minimum `libssh2` features have been exposed via the zig shim.


### Platform Definitions

A platform *definition* defines how libscrapli should interact with a Cli device (telnet/SSH). This definition is a simple YAML file that holds some information such as the regular expression pattern used to match a prompt for the given device, some inputs that should be called upon connection (to disable pagingation for example), and possible "modes" the device may have (such as a "configuration" mode).

Here is an annotated and slightly modified version (for illustration purposes) of the (at time of writing) Nokia SRLinux platform definition:

```yaml
---
prompt_pattern: '(^.*[>#$]\s?+$)|(--.*--\s*\n[abcd]:\S+#\s*$)' # (1)
prompt_excludes: # (2)
  - foobarbaz
default_mode: 'exec' # (3)
modes:  # (4)
  - name: 'bash'
    prompt_pattern: '^.*[>#$]\s?+$'
    prompt_excludes: # (5)
      # ensure bash doesnt match on exec/config. technically this could be in a bash prompt
      # but seems pretty unlikely
      - '--{'
    accessible_modes:
      - name: 'exec'
        instructions: # (6)
          - send_input:
              input: 'exit'
  - name: 'exec'
    prompt_pattern: '^--{(\s\[[\w\s]+\]){0,5}[\+\*\s]{1,}running\s}--\[.+?\]--\s*\n[abcd]:\S+#\s*$'
    accessible_modes:
      - name: 'bash'
        instructions:
          - send_input:
              input: 'bash'
      - name: 'configuration'
        instructions:
          # yes, this is made up and not applicable to srlinux, just using it to have an example!
          - send_prompted_input: # (7)
              input: 'enable'
              prompt_exact: 'Password:'
              response: '__lookup::enable'
  - name: 'configuration'
    prompt_pattern: '^--{(\s\[[\w\s]+\]){0,5}[\+\*\!\s]{1,}candidate[\-\w\s]+}--\[.+?\]--\s*\n[abcd]:\S+#\s*$'
    accessible_modes:
      - name: 'exec'
        instructions:
          - send_input:
              input: 'discard now'
failure_indicators: # (8)
  - 'Error:'
on_open_instructions: # (9)
  - enter_mode:
      requested_mode: 'exec'
  - send_input:
      input: 'environment cli-engine type basic'
  - send_input:
      input: 'environment complete-on-space false'
on_close_instructions: # (10)
  - enter_mode:
      requested_mode: 'exec'
  - write:
      input: 'quit'
```

1. The single most important part -- a regular expression (PCRE2) that matches any/all prompts the device may show.
2. Optional array of strings that indicate a matched prompt should be excluded -- this applies only
to the global prompt pattern.
3. The "mode" to acquire and send inputs to by default.
4. An array of "modes" that define a more explicit pattern that matches the prompt of this mode, and which other modes are accessible from the given mode (and how to access them).
5. Prompts can be tricky to match with a regular expression without accidentally matching other mode prompts too -- this is a list of strings that, if a prompt contains them, would preclude a possible prompt from matching this mode.
6. Instructions on how to acquire another mode from this mode -- these instructions are very simple -- send an input, send a return character, send a *prompted* input (for things like expecting a password prompt).
7. You can always "manually" enter modes by sending inputs (or for password related things more
likely using `sendPromptedInput` or the python/go equivalent), however for privilege levels this
should generally be baked into the platform. In this case we send `enable`, expecting `Password:`
and then send the value the "enable" field via a lookup (more on this below), alternatively you
could simply put your credentials here in plaintext if you're into that sort of thing.
8. A list of strings that when found in the output of some input will cause the result object to be marked as "failed" -- this is not an error scrapli will return, but is more an annotation that the given input completed successfully but likely did not succeed.
9. Instructions for what libscrapli should do immediately upon successfully opening a connection to a device of this flavor. Typically this includes disabling fancy prompt things, disabling pagination, and possibly disabling console/terminal logging output.
10. Instructions for what libscrapli should do before closing the connection. Usually this just means sending "exit", "quit", or "logout" in order to nicely close/clean-up the connection.

Lastly, here is a lazily LLM generated schema if you're into that sort of thing (that appears to be pretty accurate):

??? schema "Definition JSON Schema"
    ```json
    {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "title": "PlatformDefinition",
      "description": "libscrapli cli platform definition -- the yaml document that tells libscrapli how to drive a cli connection to some device: prompt matching, available 'modes', on open/close instructions, etc.",
      "type": "object",
      "properties": {
        "prompt_pattern": {
          "description": "PCRE2 pattern that matches any prompt of the device, in any mode.",
          "type": "string"
        },
        "prompt_excludes": {
          "description": "Substrings that, if found in the output, indicate the match is not actually a prompt.",
          "type": [
            "array",
            "null"
          ],
          "items": {
            "type": "string"
          }
        },
        "default_mode": {
          "description": "Name of the mode the driver should treat as the default mode -- must be one of the modes defined in 'modes'.",
          "type": "string"
        },
        "modes": {
          "description": "The privilege levels/'modes' of the device (e.g. exec, privileged exec, configuration).",
          "type": "array",
          "items": {
            "$ref": "#/$defs/mode"
          }
        },
        "failure_indicators": {
          "description": "Substrings in device output that indicate an operation failed (e.g. '% Invalid input').",
          "type": [
            "array",
            "null"
          ],
          "items": {
            "type": "string"
          }
        },
        "on_open_instructions": {
          "description": "Instructions executed after the connection is opened and authenticated (e.g. disable paging).",
          "type": [
            "array",
            "null"
          ],
          "items": {
            "$ref": "#/$defs/onXInstruction"
          }
        },
        "on_close_instructions": {
          "description": "Instructions executed prior to closing the connection.",
          "type": [
            "array",
            "null"
          ],
          "items": {
            "$ref": "#/$defs/onXInstruction"
          }
        },
        "force_in_session_auth": {
          "description": "Force 'in session' authentication handling (i.e. username/password prompts consumed in the session itself, as with telnet or bin transport).",
          "type": [
            "boolean",
            "null"
          ],
          "default": false
        },
        "bypass_in_session_auth": {
          "description": "Skip 'in session' authentication handling entirely.",
          "type": [
            "boolean",
            "null"
          ],
          "default": false
        },
        "ntc_templates_platform": {
          "description": "The ntc-templates platform name to use for textfsm parsing of outputs.",
          "type": [
            "string",
            "null"
          ]
        },
        "genie_platform": {
          "description": "The (pyats) genie platform name to use for genie parsing of outputs.",
          "type": [
            "string",
            "null"
          ]
        }
      },
      "required": [
        "prompt_pattern",
        "default_mode",
        "modes"
      ],
      "additionalProperties": false,
      "$defs": {
        "mode": {
          "title": "Mode",
          "description": "A mode -- some type of config 'level' on a cli device, e.g. 'privileged exec' or 'configuration'.",
          "type": "object",
          "properties": {
            "name": {
              "description": "Name of the mode.",
              "type": "string"
            },
            "prompt_exact": {
              "description": "Exact string that matches this mode's prompt.",
              "type": [
                "string",
                "null"
              ]
            },
            "prompt_pattern": {
              "description": "PCRE2 pattern that matches this mode's prompt.",
              "type": [
                "string",
                "null"
              ]
            },
            "prompt_excludes": {
              "description": "Substrings that, if found in the current prompt, exclude it from matching this mode (useful when another mode's prompt would otherwise also match).",
              "type": [
                "array",
                "null"
              ],
              "items": {
                "type": "string"
              }
            },
            "accessible_modes": {
              "description": "Modes reachable from this mode and the instructions required to get to them.",
              "type": [
                "array",
                "null"
              ],
              "items": {
                "$ref": "#/$defs/accessibleMode"
              }
            }
          },
          "required": [
            "name"
          ],
          "additionalProperties": false
        },
        "accessibleMode": {
          "title": "AccessibleMode",
          "description": "The name of a mode accessible from the parent mode, and the instructions required to access it.",
          "type": "object",
          "properties": {
            "name": {
              "description": "Name of the target mode.",
              "type": "string"
            },
            "instructions": {
              "description": "Operations executed, in order, to move from the parent mode to the target mode.",
              "type": "array",
              "items": {
                "$ref": "#/$defs/modeOperation"
              }
            }
          },
          "required": [
            "name",
            "instructions"
          ],
          "additionalProperties": false
        },
        "modeOperation": {
          "title": "ModeOperation",
          "description": "An operation used when changing between modes -- exactly one of 'send_input' or 'send_prompted_input'.",
          "type": "object",
          "oneOf": [
            {
              "properties": {
                "send_input": {
                  "$ref": "#/$defs/sendInput"
                }
              },
              "required": [
                "send_input"
              ],
              "additionalProperties": false
            },
            {
              "properties": {
                "send_prompted_input": {
                  "$ref": "#/$defs/sendPromptedInput"
                }
              },
              "required": [
                "send_prompted_input"
              ],
              "additionalProperties": false
            }
          ]
        },
        "onXInstruction": {
          "title": "OnXInstruction",
          "description": "An instruction usable in on open/close instruction lists -- exactly one of 'write', 'enter_mode', 'send_input', or 'send_prompted_input'.",
          "type": "object",
          "oneOf": [
            {
              "properties": {
                "write": {
                  "$ref": "#/$defs/write"
                }
              },
              "required": [
                "write"
              ],
              "additionalProperties": false
            },
            {
              "properties": {
                "enter_mode": {
                  "$ref": "#/$defs/enterMode"
                }
              },
              "required": [
                "enter_mode"
              ],
              "additionalProperties": false
            },
            {
              "properties": {
                "send_input": {
                  "$ref": "#/$defs/sendInput"
                }
              },
              "required": [
                "send_input"
              ],
              "additionalProperties": false
            },
            {
              "properties": {
                "send_prompted_input": {
                  "$ref": "#/$defs/sendPromptedInput"
                }
              },
              "required": [
                "send_prompted_input"
              ],
              "additionalProperties": false
            }
          ]
        },
        "write": {
          "title": "Write",
          "description": "Write the given input to the session without waiting for a prompt (a return is sent after the input).",
          "type": "object",
          "properties": {
            "input": {
              "type": "string"
            }
          },
          "required": [
            "input"
          ],
          "additionalProperties": false
        },
        "enterMode": {
          "title": "EnterMode",
          "description": "Enter the requested mode.",
          "type": "object",
          "properties": {
            "requested_mode": {
              "type": "string"
            }
          },
          "required": [
            "requested_mode"
          ],
          "additionalProperties": false
        },
        "sendInput": {
          "title": "SendInput",
          "description": "Send the given input and wait for the prompt to return.",
          "type": "object",
          "properties": {
            "input": {
              "type": "string"
            }
          },
          "required": [
            "input"
          ],
          "additionalProperties": false
        },
        "sendPromptedInput": {
          "title": "SendPromptedInput",
          "description": "Send an input that triggers a secondary prompt (e.g. 'enable' asking for a password) and respond to it. One of 'prompt_exact' or 'prompt_pattern' should be set.",
          "type": "object",
          "properties": {
            "input": {
              "type": "string"
            },
            "prompt_exact": {
              "description": "Exact string of the expected secondary prompt.",
              "type": [
                "string",
                "null"
              ]
            },
            "prompt_pattern": {
              "description": "PCRE2 pattern matching the expected secondary prompt.",
              "type": [
                "string",
                "null"
              ]
            },
            "response": {
              "description": "Response to send when the secondary prompt is seen.",
              "type": "string"
            }
          },
          "required": [
            "input",
            "response"
          ],
          "additionalProperties": false
        }
      }
    }
    ```

#### Lookups

A quick note about "lookups"... Lookups basically exist so that you can specify how to enter some
mode of the cli that is "privileged" and requires credentials to escalate into (i.e. "enable" to
get into privileged exec mode in cisco/arista style platforms). The definition should obviously not
include hard coded credentials in anything other than some lab/test scenario, so we provide this
lookup functionality to wire those credentials into the definition. A simple example in python and
go:

```python
c = Cli(
    host="localhost",
    auth_options=AuthOptions(
        username="foo",
        password="bar",
        lookups=[LookupKeyValue(key="enable", value="baz")],
    ),
)
```

```go
c, err := cli.NewCli(
	"localhost",
	scrapligooptions.WithUsername("foo"),
	scrapligooptions.WithPassword("bar"),
	scrapligooptions.WithLookupKeyValue("enable", "baz"),
)
```


### Async IO

Scrapli has always been an async friendly library -- the first bit of this was the native async/await support in scrapli (py), and of course scrapligo is effectively natively asynchronous thanks to the go runtime. This tradition continues in libscrapli, however the realization is a little bit different!

libscrapli runs a pthread for the "read loop" -- that is the loop that is constantly consuming from the transport and staging the read bytes into a queue. The transports themselves all operate in a non-blocking fashion and leverage an epoll/kqueue waiter to await readable data. This implementation gives us the best of all worlds where we do not need to have super tight read loops to continually read bytes from a connection while still allowing us to have cancellable reads (by awakaing the epoll/kqueue waiter).

When scrapli/scrapligo call into the libscrapli backend something similar happens -- tasks are queued and are pollable via an operation ID. In async Python operation and normal Go operations, these operations are awaited on by calling select on a file descriptor allocated to be used to notify the higher level language when an operation is complete. In synchronous Python operation, the operation is simply polled on an interval with a simple backoff timer.

The end result is that libscrapli is reasonably efficient no matter the way you chose to consume from it -- synchronous or asynchronous Python, or natively asynchronous Go.


## Methods

This section outlines the methods available on the Cli and Netconf drivers -- each section briefly outlines the usage of the method, and shows the method name for Zig, Python, and Go versions.


### Cli

#### Get Prompt

Fetches the current "prompt" from the device -- this is based on the regular expression pattern used to find the prompt for the given definition/platform you are using to connect to the server.

- zig: `getPrompt`
- python: `get_prompt` / `get_prompt_async`
- go: `GetPrompt`


#### Enter Mode

Enter the given "mode" on the server -- this can be things like "configuration" or "privileged-exec" type modes -- the modes themselves are define din the platform definition, so consult the definition for available modes.

- zig: `enterMode`
- python: `enter_mode` / `enter_mode_async`
- go: `EnterMode`


#### Send Input

Send a given input to the device. This input will be sent at the "default" mode for the given platform unless otherwise specified -- meaning, if you want to send a "configuration" you will need to use this method, and specify the configuration mode!

- zig: `sendInput`
- python: `send_input` / `send_input_async`
- go: `SendInput`


#### Send Inputs

The same as send input, but, for multiple inputs.

- zig: `sendInputs`
- python: `send_inputs` / `send_inputs_async`
- go: `SendInputs`


#### Send Prompted Input

Used to deal with "prompts" -- things like "are you sure you want to do this enter y for yes, or n for no" kind of things. This method accepts an input, then an exact or regular expression prompt pattern to "expect", finally, an input to respond to the prompt with.

- zig: `sendPromptedInput`
- python: `send_prompted_input` / `send_prompted_input_async`
- go: `SendPromptedInput`


#### Read With Callbacks

This method is a bit more of an advanced method -- it accepts an optional input to "start" the operation, then a list of callbacks with information about how those callbacks should be triggered. The original impetus for this method was for connecting to devices via console server and handling initial config dialogs, however of course it can be used in other ways as well!

- zig: `readWithCallbacks`
- python: `read_with_callbacks` / `read_with_callbacks_async`
- go: `ReadWithCallbacks`


### Netconf

#### Raw RPC

A method to send a "raw" rpc -- that is an rpc of your own creation. This method allows you to use scrapli for rpcs that scrapli does not natively support -- especially useful for subscriptions etc..

- zig: `rawRpc`
- python: `raw_rpc` / `raw_rpc_async`
- go: `RawRpc`


#### Get Config

The get-config RPC. Nothing too exciting to say here!

- zig: `getConfig`
- python: `get_config` / `get_config_async`
- go: `GetConfig`


#### Edit Config

The edit-config RPC. Of course this expects the payload, optionally the target datastore and some other options.

- zig: `editConfig`
- python: `edit_config` / `edit_config_async`
- go: `EditConfig`


#### Copy Config

Copy the config from one datastore to another.

- zig: `copyConfig`
- python: `copy_config` / `copy_config_async`
- go: `CopyConfig`


#### Delete Config

Delete a config in a datastore.

- zig: `deleteConfig`
- python: `delete_config` / `delete_config_async`
- go: `DeleteConfig`


#### Lock

Lock a given datastore.

- zig: `lock`
- python: `lock` / `lock_async`
- go: `Lock`


#### Unlock

Unlock a given datastore.

- zig: `unlock`
- python: `unlock` / `unlock_async`
- go: `Unlock`


#### Get

Perform a get RPC against the target server.

- zig: `get`
- python: `get` / `get_async`
- go: `Get`


#### Close Session

Nicely close the session -- typically you don't need to call this as the `close` method will handle it for you.

- zig: `closeSession`
- python: `close_session` / `close_session_async`
- go: `CloseSession`


#### Kill Session

Kill another session, you must provide the session ID to kill.

- zig: `killSession`
- python: `kill_session` / `kill_session_async`
- go: `KillSession`


#### Commit

Commit pending changes in a datastore.

- zig: `commit`
- python: `commit` / `commit_async`
- go: `Commit`


#### Discard

Discard pending changes in a datastore.

- zig: `discard`
- python: `discard` / `discard_async`
- go: `Discard`


#### Cancel Commit

Cancel a pending commit operation.

- zig: `cancelCommit`
- python: `cancel_commit` / `cancel_commit_async`
- go: `CancelCommit`


#### Validate

Validate the contents of a datastore.

- zig: `validate`
- python: `validate` / `validate_async`
- go: `Validate`


#### Get Schema

Fetch a schema from the server.

- zig: `getSchema`
- python: `get_schema` / `get_schema_async`
- go: `GetSchema`


#### Get Data

Execute the get-data RPC.

- zig: `getData`
- python: `get_data` / `get_data_async`
- go: `GetData`


#### Edit Data

Execute the edit-data RPC.

- zig: `editData`
- python: `edit_data` / `edit_data_async`
- go: `EditData`


#### Action

Execute the action RPC on the server.

- zig: `action`
- python: `action` / `action_async`
- go: `Action`
