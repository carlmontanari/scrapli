![](https://github.com/carlmontanari/scrapli/workflows/Weekly%20Build/badge.svg)
[![PyPI version](https://badge.fury.io/py/scrapli.svg)](https://badge.fury.io/py/scrapli)
[![Python 3.6](https://img.shields.io/badge/python-3.6-blue.svg)](https://www.python.org/downloads/release/python-360/)
[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/)
[![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-380/)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)


scrapli
=======

scrapli -- scrap(e c)li --  is a python library focused on connecting to devices, specifically network devices
 (routers/switches/firewalls/etc.) via SSH or Telnet. The name scrapli -- is just "scrape cli" (as in screen scrape)
 squished together! scrapli's goal is to be as fast and flexible, while providing a well typed, well documented
 , simple API.


# Table of Contents

- [Quick Start Guide](#quick-start-guide)
  - [Installation](#installation)
  - [A Simple Example](#a-simple-example)
  - [More Examples](#more-examples)
- [scrapli: What is it](#scrapli-what-is-it)
- [Documentation](#documentation)
- [Supported Platforms](#supported-platforms)
- [Advanced Installation](#advanced-installation)
- [Basic Usage](#basic-usage)
  - [Picking the right Driver](#picking-the-right-driver)
  - [Basic Driver Arguments](#basic-driver-arguments)
  - [Opening and Closing a Connection](#opening-and-closing-a-connection)
  - [Sending Commands](#sending-commands)
  - [Response Object](#response-object)
  - [Sending Configurations](#sending-configurations)
  - [Textfsm/NTC-Templates Integration](#textfsmntc-templates-integration)
  - [Handling Prompts](#handling-prompts)
  - [Telnet](#telnet)
  - [SSH Config Support](#ssh-config-support)
- [Advanced Usage](#advanced-usage)
  - [All Driver Arguments](#all-driver-arguments)
  - [Platform Regex](#platform-regex)
  - [On Connect](#on-connect)
  - [On Exit](#on-exit)
  - [Timeouts](#timeouts)
  - [Driver Privilege Levels](#driver-privilege-levels)
  - [Using Scrape Directly](#using-scrape-directly)
  - [Using a Different Transport](#using-a-different-transport)
- [FAQ](#faq)
- [Transport Notes, Caveats, and Known Issues](#transport-notes-caveats-and-known-issues)
  - [Paramiko](#paramiko)
  - [SSH2-Python](#ssh2-python)
  - [System SSH](#system)
  - [Telnet](#telnet)
- [Linting and Testing](#linting-and-testing)
  - [Linting](#linting)
  - [Testing](#testing)
- [Todo and Roadmap](#todo-and-roadmap)
  - [Todo](#todo)
  - [Roadmap](#roadmap)


# Quick Start Guide

## Installation

In most cases installation via pip is the simplest and best way to install scrapli.
See the below or [here](#advanced-installation) for advanced installation details.

```
pip install scrapli
```

## A Simple Example

```python
from scrapli.driver.core import IOSXEDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
}

conn = IOSXEDriver(**my_device)
conn.open()
response = conn.send_command("show run")
print(response.result)
```

```
$ python my_scrapli_script.py
Building configuration...

Current configuration : 7584 bytes
!
! Last configuration change at 19:24:38 PST Sat Feb 29 2020 by carl
! NVRAM config last updated at 19:00:28 PST Fri Feb 7 2020 by carl
!
version 15.2
service nagle
no service pad
service tcp-keepalives-in
service tcp-keepalives-out
service timestamps debug datetime msec
no service password-encryption
!
<SNIP>
!
end
```

## More Examples

- [Basic "native" Scrape operations](/examples/basic_usage/scrapli_driver.py)
- [Basic "driver" Scrape operations](/examples/basic_usage/iosxe_driver.py)
- [Setting up basic logging](/examples/logging/basic_logging.py)
- [Using SSH Key for authentication](/examples/ssh_keys/ssh_keys.py)
- [Using SSH config file](/examples/ssh_config_files/ssh_config_file.py)


# scrapli: What is it

As stated, scrapli is a python library focused on connecting to devices, specifically network devices via SSH or Telnet.

scrapli is built primarily in three parts: transport, channel, and driver. The transport layer is responsible for
 providing a file-like interface to the target server. The channel layer is responsible for reading and writing
  to the provided file-like interface. Finally, the driver provides the user facing API/interface to scrapli.

There are four available "transports" for the transport layer -- all of which inherit from a base transport class and
 provide the same file-like interface to the upstream channel. The transport options are:

- [paramiko](https://github.com/paramiko/paramiko)
- [ssh2-python](https://github.com/ParallelSSH/ssh2-python)
- OpenSSH/System available SSH
- telnetlib

A good question to ask at this point is probably "why?". Why multiple transport options? Why not just use paramiko
 like most folks do? Historically the reason for moving away from paramiko was simply speed. ssh2-python is a wrapper
  around the libssh2 C library, and as such is very very fast. In a prior project
   ([ssh2net](https://github.com/carlmontanari/ssh2net)), of which scrapli is the successor/evolution, ssh2-python
    was used with great success, however, it is a bit feature-limited, and development seems to have stalled.

This led to moving back to paramiko, which of course is a fantastic project with tons and tons of feature support
. Paramiko, however, does not provide "direct" OpenSSH support (as in -- auto-magically like when you ssh on your
 normal shell), and I don't believe it provides 100% full OpenSSH support either (ex: ControlPersist). Fully
  supporting an OpenSSH config file would be an ideal end goal for scrapli, something that may not be possible with
   Paramiko - ControlPersist in particular is very interesting to me.

With the goal of supporting all of the OpenSSH configuration options the primary transport driver option is simply
 native system local SSH (almost certainly this won't work on Windows, but I don't have a Windows box to test on, or
  any particular interest in doing so). The implementation of using system SSH is of course a little bit messy
  , however scrapli takes care of that for you so you don't need to care about it! The payoff of using system SSH is of
   course that OpenSSH config files simply "work" -- no passing it to scrapli, no selective support, no need to set
    username or ports or any of the other config items that may reside in your SSH config file. This driver
      will likely be the focus of most development for this project, though I will try to keep the other transport
       drivers -- in particular ssh2-python -- as close to parity as is possible/practical.

The last transport is telnet via telnetlib. This was trivial to add in as the interface is basically the same as
 SystemSSH, and it turns out telnet is still actually useful for things like terminal servers and the like!

The final piece of scrapli is the actual "driver" -- or the component that binds the transport and channel together and
 deals with instantiation of an scrapli object. There is a "base" driver object -- `Scrape` -- which provides essentially
  a "raw" SSH (or telnet) connection that is created by instantiating a Transport object, and a Channel object
  . `Scrape` provides (via Channel) read/write methods and not much else -- this should feel familiar if you have
   used paramiko in the past. More specific "drivers" can inherit from this class to extend functionality of the
    driver to make it more friendly for network devices. In fact, there is a `NetworkDriver` abstract base class which
     does just that. This `NetworkDriver` isn't really meant to be used directly though (hence why it is an ABC), but
      to be further extended and built upon instead. As this library is focused on interacting with network devices
      , an example scrapli driver (built on the `NetworkDriver`) would be the `IOSXE` driver -- to, as you may have
       guessed, interact with devices running Cisco's IOS-XE operating system.


# Documentation

Documentation is auto-generated [using pdoc3](https://github.com/pdoc3/pdoc). Documentation is linted (see Linting and
 Testing section) via [pydocstyle](https://github.com/PyCQA/pydocstyle/) and
 [darglint](https://github.com/terrencepreilly/darglint).

Documentation is hosted via GitHub Pages and can be found
[here](https://carlmontanari.github.io/scrapli/docs/scrapli/index.html). You can also view this readme as a web page
 [here](https://carlmontanari.github.io/scrapli/).

To regenerate documentation locally, use the following make command:

```
make docs
```


# Supported Platforms

scrapli "core" drivers cover basically the [NAPALM](https://github.com/napalm-automation/napalm) platforms -- Cisco
 IOS-XE, IOS-XR, NX-OS, Arista EOS, and Juniper JunOS. These drivers provide an interface tailored to network device
  "screen-scraping" rather than just a generic SSH connection/channel. Below are the core driver platforms and
   currently tested version.

- Cisco IOS-XE (tested on: 16.04.01)
- Cisco NX-OS (tested on: 9.2.4)
- Juniper JunOS (tested on: 17.3R2.10)
- Cisco IOS-XR (tested on: 6.5.3)
- Arista EOS (tested on: 4.22.1F)

In the future it would be possible for folks to contribute additional "community" drivers, however, is unlikely that any
 additional "core" platforms would be added.

The "driver" pattern is pretty much exactly like the implementation in NAPALM. The driver extends the base class
 (`Scrape`) and the base networking driver class (`NetworkDriver`) with device specific functionality such as privilege
  escalation/de-escalation, setting appropriate prompts to search for, and picking out appropriate
  [ntc templates](https://github.com/networktocode/ntc-templates) for use with TextFSM, and so on.

All of this is focused on network device type Telnet/SSH cli interfaces, but should work on pretty much any SSH
 connection (though there are almost certainly better options for non-network type devices!). The "base" (`Scrape
 `) connection does not handle any kind of device-specific operations such as privilege escalation or saving
  configurations, it is simply intended to be a bare bones connection that can interact with nearly any device
  /platform if you are willing to send/parse inputs/outputs manually. In most cases it is assumed that users will use
   one of the "core" drivers.

The goal for all "core" devices will be to include functional tests that can run against
[vrnetlab](https://github.com/plajjan/vrnetlab) containers to ensure that the "core" devices are as thoroughly tested
 as is practical. 


# Advanced Installation

As outlined in the quick start, you should be able to pip install scrapli "normally":

```
pip install scrapli
```

To install from this repositories master branch:

```
pip install git+https://github.com/carlmontanari/scrapli
```

To install from this repositories develop branch:

```
pip install -e git+https://github.com/carlmontanari/scrapli.git@develop#egg=scrapli”
```

To install from source:

```
git clone https://github.com/carlmontanari/scrapli
cd scrapli
python setup.py install
```

scrapli has made an effort to have as few dependencies as possible -- in fact to have ZERO dependencies! The "core" of
 scrapli can run with nothing other than standard library! If for any reason you wish to use paramiko or ssh2-python
  as a driver, however, you of course need to install those. These "extras" can be installed via pip:

```
pip install scrapli[paramiko]
```

The available optional installation extras options are:

- paramiko
- ssh2 (ssh2-python)
- textfsm (textfsm and ntc-templates)

As for platforms to *run* scrapli on -- it has and will be tested on MacOS and Ubuntu regularly and should work on any
 POSIX system. Windows is *NOT* tested and will not be supported (officially at least, it may work... not really sure).


# Basic Usage

## Picking the right Driver

Assuming you are using scrapli to connect to one of the five "core" platforms, you should almost always use the
 provided corresponding "core" driver. For example if you are connecting to an Arista EOS device, you should use the
  `EOSDriver`:

```python
from scrapli.driver.core import EOSDriver
```

The core drivers and associated platforms are outlined below:

| Platform/OS   | Scrapli Driver  |
|---------------|-----------------|
| Cisco IOS-XE  | IOSXEDriver     |
| Cisco NX-OS   | NXOSDriver      |
| Cisco IOS-XR  | IOSXRDriver     |
| Arista EOS    | EOSDriver       |
| Juniper JunOS | JunosDriver     |

All drivers can be imported from `scrapli.driver.core`.

## Basic Driver Arguments

The drivers of course need some information about the device you are trying to connect to. The most common arguments
 to provide to the driver are outlined below:
 
| Argument        | Purpose/Value                                               |
|-----------------|-------------------------------------------------------------|
| host            | name/ip of host to connect to                               |
| port            | port of host to connect to (defaults to port 22)            |
| auth_username   | username for authentication                                 |
| auth_password   | password for authentication                                 |
| auth_secondary  | password for secondary authentication (enable password)     |
| auth_public_key | public key for authentication                               |
| auth_strict_key | strict key checking -- TRUE by default!                     |
| ssh_config_file | True/False or path to ssh config file to use                |

These arguments may be passed as keyword arguments to the driver of your choice, or, commonly are passed via
 dictionary unpacking as show below:
 
```python
from scrapli.driver.core import IOSXRDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
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
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
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
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
}

with IOSXEDriver(**my_device) as conn:
    response = conn.send_command("show version")
```

## Sending Commands

When using any of the core network drivers (`JunosDriver`, `EOSDriver`, etc.), the `send_command` and
 `send_commands` methods will respectively send a single command or list of commands to the device. The commands will
  be sent at the `default_desired_priv` level which is typically "privilege exec" (or equivalent) privilege level
  . Please see [Driver Privilege Levels](#driver-privilege-levels) in the advanced usage section for more details on
   privilege levels.

Note the different methods for sending a single command versus a list of commands!

```python
from scrapli.driver.core import IOSXEDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
}

conn = IOSXEDriver(**my_device)
conn.open()
response = conn.send_command("show version")
responses = conn.send_commands(["show run", "show ip int brief"])
```

## Response Object

All read operations result in a `Response` object being created. The `Response` object contains attributes for the command
 sent (`channel_input`), start/end/elapsed time, and of course the result of the command sent.

```python
from scrapli.driver.core import IOSXEDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
}

conn = IOSXEDriver(**my_device)
conn.open()
response = conn.send_command("show version")
print(response.elapsed_time)
print(response.result)
```

If using `send_commands` (plural!) then scrapli will return a list of Response objects.

In addition to containing the input and output of the command(s) that you sent, the `Response` object also contains a
 method `textfsm_parse_output` (for more on TextFSM support see
 [Textfsm/NTC-Templates Integration](#textfsmntc-templates-integration) which will attempt to parse and return the
  received output. If parsing fails, the value returned will be an empty list.
   
```python
>>> structured_result = response.textfsm_parse_output()
>>> print(structured_result)
[['16.4.1', 'IOS-XE', 'csr1000v', '2 days, 22 hours, 10 minutes', 'reload', 'packages.conf', ['CSR1000V'], ['9FKLJWM5EB0'], '0x2102', []]]
```

## Sending Configurations

When using any of the core drivers, you can send configurations via the `send_configs` method which will handle
 privilege escalation and de-escalation for you. `send_configs` accepts a single string or a list of strings to
  send in "config mode".

```python
from scrapli.driver.core import IOSXEDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
}

with IOSXEDriver(**my_device) as conn:
    conn.send_configs(["interface loopback123", "description configured by scrapli"])
```

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
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
}

with IOSXEDriver(**my_device) as conn:
    response = conn.send_command("show version")
    structured_result = response.textfsm_parse_output()
    print(structured_result)
```

scrapli also supports passing in templates manually (meaning not using the pip installed ntc-templates directory to
 find templates) if desired. The `scrapli.helper.textfsm_parse` function accepts a string or loaded (TextIOWrapper
 ) template and output to parse. This can be useful if you have custom or one off templates or don't want to pip
  install ntc-templates.
  
```python
from scrapli.driver.core import IOSXEDriver
from scrapli.helper import textfsm_parse

my_device = {
    "host": "172.18.0.11",
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
}

with IOSXEDriver(**my_device) as conn:
    response = conn.send_command("show version")
    structured_result = textfsm_parse("/path/to/my/template", response.result)
```

*NOTE*: If a template does not return structured data an empty list will be returned!

## Handling Prompts

In some cases you may need to run an "interactive" command on your device. The `send_interactive` method can be used
 to accomplish this. This method accepts a list containing the initial input (command) to send, the expected prompt
  after the initial send, the response to that prompt, and the final expected prompt -- basically telling scrapli
   when it is done with the interactive command. In the example below the expectation is that the current/base prompt
    is the final expected prompt, so we can simply call the `get_prompt` method to snag that directly off the router.

```python
from scrapli.driver.core import IOSXEDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
}

with IOSXEDriver(**my_device) as conn:
    interactive = conn.send_interactive(
                ("clear logging", "Clear logging buffer [confirm]", "\n", conn.get_prompt())
            )
```

## Telnet

scrapli supports telnet as a transport driver via the standard library module `telnetlib`. Telnet is a bit of a
 special case for scrapli, here are the things you need to know if you wish to use Telnet:
 
- Currently, you *must* set the port number. At the moment scrapli assumes SSH and defaults to port 22, even if you
 specify the telnet driver. This could obviously change in the future but for now, specify your telnet port!
- You can set the username and password prompt expect string after your connection object instantiation
 and before calling the `open` method -- this means if you have non-default prompts you cannot use scrapli with a
  context manager and Telnet (because the context manager calls open for you). You can set the prompts using the
   following attributes of the `Scrape` object:
  - `username_prompt`
  - `password_prompt`

If telnet for some reason becomes an important use case, the telnet Transport layer can be improved/augmented.

## SSH Config Support

scrapli supports using OpenSSH configuration files in a few ways. For "system" SSH transport (default setting
), passing a path to a config file will simply make scrapli "point" to that file, and therefore use that
 configuration files attributes (because it is just exec'ing system SSH!). See the [Transport Notes](#transport-notes
 -caveats-and-known-issues) section for details about what Transport supports what configuration options.
   
*NOTE* -- when using the system (default) SSH transport driver scrapli does NOT disable strict host checking by default
. Obviously this is the "smart" behavior, but it can be overridden on a per host basis in your SSH config file, or by
 passing `False` to the "auth_strict_key" argument on object instantiation.

```python
from scrapli.driver.core import IOSXEDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
    "ssh_config_file": "~/my_ssh_config",
}

with IOSXEDriver(**my_device) as conn:
    print(conn.get_prompt())
```


# Advanced Usage

## All Driver Arguments

The basic usage section outlined the most commonly used driver arguments, this outlines all of the base driver
 arguments -- note that in the future there may be additional driver specific (i.e. JunosDriver) arguments not listed
  here -- check your specific driver in the docs for more details.
 
| Argument             | Purpose/Value                                               |
|----------------------|-------------------------------------------------------------|
| host                 | name/ip of host to connect to                               |
| port                 | port of host to connect to (defaults to port 22)            |
| auth_username        | username for authentication                                 |
| auth_password        | password for authentication                                 |
| auth_secondary       | password for secondary authentication (enable password)     |
| auth_public_key      | public key for authentication                               |
| auth_strict_key      | strict key checking -- TRUE by default!                     |
| timeout_socket       | timeout value for initial socket connection                 |
| timeout_transport    | timeout value for transport (i.e. paramiko)                 |
| timeout_ops          | timeout value for individual operations                     |
| timeout_exit         | True/False exit on timeout ops exceeded                     |
| keepalive            | True/False send keepalives to the remote host               |
| keepalive_interval   | interval in seconds for keepalives                          |
| keepalive_type       | network or standard; see keepalive section for details      |
| keepalive_pattern    | if network keepalive; pattern to send                       |
| comms_prompt_pattern | regex pattern for matching prompt(s); see platform regex    |
| comms_return_char    | return char to use on the channel; default `\n`             |
| comms_ansi           | True/False strip ansi from returned output                  |
| ssh_config_file      | True/False or path to ssh config file to use                |
| ssh_known_hosts_file | True/False or path to ssh known hosts file to use           |
| on_open              | callable to execute "on open"                               |
| on_close             | callable to execute "on exit"                               |
| transport            | system (default), paramiko, ssh2, or telnet                 |

Most of these attributes actually get passed from the `Scrape` (or sub-class such as `NXOSDriver`) into the
 `Transport` and `Channel` classes, so if you need to modify any of these values after instantiation you should do so
  on the appropriate object -- i.e. `conn.channel.comms_prompt_pattern`.

## Platform Regex

Due to the nature of Telnet/SSH there is no good way to know when a command has completed execution. Put another way
, when sending any command, data is returned over a socket, that socket doesn't ever tell us when it is "done
" sending the output from the command that was executed. In order to know when the session is "back at the base
 prompt/starting point" scrapli uses a regular expression pattern to find that base prompt.

This pattern is contained in the `comms_prompt_pattern` setting, and is perhaps the most important argument to getting
 scrapli working!

The "base" (default, but changeable) pattern is:

`"^[a-z0-9.\-@()/:]{1,20}[#>$]$"`

*NOTE* all `comms_prompt_pattern` should use the start and end of line anchors as all regex searches in scrapli are
 multi-line (this is an important piece to making this all work!). While you don't *need* to use the line anchors its
  probably a really good idea! Also note that most devices seem to leave at least one white space after the final
   character of the prompt, so make sure to account for this! Last important note -- the core drivers all of reliable
    patterns set for you, so you hopefully don't need to bother with this too much!

The above pattern works on all "core" platforms listed above for at the very least basic usage. Custom prompts or
 host names could in theory break this, so be careful!

If you do not wish to match Cisco "config" level prompts you could use a `comms_prompt_pattern` such as:

`"^[a-z0-9.-@]{1,20}[#>$]$"`

If you use a platform driver, the base prompt is set in the driver so you don't really need to worry about this!

The `comms_prompt_pattern` pattern can be changed at any time at or after instantiation of an scrapli object, and is
 done so by modifying `conn.channel.comms_prompt_pattern` where `conn` is your scrapli connection object. Changing
 this *can* break things though, so be careful!

## On Connect

Lots of times when connecting to a device there are "things" that need to happen immediately after getting connected
. In the context of network devices the most obvious/common example would be disabling paging (i.e. sending `terminal
 length 0` on a Cisco-type device). While scrapli `Scrape` (the base driver) does not know or care about disabling
  paging or any other on connect type activities, scrapli of course provides a mechanism for allowing users to handle
   these types of tasks. Even better yet, if you are using any of the core drivers (`IOSXEDriver`, `IOSXRDriver
   `, etc.), scrapli will automatically have some sane default "on connect" actions (namely disabling paging).

If you were so inclined to create some of your own "on connect" actions, you can simply pass those to the `on_connect
` argument of `Scrape` or any of its sub-classes (`NetworkDriver`, `IOSXEDriver`, etc.). The value of this argument
 must be a callable that accepts the reference to the connection object. This allows for the user to send commands or
  do really anything that needs to happen prior to "normal" operations. The core network drivers disable paging
   functions all call directly into the channel object `send_inputs` method -- this is a good practice to follow as
    this will avoid any of the `NetworkDriver` overhead such as trying to attain privilege levels -- things like this
     may not be "ready" until *after* your `on_connect` function is executed.
  
Below is an example of creating an "on connect" function and passing it to scrapli. Immediately after authentication
 is handled this function will be called and disable paging (in this example):
    
```python
from scrapli.driver.core import IOSXEDriver

def iosxe_disable_paging(conn):
    conn.channel.send_inputs("term length 0")

my_device = {
    "host": "172.18.0.11",
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
    "on_connect": iosxe_disable_paging
}

with IOSXEDriver(**my_device) as conn:
    print(conn.get_prompt())
```

Note that this section has talked almost exclusively about disabling paging, but any other "things" that need to
 happen in the channel can be handled here. If there is a prompt/banner to accept you should be able to handle it
  here. The goal of this "on connect" function is to allow for lots of flexibility for dealing with whatever needs to
   happen for devices -- thus decoupling the challenge of addressing all of the possible options from scrapli itself
    and allowing users to handle things specific for their environment.

## On Exit

As you may have guessed, `on_exit` is very similar to `on_connect` with the obvious difference that it happens just
 prior to disconnecting from the device. Just like `on_connect`, `on_exit` functions should accept a single argument
  that is a reference to the object itself. As with most things scrapli, there are sane defaults for the `on_exit
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

## Keepalives

In some cases it may be desirable to have a long running connection to a device, however it is generally a bad idea
 to allow for very long timeouts/exec sessions on devices. To cope with this scrapli supports sending "keepalives
 ". For "normal" ssh devices this could be basic SSH keepalives (with ssh2-python and system transports). As scrapli
  is generally focused on networking devices, and most networking devices don't support standard keepalives, scrapli
   also has the ability to send "network" keepalives.
   
In either case -- "standard" or "network" -- scrapli spawns a keepalive thread. This thread then sends either
 standard keepalive messages or "in band" keepalive messages in the case of "network" keepalives.
 
"network" keepalives default ot sending u"\005" which is equivalent of sending `CTRL-E` (jump to end (right side) of
 line). This is generally an innocuous command, and furthermore is never sent unless the keepalive thread can acquire
  a channel lock. This should allow scrapli to keep sessions alive as long as needed.

## Driver Privilege Levels

The "core" drivers understand the basic privilege levels of their respective device types. As mentioned previously
, the drivers will automatically attain the "privilege_exec" (or equivalent) privilege level prior to executing "show
" commands. If you don't want this "auto-magic" you can use the base driver (`Scrape`). The privileges for each device
 are outlined in named tuples in the platforms `driver.py` file. 
 
As an example, the following privilege levels are supported by the `IOSXEDriver`:

1. "exec"
2. "privilege_exec"
3. "configuration"
4. "special_configuration"

Each privilege level has the following attributes:

- pattern: regex pattern to associate prompt to privilege level with
- name: name of the priv level, i.e. "exec"
- deescalate_priv: name of next lower privilege or None
- deescalate: command to deescalate to next lower privilege or None
- escalate: name of next higher privilege or None
- escalate_auth: command to escalate to next higher privilege or None
- escalate_prompt: False or pattern to expect for escalation -- i.e. "Password:"
- requestable: True/False if the privilege level is requestable
- level: integer value of level i.e. 1

If you wish to manually enter a privilege level you can use the `acquire_priv` method, passing in the name of the
 privilege level you would like to enter. In general you probably won't need this too often though as the driver
  should handle much of this for you.

```python
from scrapli.driver.core import IOSXEDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
}
with IOSXEDriver(**my_device) as conn:
    conn.acquire_priv("configuration")
```

## Using `Scrape` Directly

All examples in this readme have shown using the "core" network drivers such as `IOSXEDriver`. These core network
 drivers are actually sub-classes of an ABC called `NetworkDriver` which itself is a sub-class of the base `Scrape
 ` class -- the namesake for this library. The `Scrape` object can be used directly if you prefer to have a much less
  opinionated or less "auto-magic" type experience. `Scrape` does not provide the same `send_command`/`send_commands
  `/`send_configs` methods, nor does it disable paging, or handle any kind of privilege escalation/de-escalation
  . `Scrape` is a much more basic "paramiko"-like experience. Below is a brief example of using the `Scrape` object
   directly:
   
```python
from scrapli import Scrape

my_device = {
    "host": "172.18.0.11",
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
}

with Scrape(**my_device) as conn:
    conn.channel.send_inputs("terminal length 0")
    response = conn.channel.send_inputs("show version")
    responses = conn.channel.send_inputs(("show version", "show run"))
```

Without the `send_command` and similar methods, you must directly acccess the `Channel` object when sending inputs
 with `Scrape`.


## Using a Different Transport

scrapli is built to be very flexible, including being flexible enough to use different libraries for "transport
" -- or the actual Telnet/SSH communication. By default scrapli uses the "system" transport which quite literally
 uses the ssh binary on your system (`/usr/bin/ssh`). This "system" transport means that scrapli has no external
  dependencies as it just relies on what is available on the machine running the scrapli script. It also means that
   scrapli by default probably(?) doesn't support Windows.

In the spirit of being highly flexible, scrapli allows users to swap out this "system" transport with another
 transport mechanism. The other supported transport mechanisms are `paramiko`, `ssh2-python` and `telnetlib`. The
  transport selection can be made when instantiating the scrapli connection object by passing in `paramiko`, `ssh2
  `, or `telnet` to force scrapli to use the corresponding transport mechanism.
  
While it will be a goal to ensure that these other transport mechanisms are supported and useful, the focus of
 scrapli development will be on the "system" SSH transport.
 
Example using `paramiko` as the transport:

```python
from scrapli.driver.core import IOSXEDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
    "transport": "paramiko"
}

with IOSXEDriver(**my_device) as conn:
    print(conn.get_prompt())
```

Currently the only reason I can think of to use anything other than "system" as the transport would be to test
 scrapli on a Windows host or to use telnet. If there are other good reasons please do let me know!


# FAQ

- Question: Why build this? Netmiko exists, Paramiko exists, Ansible exists, etc...?
  - Answer: I built `ssh2net` to learn -- to have a goal/target for writing some code. scrapli is an evolution of the
   lessons learned building ssh2net. About mid-way through building `ssh2net` I realized it may actually be kinda good
    at doing... stuff. So, sure there are other tools out there, but I think scrapli its pretty snazzy and fills in some
     of the gaps in other tools. For example scrapli is 100% compliant with strict mypy type checking, very uniformly
      documented/linted, contains a results object for every operation, is very very fast, is very flexible, and in
       general pretty awesome! Finally, while I think in general that SSH "screen scraping" is not "sexy" or even
        "good", it is the lowest common denominator for automation in the networking world. So I figured I could try
         to make the fastest, most flexible library around for SSH network automation! 
- Question: Is this better than Netmiko/Paramiko/Ansible?
  - Answer: Nope! It is different though! The main focus is just to be stupid fast. It is very much that. It *should* be
  super reliable too as the timeouts are very easy/obvious to control, and it should also be very very very easy to
   adapt to any other network-y type CLI by virtue of flexible prompt finding and easily modifiable on connect
    functions.
- Question: Is this easy to use?
  - Answer: Yep! The "native" usage is pretty straight forward -- the thing to remember is that it doesn't do "things
  " for you like Netmiko does for example, so its a lot more like Paramiko in that regard this just means that you
   need to disable paging yourself (or pass an `on_connect` callable to do so), handle privilege modes and things like
    that. That said you can use one of the available drivers to have a more Netmiko-like experience -OR- write your
     own driver as this has been built with the thought of being easily extended.
- Why do I get a "conn (or your object name here) has no attribute channel" exception?
  - Answer: Connection objects do not "auto open", and the channel attribute is not assigned until opening the
   connection. Call `conn.open()` (or your object name in place of conn) to open the session and assign the channel
    attribute. Alternatively you can use any of the drivers with a context manager (see what I did there? WITH... get
     it?) which will auto-magically open and close the connections for you.
- Other questions? Ask away!


# Transport Notes, Caveats, and Known Issues

## paramiko

- I'll think of something...

### SSH Config Supported Arguments

- user
- port
- identity_file

### Known Issues

- None yet!

## ssh2-python

### SSH Config Supported Arguments

- user
- port
- identity_file

### Known Issues

- Arista EOS uses keyboard interactive authentication which is currently broken in the pip-installable version
 of ssh2-python (as of January 2020). GitHub user [Red-M](https://github.com/Red-M) has contributed to and fixed this
  particular issue but the fix has not been merged. If you would like to use ssh2-python with EOS I suggest cloning
   and installing via Red-M's repository or my fork of Red-M's fork!
- Use the context manager where possible! More testing needs to be done to confirm/troubleshoot, but limited testing
 seems to indicate that without properly closing the connection there appears to be a bug that causes Python to crash
  on MacOS at least. More to come on this as I have time to poke it more! I believe this is only occurring on the
   latest branch/update (i.e. not on the pip installable version).

## system

- Any arguments passed to the `SystemSSHTransport` class will override arguments in your ssh config file. This is
 because the arguments get crafted into an "open_cmd" (the command that actually fires off the ssh session), and
  these cli arguments take precedence over the config file arguments.
- strict key checking is ENABLED by default! If you see weird EOF errors immediately after opening a connection, you
 probably did not disable strict key checking!
- If you set `ssh_config_file` to `False` the `SystemSSHTransport` class will set the config file used to `/dev/null
` so that no ssh config file configs are accidentally used.

### SSH Config Supported Arguments

- literally whatever your system supports as scrapli just execs SSH on your system!

### Known Issues

- Connecting to linux hosts (tested w/ Ubuntu, but presumably on all linux hosts?) when using system-ssh and a public
 key for authentication (thus forcing using sub process with pipes -- `_open_pipes`) successfully auths, but gets no
  read data back after reading the banner. I have no idea why. Testing to the same server w/ password authentication
   things work as expected. As linux is not a priority target for scrapli this may go unresolved for a while...

## telnet

- See the telnet section!

### SSH Config Supported Arguments

- Obviously none!

### Known Issues

- None yet!


# Linting and Testing

*NOTE* Currently there are no unit/functional tests for IOSXR/NXOS/EOS/Junos, however as this part of scrapli is largely
 a port of ssh2net, they should work :) 

## Linting

This project uses [black](https://github.com/psf/black) for auto-formatting. In addition to black, tox will execute
 [pylama](https://github.com/klen/pylama), and [pydocstyle](https://github.com/PyCQA/pydocstyle) for linting purposes
 . Tox will also run  [mypy](https://github.com/python/mypy), with strict type checking. Docstring linting with
  [darglint](https://github.com/terrencepreilly/darglint) which has been quite handy!

All commits to this repository will trigger a GitHub action which runs tox, but of course its nicer to just run that
 before making a commit to ensure that it will pass all tests!

### Typing

As stated, this project is 100% type checked and will remain that way. The value this adds for IDE auto-completion
 and just general sanity checking/forcing writing of more type-check-able code is worth the small overhead in effort.

## Testing

Testing is broken into two main categories -- unit and functional. Unit is what you would expect -- unit testing the
 code. Functional testing connects to virtual devices in order to more accurately test the code. Unit tests cover
  quite a bit of the code base due to mocking the FileIO that the channel reads/writes to. This gives a pretty high
   level of confidence that at least object instantiation and channel read/writes will generally work... Functional
    tests against virtual devices helps reinforce that and gets coverage for the transport classes.

For more ad-hoc type testing there is a `smoke` folder in the tests directory -- for "smoke tests". These are simple
 scripts that don't really "test" (as in no assertions or pytest or anything), but are useful for basic testing that
  things have not gotten broken while working on new features. These have been handy for spot testing during
   development so rather than leave them in a private directory they are included here in case they are useful for
    anyone else!

### Unit Tests

Unit tests can be executed via pytest:

```
python -m pytest tests/unit/
```

Or using the following make command:

```
make test_unit
```

If you would like to see the coverage report and generate the html coverage report:

```
make cov_unit
```

### Setting up Functional Test Environment

Executing the functional tests is a bit more complicated! First, thank you to Kristian Larsson for his great tool
 [vrnetlab](https://github.com/plajjan/vrnetlab)! All functional tests are built on this awesome platform that allows
  for easy creation of containerized network devices.

Basic functional tests exist for all "core" platform types (IOSXE, NXOS, IOSXR, EOS, Junos). Vrnetlab currently only
 supports the older emulation style NX-OS devices, and *not* the newer VM image n9kv. I have made some very minor
  tweaks to vrnetlab locally in order to get the n9kv image running -- I have raised a PR to add this to vrnetlab
   proper. Minus the n9kv tweaks, getting going with vrnetlab is fairly straightforward -- simply follow Kristian's
    great readme docs. For the Arista EOS image -- prior to creating the container you should boot the device and
     enter the `zerotouch disable` command. This allows for the config to actually be saved and prevents the
      interfaces from cycling through interface types in the container (I'm not clear why it does that but executing
       this command before building the container "fixes" this!).

The docker-compose file here will be looking for the container images matching this pattern, so this is an important
 bit! The container image names should be:

```
scrapli-cisco-iosxe
scrapli-cisco-nxos
scrapli-cisco-iosxr
scrapli-arista-eos
scrapli-juniper-junos
```

You can tag the image names on creation (following the vrnetlab readme docs), or create a new tag once the image is built:

```
docker tag [TAG OF IMAGE CREATED] scrapli-[VENDOR]-[OS]
```

*NOTE* I have added vty lines 5-98 on the CSR image -- I think the connections opening/closing so quickly during
 testing caused them to get hung. Testing things more slowly (adding time.sleep after closing connections) fixed this
  but that obviously made the testing time longer, so this seemed like a better fix. This change will be in my fork
   of vrnetlab or you can simply modify the `line vty 0 5` --> `line vty 0 98` in the `luanch.py` for the CSR in your
    vrnetlab clone. `line vty 1` for some reason also had `length 0` which I have removed (and tests expect to be
     gone). Lastly, to test telnet the `csr` setup in vrnetlab needs to be modified to allow telnet as well; this
      means the Dockerfile must expose port 23, the qemu nic settings must support port 23 being sent into the VM and
       socat must also be setup appropriately. This should all be updated in my vrnetlab fork. 


### Functional Tests

Once you have created the images, you can start the containers with a make command:

```
make start_dev_env
```

Conversely you can terminate the containers:

```
make stop_dev_env
```

To start a specific platform container:

```
make start_dev_env_iosxe
```

Substitute "iosxe" for the platform type you want to start.

Most of the containers don't take too long to fire up, maybe a few minutes (running on my old macmini with Ubuntu, so not exactly a powerhouse!). That said, the IOS-XR device takes about 15 minutes to go to "healthy" status. Once booted up you can connect to their console or via SSH:

| Device        | Local IP      |
| --------------|---------------|
| iosxe         | 172.18.0.11   |
| nxos          | 172.18.0.12   |
| iosxr         | 172.18.0.13   |
| eos           | 172.18.0.14   |
| junos         | 172.18.0.15   |

The console port for all devices is 5000, so to connect to the console of the iosxe device you can simply telnet to that port locally:

```
telnet 172.18.0.11 5000
```

Credentials for all devices use the default vrnetlab credentials:

Username: `vrnetlab`

Password: `VR-netlab9`

Once the container(s) are ready, you can use the make commands to execute tests as needed:

- `test` will execute all currently implemented functional tests as well as the unit tests
- `test_functional` will execute all currently implemented functional tests
- `test_iosxe` will execute all unit tests and iosxe functional tests
- `test_nxos` will execute all unit tests and nxos functional tests
- `test_iosxr` will execute all unit tests and iosxr functional tests
- `test_eos` will execute all unit tests and eos functional tests
- `test_junos` will execute all unit tests and junos functional tests


# Todo and Roadmap

This section may not get updated much, but will hopefully reflect the priority items for short term (todo) and longer
 term (roadmap) for scrapli.

## Todo

- Add tests for keepalive stuff if possible
- Investigate pre-authentication handling for telnet -- support handling a prompt *before* auth happens i.e. accept
 some banner/message -- does this ever happen for ssh? I don't know! If so, support dealing with that as well.
- Remove as much as possible from the vendor'd `ptyprocess` code. Type hint it, add docstrings everywhere, add tests
 if possible (and remove from ignore for test coverage and darglint).
- Improve testing in general... make it more orderly/nicer, retry connections automatically if there is a failure
 (failures happen from vtys getting tied up and stuff like that it seems), shoot for even better coverage!
- Add a dummy container (like nornir maybe?) to use for functional testing -- its very likely folks won't have a
 vrnetlab setup or compute to set that up... it'd be nice to have a lightweight container that can be used for basic
  testing of `Scrape` and for testing auth with keys and such.
- Improve logging -- especially in the transport classes and surrounding authentication (mostly in systemssh).

## Roadmap

- Async support. This is a bit of a question mark as I personally don't know even where to start to implement this
, and have no real current use case... that said I think it would be cool if for no other reason than to learn!
- Plugins -- make the drivers all plugins!
- Nonrir plugin -- make scrapli a Nornir plugin!
- Ensure v6 stuff works as expected.
- Continue to add/support ssh config file things.
