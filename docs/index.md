# Scrapli

scrapli -- scrap(e c)li -- is a set of libraries created to interact with devices via the CLI, and NETCONF.


## What Scrapli Is

- A **Zig** library (libscrapli) that enables interacting with servers via CLI (telnet/SSH) and NETCONF (via SSH)
  - libscrapli supports multiple "transports" -- that is the thing that actually sends/receivces from the server:
    - telnet
    - "bin" (wrapper around a binary, usually `/bin/ssh`, meaning, typically *openssh*)
    - libssh2
  - Methods for interacting with CLIs such as `getPrompt`, `sendInput`, and `readWithCallbacks`
  - Customizable "definitions" for defining characteristics of a CLI server -- i.e. different "modes" of the device (i.e: configuration vs privileged exec), commands that should be invoked on connection open or close, and more
  - Methods for interacting with NETCONF servers such as `action`, `get`, `getConfig`, etc.
- **Python** bindings to libscrapli (scrapli)
- **Go** bindings to libscrapli (scrapligo)

## What Scrapli Isn't

- A library/tool with explicit support for every device type -- meaning scrapli (really, libscrapli) is intended to be flexible enough that it can be adapted to work with most any CLI device (NETCONF should of course "just work" because "standards"!) through the platform definition system, however, there may be exceptions!
- An automation platform -- scrapli is a tool that can be used *in* an automation platform, but it
is simply the client to send/receive from devices
- A Python or Go library -- the Python and Go bits are *mostly* wrappers around the core zig libscrapli project; if you are interested in contributing you likely need to look at libscrapli, and therefore need to work with zig


## Why Scrapli

- User experience: scrapli -- in all its flavors -- provides a pleasant developer experience with well typed, documented, and tested code
- Customizability: (CLI) [platforms](details.md#platform-definitions) (unless you are writing zig) are simply YAML files -- have a device that isn't "supported"? Just create a simple YAML file specifying some regular expressions and maybe some inputs to send on a session open and you're set
- Small footprint: scrapli has very few dependencies regardless of "which" scrapli you are looking at -- for the zig core, we rely on only a few zig and C libraries (zig-yaml, zig-xml, pcre2, and libssh2), and the Python and Go bits primarily only rely on libscrapli itself (Python using ctypes, and Go using purego)
- Language support: zig, Python, or Go, your pick! scrapli is consistent and unified across these languages with only minor differences in the Python and Go variations in order to be idiomatic to the respective language. Additionally, any language that can interface with the C ABI could make use of libscrapli.


## Philosophy

Some general philosophical / navel gazing type thoughts about the philospohy/thinking behind Scrapli.

- Do as much as possible in zig. This keeps all the core logic in one place
- Be idiomatic -- historically scrapligo did *not* use contexts for cancellation for example, that sucked! Now the Python and Go shims should be idiomatic and feel nice to developers that are used to and appreciate the respective language
- Have as few (run/compile time) dependencies as possible -- this keeps it much easier to stay up to date, and of course makes the overall footprint nice and tidy
- Be flexible, but don't say yes too often. Basically, scrapli should be useful to a broad set of folks, but it should not adopt corner-case functionality that can be accomplished fairly easily by those users who would want said functionality


## History

As the name suggests, scrapli began life as a telnet/SSH client built specifically for interacting with "network" devices (routers/switches/etc.). This "original" scrapli was written in Python. Eventually, a go version was created, aptly named "scrapligo". Initially these two flavors of scrapli had a fairly high degree of parity. However, as time went on the two libraries began to diverge. This created a maintainer burden, and inconsistency for those few folks who switch between scrapli and scrapligo.

In addition to the divergence between Python and Go scrapli flavors, there has also been a bit of a divergence with respect to NETCONF -- for example NETCONF functionality exists directly in scrapligo, however was a separate library for Python (scrapli-netconf). Moreover, there were methods in scrapligo that were not supported (and could not easily be ported) in scrapli-netconf.

Eventually, the idea of a unified scrapli became very compelling (to me, carl, at least) -- stuffing all the important logic of scrapli into a single place and providing bindings to that core library. This would obviously be useful from a maintainer perspective, but also ensure a consistent experience when perhaps using Python for prototyping, but Go for production.

Zig was chosen as the language to write the unified scrapli (libscrapli) in. While any low level language -- or really, any language that could be compiled to shared objects -- would work, zig seemed like a nice choice. Once the zig core was in place, it was a matter of figuring out the best way for Python and Go to consume it -- this ended up being ctypes and purego respectively. For Python, it was an obvious choice. For Go, purego means that we are able to do CGO type things without the limitations of CGO (i.e. we can still cross-compile Go programs using scrapligo even though we load the zig/C libscrapli bits).
