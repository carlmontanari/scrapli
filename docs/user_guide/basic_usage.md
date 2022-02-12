# Basic Usage


## Picking the right Driver

Assuming you are using scrapli to connect to one of the five "core" platforms, you should almost always use the
 provided corresponding "core" driver. For example if you are connecting to an Arista EOS device, you should use the
  `EOSDriver`. You can select this driver "manually" or using the scrapli factory `Scrapli` (or the async scrapli
   factory `AsyncScrapli`).

Importing your driver manually looks like this:

```python
from scrapli.driver.core import EOSDriver
```

If you are using asyncio, you can use the async variant of the driver:

```python
from scrapli.driver.core import AsyncEOSDriver
```


The core drivers and associated platforms are outlined below:

| Platform/OS   | Scrapli Driver  | Scrapli Async Driver | Platform Name |
|---------------|-----------------|----------------------|---------------|
| Cisco IOS-XE  | IOSXEDriver     | AsyncIOSXEDriver     | cisco_iosxe   |
| Cisco NX-OS   | NXOSDriver      | AsyncNXOSDriver      | cisco_nxos    |
| Cisco IOS-XR  | IOSXRDriver     | AsyncIOSXRDriver     | cisco_iosxr   |
| Arista EOS    | EOSDriver       | AsyncEOSDriver       | arista_eos    |
| Juniper JunOS | JunosDriver     | AsyncJunosDriver     | juniper_junos |

All drivers can be imported from `scrapli.driver.core`.

If you would rather use the factory class to dynamically select the appropriate driver based on a platform string (as
 seen in the above table), you can do so as follows:

```python
from scrapli import Scrapli

device = {
   "host": "172.18.0.11",
   "auth_username": "scrapli",
   "auth_password": "scrapli",
   "auth_strict_key": False,
   "platform": "cisco_iosxe"
}

conn = Scrapli(**device)
conn.open()
print(conn.get_prompt())
```

Note that the `Scrapli` and `AsyncScrapli` classes inherit from the `NetworkDriver` and `AsyncNetworkDriver` classes
 respectively, so all editor code completion and type indicating behavior should work nicely! For non "core
 " platforms please see the [scrapli_community project](https://github.com/scrapli/scrapli_community).

If you are working with a platform not listed above (and/or is not in the scrapli community project), you have three
 options: 

1. You can use the (base)`Driver` driver directly, which you can read about [here](https://carlmontanari.github.io/scrapli/user_guide/advanced_usage/#using-driver-directly)
2. You can use the `GenericDriver` which you can read about [here](https://carlmontanari.github.io/scrapli/user_guide/advanced_usage/#using-the-genericdriver)
3. You can use the `NetworkDriver` which is similar to option 2 but you will need to understand/provide privilege
/prompt information so scrapli can properly escalate/deescalate to/from configuration (or other) modes.

In general you should probably simply create a scrapli community platform (read about adding a platform
 [here](https://github.com/scrapli/scrapli_community#adding-a-platform), but failing that the `GenericDriver` is
  probably the simplest path forward.

Note: if you are using async you *must* set the transport to `asyncssh` or `asynctelnet`!


## Basic Driver Arguments

The drivers of course need some information about the device you are trying to connect to. The most common arguments
 to provide to the driver are outlined below:
 
| Argument         | Purpose/Value                                               |
|------------------|-------------------------------------------------------------|
| host             | name/ip of host to connect to                               |
| port             | port of host to connect to (defaults to port 22)            |
| auth_username    | username for authentication                                 |
| auth_password    | password for authentication                                 |
| auth_secondary   | password for secondary authentication (enable password)     |
| auth_private_key | private key for authentication                              |
| auth_strict_key  | strict key checking -- TRUE by default!                     |
| ssh_config_file  | True/False or path to ssh config file to use                |

These arguments may be passed as keyword arguments to the driver of your choice, or, commonly are passed via
 dictionary unpacking as show below:
 
```python
from scrapli.driver.core import IOSXRDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
}

conn = IOSXRDriver(**my_device)
conn.open()
```

*NOTE* that scrapli enables strict host key checking by default!


## Opening and Closing a Connection

scrapli does *not* open the connection for you when creating your scrapli connection object in normal operations, you
 must manually call the `open` method prior to sending any commands to the device as shown below.

```python
from scrapli.driver.core import IOSXRDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
}

conn = IOSXRDriver(**my_device)
conn.open()
response = conn.send_command("show version")
```

Connections can be closed by calling the `close` method:

```python
conn.close()
```

scrapli also supports using a context manager (`with` block), when using the context manager the connection will be
 automatically opened and closed for you. 

```python
from scrapli.driver.core import IOSXEDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
}

with IOSXEDriver(**my_device) as conn:
    response = conn.send_command("show version")
```


## Sending Commands

When using any of the core network drivers (`JunosDriver`, `EOSDriver`, etc.) or the `GenericDriver`, the `send_command
` and `send_commands` methods will respectively send a single command or list of commands to the device.

When using the core network drivers, the command(s) will be sent at the `default_desired_privilege_level` level which is
 typically "privilege exec" (or equivalent) privilege level. Please see [Driver Privilege Levels](https://carlmontanari.github.io/scrapli/user_guide/advanced_usage/#driver-privilege-levels)
  in the advanced usage section for more details on privilege levels. As the `GenericDriver` doesn't know or
  care about privilege levels you would need to manually handle acquiring the appropriate privilege level for you
   command yourself if using that driver.

Note the different methods for sending a single command versus a list of commands!

```python
from scrapli.driver.core import IOSXEDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
}

conn = IOSXEDriver(**my_device)
conn.open()
response = conn.send_command("show version")
responses = conn.send_commands(["show run", "show ip int brief"])
```

Finally, if you prefer to have a file containing a list of commands to send, there is a `send_commands_from_file` method
. This method excepts the provided file to have a single command to send per line in the file.


## Response Object

All command/config operations that happen in the `GenericDriver` or any of the drivers inheriting from the
 `NetworkDriver` result in a `Response` object being created. The `Response` object contains attributes for the
  command sent (`channel_input`), start/end/elapsed time, and of course the result of the command sent.

```python
from scrapli.driver.core import IOSXEDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
}

conn = IOSXEDriver(**my_device)
conn.open()
response = conn.send_command("show version")
print(response.elapsed_time)
print(response.result)
```

If using `send_commands` (plural!) then scrapli will return a `MultiResponse` object containing multiple `Response`
 objects. The `MultiResponse` object is for all intents and purposes just a list of `Response` objects (with a few
  very minor differences).

In addition to containing the input and output of the command(s) that you sent, the `Response` object also contains a
 method `textfsm_parse_output` (for more on TextFSM support see
 [Textfsm/NTC-Templates Integration](#textfsmntc-templates-integration)) which will attempt to parse and return the
  received output. If parsing fails, the value returned will be an empty list -- meaning you will *always* get
   "structured data" returned, however it will just be an empty object if parsing fails.
   
```python
>>> structured_result = response.textfsm_parse_output()
>>> print(structured_result)
[['16.4.1', 'IOS-XE', 'csr1000v', '2 days, 22 hours, 10 minutes', 'reload', 'packages.conf', ['CSR1000V'], ['9FKLJWM5EB0'], '0x2102', []]]
```


## Sending Configurations

When using any of the core drivers, you can send configurations via the `send_config`, `send_configs` or
 `send_configs_from_file` methods which will handle privilege escalation for you. `send_config` accepts a single
  string, `send_configs` accepts a list of strings, and of course `send_configs_from_file` accepts a string path to a
   file containing configurations to send. Note that `send_configs_from_file` -- just like with it's commands sibling
    -- will treat each line in the file as a configuration element, in this way it behaves much like `send_configs`.

Lastly, it is good to know that `send_config` (singular!) will parse the configuration string provided and split it
 into lines -- this means that the underlying behavior is the same as `send_configs`, however this method returns a
  single `Response` object. This `send_config` method can be used to send entire configurations to devices in a
   reliable fashion.

```python
from scrapli.driver.core import IOSXEDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
}

with IOSXEDriver(**my_device) as conn:
    conn.send_configs(["interface loopback123", "description configured by scrapli"])
```

If you need to get into any kind of "special" configuration mode, such as "configure exclusive", "configure private
", or "configure session XYZ", you can pass the name of the corresponding privilege level via the `privilege_level
` argument. Please see the [Driver Privilege Levels](https://carlmontanari.github.io/scrapli/user_guide/advanced_usage/#driver-privilege-levels) section for more details!

Lastly, note that scrapli does *not* exit configuration mode at completion of a "configuration" event -- this is
 because scrapli (with the Network drivers) will automatically acquire `default_desired_privilege_level` before
  sending a "command" -- so there is no need, from a scrapli perspective, to explicitly exit config mode at end of
   the configuration session.


## Textfsm/NTC-Templates Integration

scrapli supports parsing output with TextFSM and ntc-templates. This of course requires installing TextFSM and having
 ntc-templates somewhere on your system. When using a platform driver (i.e. `IOSXEDriver`) the textfsm-platform will be
 set for you (based on the driver device type). If you wish to parse the output of your send commands, you can use the
  `textfsm_parse_output` method of the response object. This method will attempt to find the template for you
   -- based on the textfsm-platform and the channel-input (the command sent). If textfsm parsing succeeds, the
    structured result is returned. If textfsm parsing fails, an empty list is returned.

```python
from scrapli.driver.core import IOSXEDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
}

with IOSXEDriver(**my_device) as conn:
    response = conn.send_command("show version")
    structured_result = response.textfsm_parse_output()
    print(structured_result)
```

scrapli also supports passing in templates manually (meaning not using the pip installed ntc-templates directory to
 find templates) if desired. The `textfsm_parse_output` method and `scrapli.helper.textfsm_parse` function both accepts a string or loaded (TextIOWrapper
 ) template and output to parse. This can be useful if you have custom or one off templates or don't want to pip
  install ntc-templates.
  
```python
from scrapli.driver.core import IOSXEDriver
from scrapli.helper import textfsm_parse

my_device = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
}

with IOSXEDriver(**my_device) as conn:
    response = conn.send_command("show version")
    structured_result = textfsm_parse("/path/to/my/template", response.result)
```

*NOTE*: If a template does not return structured data an empty list will be returned!

*NOTE*: Textfsm and ntc-templates is an optional extra for scrapli; you can install these modules manually or using
 the optional extras install via pip:
 
`pip install scrapli[textfsm]`


## Cisco Genie Integration

Very much the same as the textfsm/ntc-templates integration, scrapli has optional integration with Cisco's PyATS
/Genie parsing library for parsing show command output. While there are parsers for non-Cisco platforms, this is
 currently just an option for Cisco platforms within scrapli.

```python
from scrapli.driver.core import IOSXEDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
}

with IOSXEDriver(**my_device) as conn:
    response = conn.send_command("show version")
    structured_result = response.genie_parse_output()
    print(structured_result)
```

*NOTE*: If a parser does not return structured data an empty list will be returned!

*NOTE*: PyATS and Genie is an optional extra for scrapli; you can install these modules manually or using
 the optional extras install via pip:
 
`pip install scrapli[genie]`


## TTP Integration

The scrapli response object also contains a `ttp_parse_output` method, that, as you may have guessed, uses the 
 [ttp](https://github.com/dmulyalin/ttp) library to parse output received from the device. Other than the obvious
  difference that this is in fact a different type of parser, the only difference from a usage perspective is that
   the `ttp_parse_output` method requires a template string, string path to a template, or loaded (TextIOWrapper
   ) template string to be passed. This is because there is no index or mapping of platform:command:template as there
    is with TextFSM/ntc-templates and genie.

An example ttp file (slightly modified from the great ttp quickstart guide) - in this case we'll pretend this file is
 called "my_template.ttp":

```text
interface {{ interface }}
 ip address {{ ip }} {{ mask }}
 description {{ description }}
```

```python
from scrapli.driver.core import IOSXEDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
}

with IOSXEDriver(**my_device) as conn:
    response = conn.send_command("show run interface GigabitEthernet1")
    structured_result = response.ttp_parse_output(template="my_template.ttp")
    print(structured_result)
```

*NOTE*: If a parser does parse data, ttp will return an empty list (as with the other parser methods)

*NOTE*: ttp is an optional extra for scrapli; you can install these modules manually or using the optional extras
 install via pip:
 
`pip install scrapli[ttp]`


## Handling Prompts

In some cases you may need to run an "interactive" command on your device. The `send_interactive` method of the
 `GenericDriver` or its sub-classes (`NetworkDriver` and "core" drivers) can be used to accomplish this. This method
  accepts a list of "interact_events" -- or basically commands you would like to send, and their expected resulting
   prompt. A third, optional, element is available for each "interaction", this last element is a bool that indicates
    weather or not the input that you are sending to the device is "hidden" or obfuscated by the device. This is
     typically used for password prompts where the input that is sent does not show up on the screen (if you as a
      human are sitting on a terminal typing).
      
This method can accept one or N "events" and thus can be used to deal with any number of subsequent prompts. 

One last important item about this method is that it accepts an argument `privilege_level` -- the value of this
 argument should be the name of the privilege level that you would like to execute the interactive command at
 . This is an optional argument, with a default of the `default_desired_privilege_level` attribute which is normally
  "privilege exec" or similar depending on the platform. 

```python
from scrapli.driver.core import IOSXEDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
}

with IOSXEDriver(**my_device) as conn:
    interactive = conn.send_interactive(
        [
            ("copy flash: scp:", "Source filename []?", False),
            ("somefile.txt", "Address or name of remote host []?", False),
            ("172.31.254.100", "Destination username [carl]?", False),
            ("scrapli", "Password:", False),
            ("super_secure_password", "csr1000v#", True),
        ]
    )
```


## Telnet

scrapli supports telnet as a transport driver via the standard library module `telnetlib` or with a custom-built 
async telnet transport (creatively called "asynctelnet") built on the standard library `asycnio`.
 
A few things worth noting:

- You can set the username and password prompt expect string after your connection object instantiation
 and before calling the `open` method -- this means if you have non-default prompts you cannot use scrapli with a
  context manager and Telnet (because the context manager calls open for you). You can set the prompts using the
   following attributes of the `Channel` (or `AsyncChannel`) object:
    - `telnet_username_prompt` which defaults to `^(.*username:)|(.*login:)\s?$`
    - `telnet_password_prompt` which defaults to `^password:\s?$`
 
    You can set these values by updating the appropriate attribute, for example: `conn.channel.telnet_username_prompt = "somethingneat"`. 
  
- If you wish to provide custom prompt values you can provide a string to look for "in" the output from the device, 
  or a regular expression pattern that starts with `^` and ends with `$` -- if you don't use the line anchors the 
    pattern will be `re.escape`'d.
- When using telnet you may need to set the `comms_return_char` to `\r\n` the tests against the core platforms pass
 without this, however it seems that some console server type devices are looking for this `\r\n` pattern instead of
  the default `\n` pattern.


## SSH Config Support

scrapli supports using OpenSSH configuration files in a few ways. For "system" SSH transport (default setting
), passing a path to a config file will simply make scrapli "point" to that file, and therefore use that
 configuration files attributes (because it is just exec'ing system SSH!). You can also pass `True` to let 
scrapli search in system default locations for a ssh config file (`~/.ssh/config` and `/etc/ssh/ssh_config`).

SSH transports other than "system" transport may support *some* subset of the OpenSSH configuration files, but will 
not provide full support. Asyncssh, for example, will automatically pick up and handle proxy-jumps, SSH keys, and 
some other items -- this is a 100% asyncssh feature and has nothing to do with scrapli (other than the fact that 
scrapli allows you to use asyncssh).

*NOTE* -- scrapli does NOT disable strict host checking by default. Obviously this is the "smart" behavior, but it
 can be overridden on a per host basis in your SSH config file, or by passing `False` to the "auth_strict_key
 " argument on object instantiation.

```python
from scrapli.driver.core import IOSXEDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "scrapli",
    "auth_password": "scrapli",
    "auth_strict_key": False,
    "ssh_config_file": "~/my_ssh_config",
}

with IOSXEDriver(**my_device) as conn:
    print(conn.get_prompt())
```
