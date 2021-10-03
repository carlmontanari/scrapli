# Project Details

## What is scrapli

scrapli is a python library focused on connecting to devices, specifically network devices via Telnet, SSH or NETCONF.

scrapli is built primarily in three parts: transport, channel, and driver. The transport layer is responsible for
 providing a file-like interface to the target server. The channel layer is responsible for reading and writing
  to the provided file-like interface. Finally, the driver provides the user facing API/interface to scrapli.

There are **six** available "transports" in scrapli "core" -- all of which inherit from a base transport classes
 and provide the same file-like interface to the upstream channel.


### Transports

The available transport plugins are:

- `system` -- wrapper around OpenSSH/System available SSH binary
- `telnet` -- Python standard library telnetlib
- `asynctelnet` -- Python standard library asyncio stream
- [`asyncssh`](https://github.com/ronf/asyncssh) -- wrapper around asyncssh library
- [`ssh2`](https://github.com/ParallelSSH/ssh2-python) -- wrapper around ssh2-python library
- [`paramiko`](https://github.com/paramiko/paramiko) -- wrapper around paramiko library

A good question to ask at this point is probably "why?". Why multiple transport options? Why not just use paramiko
 like most folks do? Historically the reason for moving away from paramiko was simply speed. ssh2-python is a wrapper
  around the libssh2 C library, and as such is very, very fast. In a prior project
   ([ssh2net](https://github.com/carlmontanari/ssh2net)), of which scrapli is the successor/evolution, ssh2-python
    was used with great success, however, it is a bit feature-limited, and development had stalled around the same
     time scrapli was getting going.

This led to moving back to paramiko, which of course is a fantastic project with tons and tons of feature support
. Paramiko, however, does not provide "direct" OpenSSH support (as in -- auto-magically like when you ssh on your
 normal shell), and I don't believe it provides 100% full OpenSSH support either (ex: ControlPersist). Fully
  supporting an OpenSSH config file would be an ideal end goal for scrapli, something that may not be possible with
   Paramiko - ControlPersist in particular is very interesting to me.

With the goal of supporting all OpenSSH configuration options the primary transport driver option is simply
 native system local SSH. The implementation of using system SSH is of course a little bit messy, however scrapli
  takes care of that for you so you don't need to care about it! The payoff of using system SSH is of course that
   OpenSSH config files simply "work" -- no passing it to scrapli, no selective support, no need to set username or
    ports or any of the other config items that may reside in your SSH config file. This driver will likely be the
     focus of most development for this project, though I will try to keep the other transport drivers -- in
      particular asyncssh -- as close to parity as is possible/practical.

Adding telnet support via telnetlib was trivial, as the interface is basically the same as SystemSSH, and it turns out
 telnet is still actually useful for things like terminal servers and the like!

Next, perhaps the most interesting scrapli transport plugin is the `asyncssh` transport. This transport option 
represented a very big change for scrapli as the entire "backend" was basically re-worked in order to provide the 
exact same API for both synchronous and asynchronous applications.

Lastly, the `asynctelnet` transport is the latest (and perhaps last?!) transport plugin. This transport plugin was 
built with only the python standard library (just like system/telnet) and as such it is part of scrapli "core".


### Channel

The "channel" sits between the transports and the drivers -- the channel is where much of the magic happens! The 
channel is responsible for all prompt finding, sending commands or configs, and generally interacting with the 
device. The channel essentially reads from and writes to the underlying transport for a given connection. The 
Channel doesn't need to know or care about which transport you pick! (except of course to know if it is async or 
synchronous)


### Drivers

The final piece of scrapli is the actual "driver" -- or the component that binds the transport and channel together and
 deals with instantiation of a scrapli object. There is a "base" driver object -- `Driver` -- which provides essentially
  a "raw" SSH (or telnet) connection that is created by instantiating a Transport object, and a Channel object
  . `Drive` provides (via Channel) read/write methods and not much else -- this should feel familiar if you have
   used paramiko in the past. More specific "drivers" can inherit from this class to extend functionality of the
    driver to make it more friendly for network devices. In fact, there is a `GenericDriver` class that inherits from
     `Scrape` and provides a base driver to work with if you need to interact with a device not represented by one of
      the "core" drivers. Next, the `NetworkDriver` class inherits from `GenericDriver`. The `NetworkDriver` isn't
       really meant to be used directly though, but to be further extended and built upon instead. As this library is
        focused on interacting with network devices, an example scrapli driver (built on the `NetworkDriver`) would
         be the `IOSXEDriver` -- to, as you may have guessed , interact with devices running Cisco's IOS-XE operating
          system.

It should be noted that this is a bit of an oversimplification of the architecture of scrapli, but it is accurate
. Scrapli has "base", "sync", and "async" versions of the core components. The "base" portion is made up of mixin
 classes that get "mixed in" to the sync or async versions of the component. For example there is a
  `NetworkDriverBase` class that is "mixed in" to the `NetworkDriver` and `AsyncNetworkDriver` classes. The mixin
   provides consistent helper like functions (sync functions) that can be used by the two driver classes -- this
    allows the sync/async components to have as little code as possible helping to keep the API consistent for both
     synchronous and asynchronous users.


## Supported Platforms

scrapli "core" drivers cover basically the [NAPALM](https://github.com/napalm-automation/napalm) platforms -- Cisco
 IOS-XE, IOS-XR, NX-OS, Arista EOS, and Juniper JunOS. These drivers provide an interface tailored to network device
  "screen-scraping" rather than just a generic SSH connection/channel. It is important to note that there is a
   synchronous and an asynchronous version of each of these drivers. Below are the core driver platforms and
   regularly tested version.

- Cisco IOS-XE (tested on: 16.12.03)
- Cisco NX-OS (tested on: 9.2.4)
- Juniper JunOS (tested on: 17.3R2.10)
- Cisco IOS-XR (tested on: 6.5.3)
- Arista EOS (tested on: 4.22.1F)

It is unlikely that any additional "core" platforms would be added, however the `scrapli_community` project is
 available for users to contribute any other platforms they would like to see scrapli support! Please see the
  [scrapli_community project](https://github.com/scrapli/scrapli_community) to check out what community platforms exist!

The "driver" pattern is pretty much exactly like the implementation in NAPALM. The driver extends the base class
 (`Scrape`) and the base networking driver class (`NetworkDriver`) with device specific functionality such as privilege
  escalation/de-escalation, setting appropriate prompts to search for, and picking out appropriate
  [ntc templates](https://github.com/networktocode/ntc-templates) for use with TextFSM, and so on.

All of this is focused on network device type Telnet/SSH cli interfaces, but should work on pretty much any SSH
 connection (though there are almost certainly better options for non-network type devices!). The "base" (`Driver`)
  and `GenericDriver` connections do not handle any kind of device-specific operations such as privilege
  escalation or saving configurations, they are simply intended to be a bare-bones connection that can interact with
   nearly any device/platform if you are willing to send/parse inputs/outputs manually. In most cases it is assumed
    that users will use one of the "core" drivers.

The goal for all "core" devices will be to include functional tests that can run against
[vrnetlab](https://github.com/plajjan/vrnetlab) containers to ensure that the "core" devices are as thoroughly tested
 as is practical.


## Related Scrapli Libraries

This repo is the "main" or "core" scrapli project, however there are other libraries/repos in the scrapli family
 -- here is a list/link to all of the other scrapli things!


- [nornir_scrapli](/more_scrapli/nornir_scrapli)
- [scrapli_community](/more_scrapli/scrapli_community)
- [scrapli_cfg](/more_scrapli/scrapli_cfg)
- [scrapli_replay](/more_scrapli/scrapli_replay)
- [scrapli_netconf](/more_scrapli/scrapli_netconf)
