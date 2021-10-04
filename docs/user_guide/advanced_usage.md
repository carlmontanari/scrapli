# Advanced Usage


## All Driver Arguments

The basic usage section outlined the most commonly used driver arguments, please see the following pages to see all 
supported driver arguments:

- [Base `Driver` Arguments](https://carlmontanari.github.io/scrapli/api_docs/driver/base_driver/) 
- [`GenericDriver` Arguments](https://carlmontanari.github.io/scrapli/api_docs/driver/generic_driver/) 
- [`NetworkDriver` Arguments](https://carlmontanari.github.io/scrapli/api_docs/driver/network_driver/) 

Most of these attributes actually get passed from the `Driver` (or sub-class such as `NXOSDriver`) into the
 `Transport` and `Channel` classes, so if you need to modify any of these values after instantiation you should do so
  on the appropriate object -- i.e. `conn.channel.comms_prompt_pattern`.


## Platform Regex

Due to the nature of Telnet/SSH there is no good way to know when a command has completed execution. Put another way
, when sending any command, data is returned over a socket, that socket doesn't ever tell us when it is "done
" sending the output from the command that was executed. In order to know when the session is "back at the base
 prompt/starting point" scrapli uses a regular expression pattern to find that base prompt.

This pattern is contained in the `comms_prompt_pattern` setting or is created by joining all possible prompt patterns
 in the privilege levels for a "core" device type. In general, you should *not* change the patterns unless you have a
  good reason to do so!

The "base" `Driver` (default, but changeable) pattern is:

`"^[a-z0-9.\-@()/:]{1,48}[#>$]\s*$"`

*NOTE* all `comms_prompt_pattern` "should" use the start and end of line anchors as all regex searches in scrapli are
 multi-line (this is an important piece to making this all work!). While you don't *need* to use the line anchors its
  probably a really good idea! Also note that most devices seem to leave at least one white space after the final
   character of the prompt, so make sure to account for this! Last important note -- the core drivers all have reliable
    patterns set for you, so you hopefully don't need to bother with this too much!

The above pattern works on all "core" platforms listed above for at the very least basic usage. Custom prompts or
 host names could in theory break this, so be careful!

If you use a platform driver, the base prompt is set in the driver, so you don't really need to worry about this!

The `comms_prompt_pattern` pattern can be changed at any time at or after instantiation of a scrapli object, and is
 done so by modifying `conn.channel.comms_prompt_pattern` where `conn` is your scrapli connection object. Changing
 this *can* break things though, so be careful! If using any `NetworkDriver` sub-classes you should modify the
  privilege level(s) if necessary, and *not* the `comms_prompt_pattern`.


## On Open

Lots of times when connecting to a device there are "things" that need to happen immediately after getting connected
. In the context of network devices the most obvious/common example would be disabling paging (i.e. sending `terminal
 length 0` on a Cisco-type device). While scrapli `Driver` (the base driver) and `GenericDriver` do not know or care
  about disabling paging or any other on connect type activities, scrapli of course provides a mechanism for allowing
   users to handle these types of tasks. Even better yet, if you are using any of the core drivers (`IOSXEDriver
   `, `IOSXRDriver`, etc.), scrapli will automatically have some sane default "on connect" actions (namely disabling
    paging).

If you were so inclined to create some of your own "on connect" actions, you can simply pass those to the `on_open
` argument of `Scrape` or any of its sub-classes (`NetworkDriver`, `IOSXEDriver`, etc.). The value of this argument
 must be a callable that accepts the reference to the connection object. This allows for the user to send commands or
  do really anything that needs to happen prior to "normal" operations. The core network drivers disable paging
   functions all call directly into the channel object `send_input` method -- this is a good practice to follow as
    this will avoid any of the `NetworkDriver` overhead such as trying to attain privilege levels -- things like this
     may not be "ready" until *after* your `on_open` function is executed.
  
Below is an example of creating an "on connect" function and passing it to scrapli. Immediately after authentication
 is handled this function will be called and disable paging (in this example):
    
```python
from scrapli.driver.core import IOSXEDriver

def iosxe_disable_paging(conn):
    conn.channel.send_input("term length 0")

my_device = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
    "on_open": iosxe_disable_paging
}

with IOSXEDriver(**my_device) as conn:
    print(conn.get_prompt())
```

Note that this section has talked almost exclusively about disabling paging, but any other "things" that need to
 happen in the channel can be handled here. If there is a prompt/banner to accept you should be able to handle it
  here. The goal of this "on connect" function is to allow for lots of flexibility for dealing with whatever needs to
   happen for devices -- thus decoupling the challenge of addressing all of the possible options from scrapli itself
    and allowing users to handle things specific for their environment.

Lastly, while the `on_open` method should be synchronous or asyncio depending on the driver -- meaning that if using
 an async driver, it will await the `on_open` callable, so it must be asynchronous!


## On Close

As you may have guessed, `on_close` is very similar to `on_open` with the obvious difference that it happens just
 prior to disconnecting from the device. Just like `on_open`, `on_close` functions should accept a single argument
  that is a reference to the object itself. As with most things scrapli, there are sane defaults for the `on_close
  ` functions, but you are welcome to override them with your own function if you so chose! 


## Timeouts

scrapli supports several timeout options:

- `timeout_socket`
- `timeout_transport`
- `timeout_ops`
 
`timeout_socket` is exactly what it sounds where possible. For the ssh2 and paramiko transports we create our own
 socket and pass this to the created object (paramiko or ssh2 object). The socket is created with the timeout value
  set in the `timeout_socket` attribute. For telnet and system transports we do not create a socket ourselves so this
   value is used slightly differently.

For telnet, the `timeout_socket` is used as the timeout for telnet session creation. After the telnet session is
 created the timeout is reset to the `timeout_transport` value (more on that in a second).
 
For system transport, `timeout_socket` governs the `ConnectTimeout` ssh argument -- which seems to be very similar to
 socket timeout in paramiko/ssh2.

`timeout_transport` is intended to govern the timeout for the actual transport mechanism itself. For paramiko and
 ssh2, this is set to the respective libraries timeout attributes. For telnet, this is set to the telnetlib timeout
  value after the initial telnet session is stood up. For system transport, this value is used as the timeout value
   for read and write operations (handled by operation timeout decorator). 
 
Finally, `timeout_ops` sets a timeout value for individual operations -- or put another way, the timeout for each
 send_input operation.



## Driver Privilege Levels

The "core" drivers understand the basic privilege levels of their respective device types. As mentioned previously
, the drivers will automatically attain the "privilege_exec" (or equivalent) privilege level prior to executing "show
" commands. If you don't want this "auto-magic" you can use the base driver (`Driver`) or the `GenericDriver`. The
 privileges for each device are outlined in the platforms `driver.py` file - each privilege is an object of the base
  `PrivilegeLevel` class which uses slots for the attributes. This used to be a named tuple, however as this was
   immutable it was a bit of a pain for users to modify things on the fly. 
 
As an example, the following privilege levels are supported by the `IOSXEDriver`:

1. "exec"
2. "privilege_exec"
3. "configuration"

Each privilege level has the following attributes:

- pattern: regex pattern to associate prompt to privilege level with
- name: name of the priv level, i.e. "exec"
- previous_priv: name of the "lower"/"previous" privilege level
- deescalate: command used to deescalate *from* this privilege level (or an empty string if no lower privilege)
- escalate: command used to escalate *to* this privilege level (from the lower/previous privilege)
- escalate_auth: True/False there is auth required to escalate to this privilege level
- escalate_prompt: pattern to expect when escalating to this privilege level, i.e. "Password:" or any empty string

If you wish to manually enter a privilege level you can use the `acquire_priv` method, passing in the name of the
 privilege level you would like to enter. In general, you probably won't need this too often though as the driver
  should handle much of this for you.

```python
from scrapli.driver.core import IOSXEDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
}
with IOSXEDriver(**my_device) as conn:
    conn.acquire_priv("configuration")
```


### Configure Exclusive and Configure Private (IOSXR/Junos)
 
IOSXR and Junos platforms have different configuration modes, such as "configure exclusive" or "configure private
". These alternate configuration modes are represented as a privilege level just like the "regular" configuration
 mode. You can acquire an "exclusive" configuration session on IOSXR as follows:
 
```python
from scrapli.driver.core import IOSXRDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
}
with IOSXRDriver(**my_device) as conn:
    conn.acquire_priv("configuration_exclusive")
```

Of course you can also pass this privilege level name to the `send_configs` or `send_configs_from_file` methods as well:

```python
from scrapli.driver.core import IOSXRDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
}
with IOSXRDriver(**my_device) as conn:
    conn.send_configs(configs=["configure things"], privilege_level="configuration_exclusive")
```

Note that the name of the privilege level is "configuration_exclusive" -- don't forget to write the whole thing out!
 

### Configure Session (EOS/NXOS)

EOS and NXOS devices support configuration "sessions", these sessions are a little bit of a special case for scrapli
. In order to use a configuration session, the configuration session must first be "registered" with scrapli -- this
 is so that scrapli can create a privilege level that is mapped to the given config session/config session name
 . The `register_configuration_session` method that accepts a string name of the configuration session you would like
  to create -- note that this method raises a `NotImplementedError` for platforms that do not support config sessions
  . The`register_configuration_session` method creates a new privilege level for you and updates the transport class
   with the appropriate information internally (see next section). An example of creating a session for an EOS device
    called "my-config-session" can be seen here:
    
```python
from scrapli.driver.core import EOSDriver

my_device = {
    "host": "172.18.0.14",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_secondary": "VR-netlab9",
    "auth_strict_key": False,
}
with EOSDriver(**my_device) as conn:
    conn.register_configuration_session(session_name="my-config-session")
    print(conn.privilege_levels["my-config-session"])
    print(conn.privilege_levels["my-config-session"].name)
    print(conn.privilege_levels["my-config-session"].pattern)
``` 

```
<scrapli.driver.network_driver.PrivilegeLevel object at 0x7fca10070820>
my-config-session
^[a-z0-9.\-@/:]{1,32}\(config\-s\-my\-con[a-z0-9_.\-@/:]{0,32}\)#\s?$
```


### Modifying Privilege Levels

When creating a configuration session, or modifying a privilege level during runtime, scrapli needs to update some
 internal arguments in order to always have a full "map" of how to escalate/deescalate, as well as to be able to
  match prompts based on any/all of the patterns available in the privilege levels dictionary. The
   `register_configuration_session` method will automatically handle updating these internal arguments, however if
    you modify any of the privilege levels (or add a priv level on the fly without using the register method) then
     you will need to manually call the `update_privilege_levels` method. 


## Using `Driver` Directly

All examples in this readme have shown using the "core" network drivers such as `IOSXEDriver`. These core network
 drivers are actually sub-classes of an ABC called `NetworkDriver` which itself is a sub-class of the `GenericDriver
 ` which is a sub-class of the base `Scrape` class -- the namesake for this library. The `Driver` object can be used
  directly if you prefer to have a much less opinionated or less "auto-magic" type experience. `Driver` does not
   provide the same `send_command`/`send_commands`/`send_configs` methods, nor does it disable paging, or handle any
    kind of privilege escalation/de-escalation. `Driver` is a much more basic "paramiko"-like experience. Below is a
     brief example of using the `Driver` object directly:
   
```python
from scrapli import Driver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
}

with Driver(**my_device) as conn:
    conn.channel.send_input("terminal length 0")
    response = conn.channel.send_input("show version")
```

Without the `send_command` and similar methods, you must directly access the `Channel` object when sending inputs
 with `Scrape`.


## Using the `GenericDriver`

Using the `Driver` driver directly is nice enough, however you may not want to have to change the prompt pattern, or
 deal with accessing the channel to send commands to the device. In this case there is a `GenericDriver` available to
  you. This driver has a *very* broad pattern that it matches for base prompts, has no concept of disabling paging or
   privilege levels (like `Driver`), but does provide `send_command`, `send_commands`, `send_interactive`, and
    `get_prompt` methods for a more NetworkDriver-like experience. 

Hopefully this `GenericDriver` can be used as a starting point for devices that don't fall under the core supported
 platforms list.
   
```python
from scrapli.driver import GenericDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
}

with GenericDriver(**my_device) as conn:
    conn.send_command("terminal length 0")
    response = conn.send_command("show version")
    responses = conn.send_commands(["show version", "show run"])
```


## Using a Different Transport

scrapli is built to be very flexible, including being flexible enough to use different libraries for "transport
" -- or the actual Telnet/SSH communication. By default, scrapli uses the "system" transport which quite literally
 uses the ssh binary on your system (`/usr/bin/ssh`). This "system" transport means that scrapli has no external
  dependencies as it just relies on what is available on the machine running the scrapli script.

In the spirit of being highly flexible, scrapli allows users to swap out this "system" transport with another
 transport mechanism. The other supported transport plugins are `paramiko`, `ssh2-python`, `telnetlib
 `, `asyncssh`, and `asynctelnet`. The transport selection can be made  when instantiating the 
scrapli connection object by passing in `paramiko`, `ssh2`, `telnet`, `asyncssh`, or `asynctelnet` to force  scrapli 
to use the corresponding transport mechanism. If you are using one of the async transports you must use an async driver!
  
While it will be a goal to ensure that these other transport mechanisms are supported and useful, the focus of
 scrapli development will be on the "system" SSH transport.
 
Example using `paramiko` as the transport:

```python
from scrapli.driver.core import IOSXEDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
    "transport": "paramiko"
}

with IOSXEDriver(**my_device) as conn:
    print(conn.get_prompt())
```

Currently, the only reason I can think of to use anything other than "system" as the transport would be to test
 scrapli on a Windows host, to use telnet, to use ssh2 for super speed, or to use asyncio. If there are other good
  reasons please do let me know!


## Auth Bypass

*NOTE* only supported with system and telnet transports!

Some devices, such as Cisco WLC, have no "true" SSH authentication, and instead prompt for credentials (or perhaps
 not even that) after session establishment. In order to cope with this corner case, the `auth_bypass` flag can be
  set to `True` which will cause scrapli to skip all authentication steps. Typically, this flag would be set and a
   custom `on_open` function set to handle whatever prompts the device has upon SSH session establishment.

See the [non core device example](https://github.com/carlmontanari/scrapli/tree/master/examples/non_core_device/wlc.py) to see this in action.


## Transport Options

Because each transport has different options/features available, it doesn't make sense to try to put all possible
 arguments in the `Driver` or `NetworkDriver` drivers, to address this an argument `transport_options` has been added
 . This is exactly what it sounds like -- arguments that can be passed to the selected transport class. As these
  arguments will be transport-specific, please check the docs/docstrings for your preferred transport to see what is
   available.
   
A simple example of passing additional SSH arguments to the `SystemSSHTransport` class is available
 [here](https://github.com/carlmontanari/scrapli/tree/master/examples/transport_options/system_ssh_args.py).


## Raise For Status

The scrapli `Response` and `MultiResponse` objects both contain a method called `raise_for_status`. This method's
 purpose is to provide a very simple way to raise an exception if any of the commands or configs sent in a method
  have failed. 
 
```python
from scrapli.driver.core import IOSXEDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
}

with IOSXEDriver(**my_device) as conn:
    commands = ["show run", "tacocat", "show version"]
    responses = conn.send_commands(commands=commands)
```

Inspecting the `responses` object from the above example, we can see that it indeed is marked as `Success: False`, even
 though the first and last commands were successful:

```python
>>> responses
MultiResponse <Success: False; Response Elements: 3>
>>> responses[0]
Response <Success: True>
>>> responses[1]
Response <Success: False>
>>> responses[2]
Response <Success: True>
```

Finally, we can all the `raise_for_status` method to have scrapli raise the `ScrapliCommandFailure` exception if any
 of the configs/commands failed:
 
```python
>>> responses.raise_for_status()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/Users/carl/dev/github/scrapli/scrapli/response.py", line 270, in raise_for_status
    raise ScrapliCommandFailure()
scrapli.exceptions.ScrapliCommandFailure
```
