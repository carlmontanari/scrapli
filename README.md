[![Supported Versions](https://img.shields.io/pypi/pyversions/scrapli.svg)](https://pypi.org/project/scrapli)
[![PyPI version](https://badge.fury.io/py/scrapli.svg)](https://badge.fury.io/py/scrapli)
[![Weekly Build](https://github.com/carlmontanari/scrapli/workflows/Weekly%20Build/badge.svg)](https://github.com/carlmontanari/scrapli/actions?query=workflow%3A%22Weekly+Build%22)
[![Coverage](https://codecov.io/gh/carlmontanari/scrapli/branch/master/graph/badge.svg)](https://codecov.io/gh/carlmontanari/scrapli)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-blueviolet.svg)](https://opensource.org/licenses/MIT)

scrapli
=======

---

**Documentation**: <a href="https://carlmontanari.github.io/scrapli" target="_blank">https://carlmontanari.github.io/scrapli</a>

**Source Code**: <a href="https://github.com/carlmontanari/scrapli" target="_blank">https://github.com/carlmontanari/scrapli</a>

**Examples**: <a href="https://github.com/carlmontanari/scrapli/tree/master/examples" target="_blank">https://github.com/carlmontanari/scrapli/tree/master/examples</a>

---

scrapli -- scrap(e c)li --  is a python 3.6+ library focused on connecting to devices, specifically network devices
 (routers/switches/firewalls/etc.) via Telnet or SSH.

#### Key Features:

- __Easy__: It's easy to get going with scrapli -- check out the documentation and example links above, and you'll be 
  connecting to devices in no time.
- __Fast__: Do you like to go fast? Of course you do! All of scrapli is built with speed in mind, but if you really 
  feel the need for speed, check out the `ssh2` transport plugin to take it to the next level!
- __Great Developer Experience__: scrapli has great editor support thanks to being fully typed; that plus thorough 
  docs make developing with scrapli a breeze.
- __Well Tested__: Perhaps out of paranoia, but regardless of the reason, scrapli has lots of tests! Unit tests 
  cover the basics, regularly ran functional tests connect to virtual routers to ensure that everything works IRL! 
- __Pluggable__: scrapli provides a pluggable transport system -- don't like the currently available transports, 
  simply extend the base classes and add your own! Need additional device support? Create a simple "platform" in 
  [scrapli_community](https://github.com/scrapli/scrapli_community) to easily add new device support!
- __But wait, there's more!__: Have NETCONF devices in your environment, but love the speed and simplicity of 
  scrapli? You're in luck! Check out [scrapli_netconf](https://github.com/scrapli/scrapli_netconf)!
- __Concurrency on Easy Mode__: [Nornir's](https://github.com/nornir-automation/nornir) 
  [scrapli plugin](https://github.com/scrapli/nornir_scrapli) gives you all the normal benefits of scrapli __plus__ 
  all the great features of Nornir.


## Requirements

MacOS or \*nix<sup>1</sup>, Python 3.6+

scrapli "core" has no requirements other than the Python standard library<sup>2</sup>.


<sup>1</sup> Although many parts of scrapli *do* run on Windows, Windows is not officially supported

<sup>2</sup> Python 3.6 requires the `dataclass` backport as well as third party `async_generator` library, Python 3.
7+ has no external dependencies for scrapli "core"


## Installation

```
pip install scrapli
```

See the [docs](https://carlmontanari.github.io/scrapli/user_guide/installation) for other installation methods/details.



## A simple Example

```python
from scrapli import Scrapli

device = {
   "host": "172.18.0.11",
   "auth_username": "vrnetlab",
   "auth_password": "VR-netlab9",
   "auth_strict_key": False,
   "platform": "cisco_iosxe"
}

conn = Scrapli(**device)
conn.open()
print(conn.get_prompt())
```
