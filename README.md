![](https://github.com/carlmontanari/scrapli/workflows/Weekly%20Build/badge.svg)
[![PyPI version](https://badge.fury.io/py/scrapli.svg)](https://badge.fury.io/py/scrapli)
[![Python 3.7](https://img.shields.io/badge/python-3.7-blue.svg)](https://www.python.org/downloads/release/python-370/)
[![Python 3.8](https://img.shields.io/badge/python-3.8-blue.svg)](https://www.python.org/downloads/release/python-380/)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)


scrapli
=======

scrapli -- scrap(e) (c)li --  is a python library focused on connecting to devices, specifically network devices
 (routers/switches/firewalls/etc.) via SSH or Telnet. The name scrapli -- is just "scrape cli" (as in screen scrape
 ) squished together! scrapli's goal is to be as fast and flexible as possible, while providing a well typed, well
  documented, simple API.

scrapli is built primarily in two parts: transport and channel. The transport layer is responsible for providing a file
-like interface to the target SSH server. The channel layer is responsible for reading and writing to the provided
 file-like interface.

There are three available "drivers" for the transport layer -- all of which inherit from a base transport class and
 provide the same file-like interface to the upstream channel. The transport drivers are:
 
- [paramiko]()
- [ssh2-python]()
- OpenSSH/System available SSH

A good question to ask at this point is probably "why?". Why multiple transport options? Why not just use paramiko
 like most folks do? Historically the reason for moving away from paramiko was simply speed. ssh2-python is a wrapper
  around the libssh2 C library, and as such is very very fast. In a prior project ([ssh2net]()), of which scrapli is the
   successor/evolution, ssh2-python was used with great success, however, it is a bit feature-limited, and development
    seems to have stalled.
   
This led to moving back to paramiko, which of course is a fantastic project with tons and tons of feature support
. Paramiko, however, does not "direct" OpenSSH support, and I don't believe it provides 100% full OpenSSH support
 either (ex: ControlPersist). Fully supporting an OpenSSH config file would be an ideal end goal for scrapli, something
  that may not be possible with Paramiko - ControlPersist in particular is very interesting to me.
 
With the goal of supporting all of the OpenSSH configuration options the final transport driver option is simply
 native system local SSH (almost certainly this won't work on Windows, but I don't have a Windows box to test on, or
  any particular interest in doing so). The implementation of using system SSH is of course a little bit messy
  , however scrapli takes care of that for you so you don't need to care about it! The payoff of using system SSH is of
   course that OpenSSH config files simply "work" -- no passing it to scrapli, no selective support, no need to set
    username or ports or any of the other config items that may reside in your SSH config file. The "system"
     transport driver is still a bit of a work in progress, but in testing has been reliable thus far.

The final piece of scrapli is the actual "driver" -- or the component that binds the transport and channel together and
 deals with instantiation of an scrapli object. There is a "base" driver object -- `Scrape` -- which provides essentially
  a "raw" SSH connection with read and write methods (provided by the channel object), and not much else. More
   specific "drivers" can inherit from this class to extend functionality of the driver to make it more friendly for
    network devices.


# Table of Contents

- [Documentation](#documentation)
- [Supported Platforms](#supported-platforms)
- [Installation](#installation)
- [Examples Links](#examples-links)
- [Basic Usage](#basic-usage)
  - [Native and Platform Drivers Examples](#native-and-platform-drivers-examples)
  - [Platform Regex](#platform-regex)
  - [Basic Operations -- Sending and Receiving](#basic-operations----sending-and-receiving)
  - [Response Objects](#response-objects)
  - [Handling Prompts](#handling-prompts)
  - [Driver Privilege Levels](#driver-privilege-levels)
  - [Sending Configurations](#sending-configurations)
  - [TextFSM/NTC-Templates Integration](#textfsmntc-templates-integration)
  - [Timeouts](#timeouts)
  - [Disabling Paging](#disabling-paging)
  - [Login Handlers](#login-handlers)
  - [SSH Config Support](#ssh-config-support)
- [FAQ](#faq)
- [Known Issues](#known-issues)
- [Linting and Testing](#linting-and-testing)


# Documentation

Documentation is auto-generated [using pdoc3](https://github.com/pdoc3/pdoc). Documentation is linted (see Linting and
 Testing section) via [pydocstyle](https://github.com/PyCQA/pydocstyle/) and [darglint](https://github.com/terrencepreilly/darglint).

Documentation is hosted via GitHub Pages and can be found [here.](https://carlmontanari.github.io/scrapli/docs/scrapli/index.html). 
 You can also view the readme as a web page [here.](https://carlmontanari.github.io/scrapli/)

To regenerate documentation locally, use the following make command:

```
make docs
```


# Supported Platforms

scrapli "core" drivers cover basically the [NAPALM](https://github.com/napalm-automation/napalm) platforms -- Cisco
 IOS-XE, IOS-XR, NX-OS, Arista EOS, and Juniper JunOS. These drivers provide an interface tailored to network device
  "screen-scraping" rather than just a generic SSH connection/channel.

At the moment there are five "core" drivers representing the most common networking platforms (outlined below)
, however in the future it would be possible for folks to contribute additional "community" drivers. It is unlikely
 that any additional "core" platforms would be added at the moment.

- Cisco IOS-XE (tested on: 16.04.01)
- Cisco NX-OS (tested on: 9.2.4)
- Juniper JunOS (tested on: 17.3R2.10)
- Cisco IOS-XR (tested on: 6.5.3)
- Arista EOS (tested on: 4.22.1F)

This "driver" pattern is pretty much exactly like the implementation in NAPALM. The driver extends the base class/base
  networking driver class with device specific functionality such as privilege escalation/de-escalation, setting
   appropriate prompts to search for, and picking out appropriate [ntc templates](https://github.com/napalm-automation/napalm)
    for use with TextFSM. 

All of this is focused on network device type SSH cli interfaces, but should work on pretty much any SSH connection
 (though there are almost certainly better options for non-network type devices!). This "base" (`Scrape`) connection does
  not handle any kind of device-specific operations such as privilege escalation or saving configurations, it is simply
   intended to be a bare bones connection that can interact with nearly any device/platform if you are willing to
    send/parse inputs/outputs manually.

The goal for all "core" devices will be to include functional tests that can run against [vrnetlab](https://github.com/plajjan/vrnetlab)
 containers to ensure that the "core" devices are as thoroughly tested as is practical. 


# Installation

You should be able to pip install it "normally":

```
pip install scrapli
```

To install from this repositories master branch:

```
pip install git+https://github.com/carlmontanari/scrapli
```

To install from source:

```
git clone https://github.com/carlmontanari/scrapli
cd scrapli
python setup.py install
```

scrapli has made an effort to have as few dependencies as possible. The "core" of scrapli can run with nothing other
 than standard library! If you wish to use paramiko or ssh2-python as a driver, however, you of course need to install
  those. This can be done with pip:

```
pip install scrapli[paramiko]
```

The available optional installation options are:

- paramiko
- ssh2 (ssh2-python)
- textfsm (textfsm and ntc-templates)

As for platforms to *run* scrapli on -- it has and will be tested on MacOS and Ubuntu regularly and should work on any
 POSIX system.


# Examples Links

- [Basic "native" Scrape operations](/examples/basic_usage/scrapli_driver.py)
- [Basic "driver" Scrape operations](/examples/basic_usage/iosxe_driver.py)
- [Setting up basic logging](/examples/logging/basic_logging.py)
- [Using SSH Key for authentication](/examples/ssh_keys/ssh_keys.py)
- [Using SSH config file](/)


# Basic Usage

## Native and Platform Drivers Examples

Example Scrape "native/base" connection:

```python
from scrapli import Scrape

my_device = {"host": "172.18.0.11", "auth_username": "vrnetlab", "auth_password": "VR-netlab9"}
conn = Scrape(**my_device)
conn.open()
# do stuff!
```

Example IOS-XE driver setup. This also shows using context manager which is also supported on "native" mode -- when
 using the context manager there is no need to call the "open_shell" method:

```python
from scrapli.driver.core import IOSXEDriver

my_device = {"host": "172.18.0.11", "auth_username": "vrnetlab", "auth_password": "VR-netlab9"}
with IOSXEDriver(**my_device) as conn:
    print(conn)
    # do stuff!
```

## Platform Regex

Due to the nature of SSH there is no good way to know when a command has completed execution. Put another way, when
 sending any command, data is returned over a socket, that socket doesn't ever tell us when it is "done" sending the
  output from the command that was executed. In order to know when the session is "back at the base prompt/starting
   point" scrapli uses a regular expression pattern to find that base prompt.

This pattern is contained in the `comms_prompt_pattern` setting, and is perhaps the most important argument to getting
 scrapli working.

The "base" (default, but changeable) pattern is:

`"^[a-z0-9.\-@()/:]{1,20}[#>$]$"`

*NOTE* all `comms_prompt_pattern` should use the start and end of line anchors as all regex searches in scrapli are
 multline (this is an important piece to making this all work!). While you don't *need* to use the line anchors its
  probably a really good idea!

The above pattern works on all "core" platforms listed above for at the very least basic usage. Custom prompts or
 hostnames could in theory break this, so be careful!

If you do not wish to match Cisco "config" level prompts you could use a `comms_prompt_pattern` such as:

`"^[a-z0-9.-@]{1,20}[#>$]$"`

If you use a platform driver, the base prompt is set in the driver so you don't really need to worry about this!

The `comms_prompt_pattern` pattern can be changed at any time at or after instantiation of an scrapli object. Changing
 this *can* break things though, so be careful!


## Basic Operations -- Sending and Receiving

Sending inputs and receiving outputs is done through the base Scrape object or your selected driver object. The inputs
 /outputs all are processed (sent/read) via the channel object. If using the base `Scrape` object you must use the
  `channel.send_inputs` method -- the `NetworkDriver` and platform specific drivers have a `send_commands` method as
   outlined below. The following example shows sending a "show version" command as a string. Also shown: `send_inputs
   ` accepts a list/tuple of commands.

```python
from scrapli import Scrape

my_device = {"host": "172.18.0.11", "auth_username": "vrnetlab", "auth_password": "VR-netlab9"}
with Scrape(**my_device) as conn:
    results = conn.channel.send_inputs("show version")
    results = conn.channel.send_inputs(("show version", "show run"))
```

When using a network "driver", it is more desirable to use the `send_commands` method to send commands (commands that
 would be ran at privilege exec in Cisco terms, or similar privilege level for the other platforms). `send_commands` is
  just a thin wrapper around `send_inputs`, however it ensures that the device is at the appropriate prompt
   (`default_desired_priv` attribute of the specific driver, see [Driver Privilege Levels](#driver-privilege-levels)).

```python
from scrapli.driver.core import IOSXEDriver

my_device = {"host": "172.18.0.11", "auth_username": "vrnetlab", "auth_password": "VR-netlab9"}
with IOSXEDriver(**my_device) as conn:
    results = conn.send_commands("show version")
    results = conn.send_commands(("show version", "show run"))
```


## Response Objects

All read operations result in a `Response` object being created. The `Response` object contains attributes for the command
 sent (`channel_input`), start/end/elapsed time, and of course the result of the command sent.

```python
from scrapli.driver.core import IOSXEDriver

my_device = {"host": "172.18.0.11", "auth_username": "vrnetlab", "auth_password": "VR-netlab9"}
with IOSXEDriver(**my_device) as conn:
    results = conn.send_commands("show version")
    print(results[0].elapsed_time)
    print(results[0].result)
```


## Handling Prompts

In some cases you may need to run an "interactive" command on your device. The `channel.send_inputs_interact` method
 can be used to handle these situations if using the base `Scrape` driver -- if using the `NetworkBase` or any of the
  platform drivers, the `send_interactive` method can be used to accomplish this -- `send_interactive` is just a thin
   wrapper around the `channel.send_inputs_interact` method for convenience (not having to call a channel method
    basically). This method accepts a tuple containing the initial input (command) to send, the expected prompt after
     the initial send, the response to that prompt, and the final expected prompt -- basically telling scrapli when it
      is done with the interactive command. In the below example the expectation is that the current/base prompt is
       the final expected prompt, so we can simply call the `get_prompt` method to snag that directly off the router.

```python
from scrapli import Scrape

my_device = {"host": "172.18.0.11", "auth_username": "vrnetlab", "auth_password": "VR-netlab9"}
interact = ["clear logging", "Clear logging buffer [confirm]", "\n"]

with Scrape(**my_device) as conn:
    interactive = conn.channel.send_inputs_interact(
                ("clear logging", "Clear logging buffer [confirm]", "\n", conn.get_prompt())
            )
```

Or with the `NetworkDriver` or any platform driver:

```python
from scrapli.driver import NetworkDriver

my_device = {"host": "172.18.0.11", "auth_username": "vrnetlab", "auth_password": "VR-netlab9"}
interact = ["clear logging", "Clear logging buffer [confirm]", "\n"]

with NetworkDriver(**my_device) as conn:
    interactive = conn.send_interactive(
                ("clear logging", "Clear logging buffer [confirm]", "\n", conn.get_prompt())
            )
```


## Driver Privilege Levels

The "core" drivers understand the basic privilege levels of their respective device types. As mentioned previously
, the drivers will automatically attain the "privilege_exec" (or equivalent) privilege level prior to executing "show
" commands. If you don't want this "auto-magic" you can use the base driver (Scrape). The privileges for each device
 are outlined in named tuples in the platforms `driver.py` file. 
 
As an example, the following privilege levels are supported by the IOSXEDriver:

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

my_device = {"host": "172.18.0.11", "auth_username": "vrnetlab", "auth_password": "VR-netlab9"}

with IOSXEDriver(**my_device) as conn:
    conn.acquire_priv("configuration")
```


## Sending Configurations

When using the native mode (`Scrape` object), sending configurations is no different than sending commands and is done via
 the `send_inputs` method. You must manually ensure you are in the correct privilege/mode.
 
When using any of the core drivers or the base `NetworkDriver`, you can send configurations via the `send_configs` method
 which will handle privilege escalation for you. As with the `send_commands` and `send_inputs` methods -- you can
  send a single string or a list/tuple of strings.

```python
from scrapli.driver.core import IOSXEDriver

my_device = {"host": "172.18.0.11", "auth_username": "vrnetlab", "auth_password": "VR-netlab9"}

with IOSXEDriver(**my_device) as conn:
    conn.send_configs(("interface loopback123", "description configured by scrapli"))
```


## TextFSM/NTC-Templates Integration

scrapli supports parsing output with TextFSM. This of course requires installing TextFSM and having ntc-templates
 somewhere on your system. When using a driver you can pass `textfsm=True` to the `send_commands` method to
  automatically try to parse all output. Parsed/structured output is stored in the `Response` object in the
   `structured_result` attribute. Alternatively you can use the `textfsm_parse_output` method of the driver to parse
    output in a more manual fashion. This method accepts the string command (channel_input) and the text result and
     returns structured data; the driver is already configured with the ntc-templates device type to find the correct
      template. 

```python
from scrapli.driver.core import IOSXEDriver

my_device = {"host": "172.18.0.11", "auth_username": "vrnetlab", "auth_password": "VR-netlab9"}

with IOSXEDriver(**my_device) as conn:
    results = conn.send_commands("show version", textfsm=True)
    print(results[0].structured_result)
    # or parse manually...
    results = conn.send_commands("show version")
    structured_output = conn.textfsm_parse_output("show version", results[0].result)
```

scrapli also supports passing in templates manually (meaning not using the pip installed ntc-templates directory to
 find templates) if desired. The `scrapli.helper.textfsm_parse` function accepts a string or loaded (TextIOWrapper
 ) template and output to parse. This can be useful if you have custom or one off templates or don't want to pip
  install ntc-templates.
  
```python
from scrapli.driver.core import IOSXEDriver
from scrapli.helper import textfsm_parse

my_device = {"host": "172.18.0.11", "auth_username": "vrnetlab", "auth_password": "VR-netlab9"}

with IOSXEDriver(**my_device) as conn:
    results = conn.send_commands("show version")
    structured_result = textfsm_parse("/path/to/my/template", results[0].result)
```

*NOTE*: If a template does not return structured data an empty dict will be returned!


## Timeouts

scrapli supports several timeout options. The simplest is the `timeout_socket` which controls the timeout for... setting
 up the underlying socket in seconds. Value should be a positive, non-zero number, however ssh2 and paramiko
  transport options support floats.
 
`timeout_ssh` sets the timeout for the actual SSH session when using ssh2 or paramiko transport options. When using
 system SSH, this is currently only used as the timeout timer for authentication.
 
Finally, `timeout_ops` sets a timeout value for individual operations -- or put another way, the timeout for each
 send_input operation.


## Disabling Paging

scrapli native driver attempts to send `terminal length 0` to disable paging by default. In the future this will
 likely be removed and relegated to the device drivers only. For all drivers, there is a standard disable paging
  string already configured for you, however this is of course user configurable. In addition to passing a string to
   send to disable paging, scrapli supports passing a callable. This callable should accept the drivers reference to
    self as the only argument. This allows for users to create a custom function to disable paging however they like
    . This callable option is supported on the native driver as well. In general it is probably a better idea to
     handle this by simply passing a string, but the goal is to be flexible so the callable is supported.
    
```python
from scrapli.driver.core import IOSXEDriver

def iosxe_disable_paging(cls):
    cls.send_commands("term length 0")

my_device = {"host": "172.18.0.11", "auth_username": "vrnetlab", "auth_password": "VR-netlab9", "session_disable_paging": iosxe_disable_paging}

with IOSXEDriver(**my_device) as conn:
    print(conn.get_prompt())
```


## Login Handlers

Some devices have additional prompts or banners at login. This generally causes issues for SSH screen scraping
 automation. scrapli supports -- just like disable paging -- passing a string to send or a callable to execute after
  successful SSH connection but before disabling paging occurs. By default this is an empty string which does nothing.


## SSH Config Support

scrapli supports using OpenSSH configuration files in a few ways. For "system" SSH driver, passing a path to a config
 file will simply make scrapli "point" to that file, and therefore use that configuration files attributes (because it
  is just exec'ing system SSH!). Soon SSH support that exists in ssh2net will be ported over to scrapli for ssh2-python
   and paramiko transport drivers.
   
*NOTE* -- when using the system (default) SSH transport driver scrapli does NOT disable strict host checking by default
. Obviously this is the "smart" behavior, but it can be overridden on a per host basis in your SSH config file, or by
 passing `False` to the "auth_strict_key" argument on object instantiation.

```python
from scrapli.driver.core import IOSXEDriver

my_device = {"host": "172.18.0.11", "ssh_config_file": "~/mysshconfig", "auth_strict_key": False, "auth_password": "VR-netlab9"}

with IOSXEDriver(**my_device) as conn:
    print(conn.get_prompt())
```


# FAQ

- Question: Why build this? Netmiko exists, Paramiko exists, Ansible exists, etc...?
  - Answer: I built ssh2net to learn -- to have a goal/target for writing some code. scrapli is an evolution of the
   lessons learned building ssh2net. About mid-way through building ssh2net I realized it may actually be kinda good
    at doing... stuff. So, sure there are other tools out there, but I think scrapli its pretty snazzy and fills in some
     of the gaps in other tools. For example scrapli is 100% compliant with strict mypy type checking, very uniformly
      documented/linted, contains a results object for every operation, is very very fast, is very flexible, and in
       general pretty awesome! Finally, while I think in general that SSH "screen scraping" is not "sexy" or even
        "good", it is the lowest common denominator for automation in the networking world. So I figured I could try
         to make the fastest, most flexible library around for SSH network automation! 
- Question: Is this better than Netmiko/Paramiko/Ansible?
  - Answer: Nope! It is different though! The main focus is just to be stupid fast. It is very much that. It *should* be
  super reliable too as the timeouts are very easy/obvious to control, and it should also be very very very easy to
   adapt to any other network-y type CLI.
- Question: Is this easy to use?
  - Answer: Yep! The "native" usage is pretty straight forward -- the thing to remember is that it doesn't do "things
  " for you like Netmiko does for example, so its a lot more like Paramiko in that regard. That said you can use one
   of the available drivers to have a more Netmiko-like experience -OR- write your own driver as this has been built
    with the thought of being easily extended.
- Why do I get a "conn (or your object name here) has no attribute channel" exception when using the base `Scrape` or
 `NetworkDriver` objects?
  - Answer: Those objects do not "auto open", and the channel attribute is not assigned until opening the connection
  . Call `conn.open()` (or your object name in place of conn) to open the session and assign the channel attribute.
- Other questions? Ask away!


# Known Issues

## SSH2-Python

- Arista EOS uses keyboard interactive authentication which is currently broken in the pip-installable version
 of ssh2-python (as of January 2020). GitHub user [Red-M](https://github.com/Red-M) has contributed to and fixed this
  particular issue but the fix has not been merged. If you would like to use ssh2-python with EOS I suggest cloning
   and installing via Red-M's repository or my fork of Red-M's fork!

- Use the context manager where possible! More testing needs to be done to confirm/troubleshoot, but limited testing
 seems to indicate that without properly closing the connection there appears to be a bug that causes Python to crash
  on MacOS at least. More to come on this as I have time to poke it more! I believe this is only occurring on the
   latest branch/update (i.e. not on the pip installable version).
  
 
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

I broke testing into two main categories -- unit and functional. Unit is what you would expect -- unit testing the code.
 Functional testing connects to virtual devices in order to more accurately test the code. Unit tests cover quite a
  bit of the code base due to mocking the FileIO that the channel reads/writes to. This gives a pretty high level of
   confidence that at least object instantiation and channel read/writes will generally work... Functional tests
    against virtual devices helps reinforce that and gets coverage for the transport classes.

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


Executing the functional tests is a bit more complicated! First, thank you to Kristian Larsson for his great tool [vrnetlab](https://github.com/plajjan/vrnetlab)! All functional tests are built on this awesome platform that allows for easy creation of containerized network devices.

Basic functional tests exist for all "core" platform types (IOSXE, NXOS, IOSXR, EOS, Junos). Vrnetlab currently only supports the older emulation style NX-OS devices, and *not* the newer VM image n9kv. I have made some very minor tweaks to vrnetlab locally in order to get the n9kv image running -- I have raised a PR to add this to vrnetlab proper. Minus the n9kv tweaks, getting going with vrnetlab is fairly straightforward -- simply follow Kristian's great readme docs. For the Arista EOS image -- prior to creating the container you should boot the device and enter the `zerotouch disable` command. This allows for the config to actually be saved and prevents the interfaces from cycling through interface types in the container (I'm not clear why it does that but executing this command before building the container "fixes" this!). After creating the image(s) that you wish to test, rename the image to the following format:

```
scrapli[PLATFORM]
```

The docker-compose file here will be looking for the container images matching this pattern, so this is an important bit! The container image names should be:

```
scrapliciscoiosxe
scraplicisconxos
scrapliciscoiosxr
scrapliaristaeos
scraplijuniperjunos
```

You can tag the image names on creation (following the vrnetlab readme docs), or create a new tag once the image is built:

```
docker tag [TAG OF IMAGE CREATED] scrapli[VENDOR][OS]
```

*NOTE* I have added vty lines 5-98 on the CSR image -- I think the connections opening/closing so quickly during
 testing caused them to get hung. Testing things more slowly (adding time.sleep after closing connections) fixed this
  but that obviously made the testing time longer, so this seemed like a better fix. This change will be in my fork
   of vrnetlab or you can simply modify the `line vty 0 5` --> `line vty 0 98` in the `luanch.py` for the CSR in your
    vrnetlab clone.


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
