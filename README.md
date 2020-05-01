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
 squished together! scrapli's goal is to be as fast and flexible as possible, while providing a thoroughly tested, well
  typed, well documented, simple API.


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
  - [Cisco Genie Integration](#cisco-genie-integration)
  - [Handling Prompts](#handling-prompts)
  - [Telnet](#telnet)
  - [SSH Config Support](#ssh-config-support)
- [Advanced Usage](#advanced-usage)
  - [All Driver Arguments](#all-driver-arguments)
  - [Platform Regex](#platform-regex)
  - [On Open](#on-open)
  - [On Close](#on-close)
  - [Timeouts](#timeouts)
  - [Driver Privilege Levels](#driver-privilege-levels)
  - [Using Scrape Directly](#using-scrape-directly)
  - [Using the GenericDriver](#using-the-genericdriver)
  - [Using a Different Transport](#using-a-different-transport)
  - [Auth Bypass](#auth-bypass)
  - [Transport Options](#transport-options)
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
See below or [here](#advanced-installation) for advanced installation details.

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
- [Basic "GenericDriver" operations](/examples/basic_usage/generic_driver.py)
- [Basic "core" Driver operations](/examples/basic_usage/iosxe_driver.py)
- [Setting up basic logging](/examples/logging/basic_logging.py)
- [Using SSH Key for authentication](/examples/ssh_keys/ssh_keys.py)
- [Using SSH config file](/examples/ssh_config_files/ssh_config_file.py)
- [Parse output with TextFSM/ntc-templates](/examples/structured_data/structured_data_textfsm.py)
- [Parse output with Genie](/examples/structured_data/structured_data_genie.py)
- [Transport Options](examples/transport_options/system_ssh_args.py)


# scrapli: What is it

As stated, scrapli is a python library focused on connecting to devices, specifically network devices via SSH or Telnet.

scrapli is built primarily in three parts: transport, channel, and driver. The transport layer is responsible for
 providing a file-like interface to the target server. The channel layer is responsible for reading and writing
  to the provided file-like interface. Finally, the driver provides the user facing API/interface to scrapli.

There are two available "transports" in scrapli "core" -- both of which inherit from a base transport class
 and provide the same file-like interface to the upstream channel. There are also (currently!) two transport plugins
  available -- both of which are installable as optional extras. The transport options are:

- [paramiko](https://github.com/paramiko/paramiko) (optional extra)
- [ssh2-python](https://github.com/ParallelSSH/ssh2-python) (optional extra)
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
 native system local SSH. The implementation of using system SSH is of course a little bit messy, however scrapli
  takes care of that for you so you don't need to care about it! The payoff of using system SSH is of course that
   OpenSSH config files simply "work" -- no passing it to scrapli, no selective support, no need to set username or
    ports or any of the other config items that may reside in your SSH config file. This driver will likely be the
     focus of most development for this project, though I will try to keep the other transport drivers -- in
      particular ssh2-python -- as close to parity as is possible/practical.

The last transport is telnet via telnetlib. This was trivial to add in as the interface is basically the same as
 SystemSSH, and it turns out telnet is still actually useful for things like terminal servers and the like!

The final piece of scrapli is the actual "driver" -- or the component that binds the transport and channel together and
 deals with instantiation of an scrapli object. There is a "base" driver object -- `Scrape` -- which provides essentially
  a "raw" SSH (or telnet) connection that is created by instantiating a Transport object, and a Channel object
  . `Scrape` provides (via Channel) read/write methods and not much else -- this should feel familiar if you have
   used paramiko in the past. More specific "drivers" can inherit from this class to extend functionality of the
    driver to make it more friendly for network devices. In fact, there is a `GenericDriver` class that inherits from
     `Scrape` and provides a base driver to work with if you need to interact with a device not represented by one of
      the "core" drivers. Next, the `NetworkDriver` abstract base class inherits from `GenericDriver` This
       `NetworkDriver` isn't really meant to be used directly though (hence why it is an ABC), but to be further
        extended and built upon instead. As this library is focused on interacting with network devices, an example
         scrapli driver (built on the `NetworkDriver`) would be the `IOSXEDriver` -- to, as you may have guessed
         , interact with devices running Cisco's IOS-XE operating system.


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
 `) and `GenericDriver` connections do not handle any kind of device-specific operations such as privilege
  escalation or saving configurations, they are simply intended to be a bare bones connection that can interact with
   nearly any device/platform if you are willing to send/parse inputs/outputs manually. In most cases it is assumed
    that users will use one of the "core" drivers.

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
pip install -e git+https://github.com/carlmontanari/scrapli.git@develop#egg=scrapli
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

- paramiko (paramiko and the scrapli_paramiko transport)
- ssh2 (ssh2-python and the scrapli_ssh2 transport)
- textfsm (textfsm and ntc-templates)
- genie (genie/pyats)

As for platforms to *run* scrapli on -- it has and will be tested on MacOS and Ubuntu regularly and should work on any
 POSIX system. Windows is now being tested very minimally via GitHub Actions builds, however it is important to note
  that if you wish to use Windows you will need to use paramiko or ssh2-python as the transport driver. It is
   *strongly* recommended/preferred for folks to use WSL/Cygwin and stick with "system" as the transport. 


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

If you are working with a platform not listed above, you have two options: you can use the `Scrape` driver directly
, which you can read about [here](#using-scrape-directly) or you can use the `GenericDriver` which which you can read
 about [here](#using-the-genericdriver). In general you should probably use the `GenericDriver` and not mess about
  using `Scrape` directly.


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

When using any of the core network drivers (`JunosDriver`, `EOSDriver`, etc.) or the `GenericDriver`, the `send_command
` and `send_commands` methods will respectively send a single command or list of commands to the device.

When using the core network drivers, the command(s) will be sent at the `default_desired_priv` level which is
 typically "privilege exec" (or equivalent) privilege level. Please see [Driver Privilege Levels](#driver-privilege
 -levels) in the advanced usage section for more details on privilege levels. As the `GenericDriver` doesn't know or
  care about privilege levels you would need to manually handle acquiring the appropriate privilege level for you
   command yourself if using that driver.

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

Finally, if you prefer to have a list of commands to send, there is a `send_commands_from_file` method. This method
 excepts the provided file to have a single command to send per line in the file.

## Response Object

All command/config operations that happen in the `GenericDriver` or any of the drivers inheriting from the
 `NetworkDriver` result in a `Response` object being created. The `Response` object contains attributes for the
  command sent (`channel_input`), start/end/elapsed time, and of course the result of the command sent.

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
 [Textfsm/NTC-Templates Integration](#textfsmntc-templates-integration)) which will attempt to parse and return the
  received output. If parsing fails, the value returned will be an empty list -- meaning you will *always* get
   "structured data" returned, however it will just be an empty object if parsing fails.
   
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

There is also a `send_configs_from_file` method that behaves exactly like the commands version, but sends the
 commands in configuration mode as you would expect.

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
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
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


## Handling Prompts

In some cases you may need to run an "interactive" command on your device. The `send_interactive` method of the
 `GenericDriver` or its sub-classes (`NetworkDriver` and "core" drivers) can be used to accomplish this. This method
  accepts a list of "interact_events" -- or basically commands you would like to send, and their expected resulting
   prompt. A third, optional, element is available for each "interaction", this last element is a bool that indicates
    weather or not the input that you are sending to the device is "hidden" or obfuscated by the device. This is
     typically used for password prompts where the input that is sent does not show up on the screen (if you as a
      human are sitting on a terminal typing).
      
This method can accept one or N "events" and thus can be used to deal with any number of subsequent prompts. 

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
 -caveats-and-known-issues) section for details about what Transport supports what configuration options. You can
  also pass `True` to let scrapli search in system default locations for an ssh config file (`~/.ssh/config` and
   `/etc/ssh/ssh_config`.)
   
*NOTE* -- scrapli does NOT disable strict host checking by default. Obviously this is the "smart" behavior, but it
 can be overridden on a per host basis in your SSH config file, or by passing `False` to the "auth_strict_key
 " argument on object instantiation.

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
 arguments.
 
| Argument                        | Purpose/Value                                               | Class             |
|---------------------------------|-------------------------------------------------------------|-------------------|
| host                            | name/ip of host to connect to                               | Scrape            |                             
| port                            | port of host to connect to (defaults to port 22)            | Scrape            |                             
| auth_username                   | username for authentication                                 | Scrape            |                             
| auth_password                   | password for authentication                                 | Scrape            |                             
| auth_secondary                  | password for secondary authentication (enable password)     | NetworkDriver     |                  
| auth_private_key                | private key for authentication                              | Scrape            |                   
| auth_strict_key                 | strict key checking -- TRUE by default!                     | Scrape            |    
| auth_bypass                     | bypass ssh auth prompts after ssh establishment             | Scrape            |                           
| timeout_socket                  | timeout value for initial socket connection                 | Scrape            |                   
| timeout_transport               | timeout value for transport (i.e. paramiko)                 | Scrape            |                   
| timeout_ops                     | timeout value for individual operations                     | Scrape            |                   
| timeout_exit                    | True/False exit on timeout ops exceeded                     | Scrape            |                   
| keepalive                       | True/False send keepalives to the remote host               | Scrape            |                   
| keepalive_interval              | interval in seconds for keepalives                          | Scrape            |                   
| keepalive_type                  | network or standard; see keepalive section for details      | Scrape            |                   
| keepalive_pattern               | if network keepalive; pattern to send                       | Scrape            |                   
| comms_prompt_pattern            | regex pattern for matching prompt(s); see platform regex    | Scrape            |                   
| comms_return_char               | return char to use on the channel; default `\n`             | Scrape            |                   
| comms_ansi                      | True/False strip ansi from returned output                  | Scrape            |                   
| ssh_config_file                 | True/False or path to ssh config file to use                | Scrape            |                   
| ssh_known_hosts_file            | True/False or path to ssh known hosts file to use           | Scrape            |                   
| on_open                         | callable to execute "on open"                               | Scrape            |                   
| on_close                        | callable to execute "on exit"                               | Scrape            |                   
| transport                       | system (default), paramiko, ssh2, or telnet                 | Scrape            |  
| transport_options               | dictionary of transport-specific arguments                  | Scrape            |                
| default_desired_privilege_level | privilege level for "show" commands to be executed at       | NetworkDriver     |

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

`"^[a-z0-9.\-@()/:]{1,20}[#>$]\s*$"`

*NOTE* all `comms_prompt_pattern` "should" use the start and end of line anchors as all regex searches in scrapli are
 multi-line (this is an important piece to making this all work!). While you don't *need* to use the line anchors its
  probably a really good idea! Also note that most devices seem to leave at least one white space after the final
   character of the prompt, so make sure to account for this! Last important note -- the core drivers all have reliable
    patterns set for you, so you hopefully don't need to bother with this too much!

The above pattern works on all "core" platforms listed above for at the very least basic usage. Custom prompts or
 host names could in theory break this, so be careful!

If you do not wish to match Cisco "config" level prompts you could use a `comms_prompt_pattern` such as:

`"^[a-z0-9.-@]{1,20}[#>$]\s*$"`

If you use a platform driver, the base prompt is set in the driver so you don't really need to worry about this!

The `comms_prompt_pattern` pattern can be changed at any time at or after instantiation of an scrapli object, and is
 done so by modifying `conn.channel.comms_prompt_pattern` where `conn` is your scrapli connection object. Changing
 this *can* break things though, so be careful!

## On Open

Lots of times when connecting to a device there are "things" that need to happen immediately after getting connected
. In the context of network devices the most obvious/common example would be disabling paging (i.e. sending `terminal
 length 0` on a Cisco-type device). While scrapli `Scrape` (the base driver) and `GenericDriver` do not know or care
  about disabling paging or any other on connect type activities, scrapli of course provides a mechanism for allowing
   users to handle these types of tasks. Even better yet, if you are using any of the core drivers (`IOSXEDriver
   `, `IOSXRDriver`, etc.), scrapli will automatically have some sane default "on connect" actions (namely disabling
    paging).

If you were so inclined to create some of your own "on connect" actions, you can simply pass those to the `on_open
` argument of `Scrape` or any of its sub-classes (`NetworkDriver`, `IOSXEDriver`, etc.). The value of this argument
 must be a callable that accepts the reference to the connection object. This allows for the user to send commands or
  do really anything that needs to happen prior to "normal" operations. The core network drivers disable paging
   functions all call directly into the channel object `send_inputs` method -- this is a good practice to follow as
    this will avoid any of the `NetworkDriver` overhead such as trying to attain privilege levels -- things like this
     may not be "ready" until *after* your `on_open` function is executed.
  
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

## Keepalives

In some cases it may be desirable to have a long running connection to a device, however it is generally a bad idea
 to allow for very long timeouts/exec sessions on devices. To cope with this scrapli supports sending "keepalives
 ". For "normal" ssh devices this could be basic SSH keepalives (with ssh2-python and system transports). As scrapli
  is generally focused on networking devices, and most networking devices don't support standard keepalives, scrapli
   also has the ability to send "network" keepalives.
   
In either case -- "standard" or "network" -- scrapli spawns a keepalive thread. This thread then sends either
 standard keepalive messages or "in band" keepalive messages in the case of "network" keepalives.
 
"network" keepalives default to sending u"\005" which is equivalent of sending `CTRL-E` (jump to end (right side) of
 line). This is generally an innocuous command, and furthermore is never sent unless the keepalive thread can acquire
  a channel lock. This should allow scrapli to keep sessions alive as long as needed.

## Driver Privilege Levels

The "core" drivers understand the basic privilege levels of their respective device types. As mentioned previously
, the drivers will automatically attain the "privilege_exec" (or equivalent) privilege level prior to executing "show
" commands. If you don't want this "auto-magic" you can use the base driver (`Scrape`) or the `GenericDriver`. The
 privileges for each device are outlined in named tuples in the platforms `driver.py` file. 
 
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
 drivers are actually sub-classes of an ABC called `NetworkDriver` which itself is a sub-class of the `GenericDriver
 ` which is a sub-class of the base `Scrape` class -- the namesake for this library. The `Scrape` object can be used
  directly if you prefer to have a much less opinionated or less "auto-magic" type experience. `Scrape` does not
   provide the same `send_command`/`send_commands`/`send_configs` methods, nor does it disable paging, or handle any
    kind of privilege escalation/de-escalation. `Scrape` is a much more basic "paramiko"-like experience. Below is a
     brief example of using the `Scrape` object directly:
   
```python
from scrapli import Scrape

my_device = {
    "host": "172.18.0.11",
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
}

with Scrape(**my_device) as conn:
    conn.channel.send_input("terminal length 0")
    response = conn.channel.send_input("show version")
    responses = conn.channel.send_inputs(["show version", "show run"])
```

Without the `send_command` and similar methods, you must directly access the `Channel` object when sending inputs
 with `Scrape`.


## Using the `GenericDriver`

Using the `Scrape` driver directly is nice enough, however you may not want to have to change the prompt pattern, or
 deal with accessing the channel to send commands to the device. In this case there is a `GenericDriver` available to
  you. This driver has a *very* broad pattern that it matches for base prompts, has no concept of disabling paging or
   privilege levels (like `Scrape`), but does provide `send_command`, `send_commands`, `send_interact`, and
    `get_prompt` methods for a more NetworkDriver-like experience. 

Hopefully this `GenericDriver` can be used as a starting point for devices that don't fall under the core supported
 platforms list.
   
```python
from scrapli.driver import GenericDriver

my_device = {
    "host": "172.18.0.11",
    "auth_username": "vrnetlab",
    "auth_password": "VR-netlab9",
    "auth_strict_key": False,
}

with GenericDriver(**my_device) as conn:
    conn.send_command("terminal length 0")
    response = conn.send_command("show version")
    responses = conn.send_commands(["show version", "show run"])
```


## Using a Different Transport

scrapli is built to be very flexible, including being flexible enough to use different libraries for "transport
" -- or the actual Telnet/SSH communication. By default scrapli uses the "system" transport which quite literally
 uses the ssh binary on your system (`/usr/bin/ssh`). This "system" transport means that scrapli has no external
  dependencies as it just relies on what is available on the machine running the scrapli script.

In the spirit of being highly flexible, scrapli allows users to swap out this "system" transport with another
 transport mechanism. The other supported transport mechanisms are `paramiko`, `ssh2-python` and `telnetlib
 `. `paramiko` and `ssh2-python` were originally part of the core of scrapli, but have since been moved to their own
  repositories to be used as plugins to keep the codebase as simple as possible. The transport selection can be made
   when instantiating the scrapli connection object by passing in `paramiko`, `ssh2`, or `telnet` to force scrapli to
    use the corresponding transport mechanism.
  
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


## Auth Bypass

*NOTE* Currently only supported with system transport!

Some devices, such as Cisco WLC, have no "true" SSH authentication, and instead prompt for credentials (or perhaps
 not even that) after session establishment. In order to cope with this corner case, the `auth_bypass` flag can be
  set to `True` which will cause scrapli to skip all authentication steps. Typically this flag would be set and a
   custom `on_open` function set to handle whatever prompts the device has upon SSH session establishment.
   
In the future this functionality will likely be extended to the telnet transport, and may be extended to paramiko and
 ssh2 transports.

See the [non core device example](/examples/non_core_device/wlc.py) to see this in action.


## Transport Options

Because each transport has different options/features available, it doesn't make sense to try to put all possible
 arguments in the `Scrape` or `NetworkDriver` drivers, to address this an argument `transport_options` has been added
 . This is exactly what it sounds like -- arguments that can be passed to the selected transport class. As these
  arguments will be transport-specific, please check the docs/docstrings for your preferred transport to see what is
   available.
   
A simple example of passing additional SSH arguments to the `SystemSSHTransport` class is available
 [here](examples/transport_options/system_ssh_args.py).


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
  - Answer: Yep! The base usage with `Scrape` is pretty straight forward -- the thing to remember is that it doesn't
   do "things" for you like Netmiko does for example, so its a lot more like Paramiko in that regard this just means
    that you need to disable paging yourself (or pass an `on_open` callable to do so), handle privilege modes and
     things like that. That said you can use one of the available drivers to have a more Netmiko-like experience -OR
     - write your own driver as this has been built with the thought of being easily extended.
- Why do I get a "conn (or your object name here) has no attribute channel" exception?
  - Answer: Connection objects do not "auto open", and the channel attribute is not assigned until opening the
   connection. Call `conn.open()` (or your object name in place of conn) to open the session and assign the channel
    attribute. Alternatively you can use any of the drivers with a context manager (see what I did there? WITH... get
     it?) which will auto-magically open and close the connections for you.
- I wanna go fast!
  - Hmmm... not a question but I dig it. If you wanna go fast you gotta learn to drive with the fear... ok, enough
   Talladega Nights quoting for now. In theory using the `ssh2` transport is the gateway to speed... being a very
    thin wrapper around libssh2 means that its basically all C and that means its probably about as fast as we're
     reasonably going to get. All that said, scrapli by default uses the `system` transport which is really just
      using your system ssh.... which is almost certainly libssh2/openssh which is also C. There is a thin layer of
       abstraction between scrapli and your system ssh but really its just reading/writing to a file which Python
        should be doing in C anyway I would think. In summary... while `ssh2` is probably the fastest you can go with
         scrapli, the difference between `ssh2` and `system` transports in limited testing is microscopic, and the
          benefits of using system transport (native ssh config file support!!) probably should outweigh the speed of
           ssh2 -- especially if you have control persist and can take advantage of that with system transport!
- Other questions? Ask away!


# Transport Notes, Caveats, and Known Issues

## paramiko

- Currently there seems to be a cosmetic bug where there is an error message about some socket error... but
 everything seems to work as expected.

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
  - Windows users using python3.8 may need to use Red-M's fork, quick testing in GitHub actions for py3.8 on Windows
   had install failures for ssh2-python.
- Use the context manager where possible! More testing needs to be done to confirm/troubleshoot, but limited testing
 seems to indicate that without properly closing the connection there appears to be a bug that causes Python to crash
  on MacOS at least. More to come on this as I have time to poke it more! I believe this is only occurring on the
   latest branch/update (i.e. not on the pip installable version). (April 2020 -- this may be fixed... need to retest
   ...)

## system

- Any arguments passed to the `SystemSSHTransport` class will override arguments in your ssh config file. This is
 because the arguments get crafted into an "open_cmd" (the command that actually fires off the ssh session), and
  these cli arguments take precedence over the config file arguments.
- If you set `ssh_config_file` to `False` the `SystemSSHTransport` class will set the config file used to `/dev/null
` so that no ssh config file configs are accidentally used.
- There is zero Windows support for system ssh transport - I would strongly encourage the use of WSL or cygwin and
 sticking with systemssh instead of using paramiko/ssh2 natively in Windows -- system ssh is very much the focus of
  development for scrapli!

### SSH Config Supported Arguments

- literally whatever your system supports as scrapli just execs SSH on your system!

### Known Issues

- None yet!

## telnet

- See the telnet section!

### SSH Config Supported Arguments

- Obviously none!

### Known Issues

- None yet!


# Linting and Testing

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

Basic functional tests exist for all "core" platform types (IOSXE, NXOS, IOSXR, EOS, Junos) as well as basic testing
 for Linux. Vrnetlab currently only supports the older emulation style NX-OS devices, and *not* the newer VM image
  n9kv. I have made some very minor tweaks to vrnetlab locally in order to get the n9kv image running. I also have
   made some changes to enable scp-server for IOSXE/NXOS devices to allow for config replaces with NAPALM right out
    of the box. You can get these tweaks in my fork of vrnetlab. Getting going with vrnetlab is fairly
     straightforward -- simply follow Kristian's great readme docs.
     
For the Arista EOS image -- prior to creating the container you should boot the device and enter the `zerotouch
 disable` command. This allows for the config to actually be saved and prevents the interfaces from cycling through
  interface types in the container (I'm not clear why it does that but executing this command before building the
   container "fixes" this!). An example qemu command to boot up the EOS device is:
         
```
qemu-system-x86_64 -enable-kvm -display none -machine pc -monitor tcp:0.0.0.0:4999,server,nowait -m 4096 -serial telnet:0.0.0.0:5999,server,nowait -drive if=ide,file=vEOS-lab-4.22.1F.vmdk -device pci-bridge,chassis_nr=1,id=pci.1 -device e1000,netdev=p00,mac=52:54:00:54:e9:00 -netdev user,id=p00,net=10.0.0.0/24,tftp=/tftpboot,hostfwd=tcp::2022-10.0.0.15:22,hostfwd=tcp::2023-10.0.0.15:23,hostfwd=udp::2161-10.0.0.15:161,hostfwd=tcp::2830-10.0.0.15:830,hostfwd=tcp::2080-10.0.0.15:80,hostfwd=tcp::2443-10.0.0.15:443
```

Once booted, connect to the device (telnet to container IP on port 5999 if using above command), issue the command
 `zerotouch disable`, save the config and then you can shut it down, and make the container.

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

*NOTE* If you are going to test scrapli, use [my fork of vrnetlab](https://github.com/carlmontanari/vrnetlab) -- I've
 enabled telnet, set ports, taken care of setting things up so that NAPALM can config replace, etc.


### Functional Tests

Once you have created the images, you can start all of the containers with a make command:

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

Most of the containers don't take too long to fire up, maybe a few minutes (running on my old macmini with Ubuntu, so
 not exactly a powerhouse!). That said, the IOS-XR device takes about 15 minutes to go to "healthy" status. Once
  booted up you can connect to their console or via SSH:

| Device        | Local IP      |
| --------------|---------------|
| iosxe         | 172.18.0.11   |
| nxos          | 172.18.0.12   |
| iosxr         | 172.18.0.13   |
| eos           | 172.18.0.14   |
| junos         | 172.18.0.15   |
| linux         | 172.18.0.20   |

The console port for all devices is 5000, so to connect to the console of the iosxe device you can simply telnet to
 that port locally:

```
telnet 172.18.0.11 5000
```

Credentials for all devices use the default vrnetlab credentials:

Username: `vrnetlab`

Password: `VR-netlab9`

You should also run the `prepare_devices` script in the functional tests, or use the Make commands to do so for you
. This script will deploy the base config needed for testing. The make commands for this step follow the same pattern
 as the others:

- `prepare_dev_env` will push the base config to all devices
- `prepare_dev_env_XYZ` where XYZ == "iosxe", "nxos", etc. will push the base config for the specified device.

Once the container(s) are ready, you can use the make commands to execute tests as needed:

- `test` will execute all currently implemented functional tests as well as the unit tests
- `test_functional` will execute all currently implemented functional tests
- `test_iosxe` will execute all unit tests and iosxe functional tests
- `test_nxos` will execute all unit tests and nxos functional tests
- `test_iosxr` will execute all unit tests and iosxr functional tests
- `test_eos` will execute all unit tests and eos functional tests
- `test_junos` will execute all unit tests and junos functional tests
- `test_linux` will execute all unit tests and basic linux functional tests (this is really intended to test the base
 `Scrape` driver instead of the network drivers)

### Other Functional Test Info

IOSXE is the only platform that is testing SSH key based authentication at the moment. The key is pushed via NAPALM in
 the setup phase. This was mostly done out of laziness, and in the future the other platforms may be tested with key
  based auth as well, but for now IOSXE is representative enough to provide some faith that key based auth works! 


# Todo and Roadmap

This section may not get updated much, but will hopefully reflect the priority items for short term (todo) and longer
 term (roadmap) for scrapli.

## Todo

- Investigate setter methods for setting user/pass/and other attrs on base scrape object... they should be able to be
 set at that level and have the transport updated if it can be done reasonably
- Refresh the keepalive stuff -- how/where keepalives get kicked off needs to be reevaluated, particularly for
 systemssh "standard" keepalives as this should really be happening in the open command (systemssh will probably have
  to override some Transport methods basically), get all of this under functional testing as well
- Add tests for timeouts if possible
- Add more tests for auth failures
- Add tests for custom on open/close functions
- Remove as much as possible from the vendor'd `ptyprocess` code. Type hint it, add docstrings everywhere, add tests
 if possible (and remove from ignore for test coverage and darglint).
- Add darglint back in if it gets faster

## Roadmap

- Async support. This is a bit of a question mark as I personally don't know even where to start to implement this
, and have no real current use case... that said I think it would be cool if for no other reason than to learn!
- Plugins -- build framework to allow for others to easily build driver plugins if desired
- Ensure v6 stuff works as expected.
- Continue to add/support ssh config file things.
- Maybe make this into a netconf driver as well? ncclient is just built on paramiko so it seems doable...?
