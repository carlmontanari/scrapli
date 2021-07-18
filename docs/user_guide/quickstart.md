# Quick Start Guide


## Installation

In most cases installation via pip is the simplest and best way to install scrapli.
See [here](/user_guide/installation) for advanced installation details.

```
pip install scrapli
```


## A Simple Example

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

- [Basic "native" Scrape operations](https://github.com/carlmontanari/scrapli/tree/master/examples/basic_usage/scrapli_driver.py)
- [Basic "GenericDriver" operations](https://github.com/carlmontanari/scrapli/tree/master/examples/basic_usage/generic_driver.py)
- [Basic "core" Driver operations](https://github.com/carlmontanari/scrapli/tree/master/examples/basic_usage/iosxe_driver.py)
- [Basic async operations](https://github.com/carlmontanari/scrapli/tree/master/examples/async_usage/async_iosxe_driver.py)
- [Async multiple connections](https://github.com/carlmontanari/scrapli/tree/master/examples/async_usage/async_multiple_connections.py)
- [Setting up basic logging](https://github.com/carlmontanari/scrapli/tree/master/examples/logging/basic_logging.py)
- [Using SSH Key for authentication](https://github.com/carlmontanari/scrapli/tree/master/examples/ssh_keys/ssh_keys.py)
- [Using SSH config file](https://github.com/carlmontanari/scrapli/tree/master/examples/ssh_config_files/ssh_config_file.py)
- [Parse output with TextFSM/ntc-templates](https://github.com/carlmontanari/scrapli/tree/master/examples/structured_data/structured_data_textfsm.py)
- [Parse output with Genie](https://github.com/carlmontanari/scrapli/tree/master/examples/structured_data/structured_data_genie.py)
- [Transport Options](https://github.com/carlmontanari/scrapli/tree/master/examples/transport_options/system_ssh_args.py)
- [Configuration Modes - IOSXR Configure Exclusive](https://github.com/carlmontanari/scrapli/tree/master/examples/configuration_modes/iosxr_configure_exclusive.py)
- [Configuration Modes - EOS Configure Session](https://github.com/carlmontanari/scrapli/tree/master/examples/configuration_modes/eos_configure_session.py)
- [Banners, Macros, and other "weird" Things](https://github.com/carlmontanari/scrapli/tree/master/examples/banners_macros_etc/iosxe_banners_macros_etc.py)


## Other Stuff

Other scrapli related docs/blogs/videos/info:

- [Scrapli on Dmitry Figol's Network Automation Channel](https://www.youtube.com/watch?v=OJa2typq7yI)
- [Scrapli Intro on Wim Wauter's blog](https://blog.wimwauters.com/networkprogrammability/2020-04-09_scrapli_introduction/)
- [Scrapli on the Packet Pushers Heavy Networking Podcast](https://packetpushers.net/podcast/heavy-networking-532-scrapli-is-a-netmiko-alternative/)
- [IPvZero's Network Automation Course (including scrapli!) on CBT Nuggets (paid resource)](https://www.cbtnuggets.com/it-training/networking/network-automation-cisco-python?utm_source=trainer&utm_medium=trainer&utm_campaign=john-mcgovern)
- [Rick Donato's Scrapli Course (paid resource)](https://www.packetcoders.io/network-configuration-with-scrapli/)