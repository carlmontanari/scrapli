# Legacy Migration

This page attempts to outline the changes from "legacy" scrapli to the newer libscrapli based libraries. Thankfully the surface area for the scrapli API is pretty small, so while the changes are dramatic, it shouldn't be *too* terribly difficult to migrate any existing code to the newer format.


## General Changes

- All the smart stuff happens in Zig! Libscrapli is basically the core of everything now, Python and Go packages are thin, idiomatic wrappers around libscrapli.
- scrapli/scrapligo *will not work* without libscrapli -- please see [the installation section](installation.md#go) for more info.
- No more generic vs network driver -- libscrapli dropped the idea of sending "configurations". There are now only inputs, you can send those inputs at any "mode" you would like (including of course "configuration" mode). With this change in mentality, there is no point in dividing things between generic and network, so that division does not exist anymore!
- scrapli community has been deprecated in favor of scrapli definitions -- this has been a long time coming, starting with scrapligo, where "definitions" were strictly YAML. This of course makes things more portable, at the expense of being less flexible (though it seems only FortiOS will have issues with this, see python changes below).
- You do *not* need to specify a platform anymore when using a Cli connection -- there is very generic default platform that will be auto selected if you do not provide one. You probably should still provide one to match your target device so you have proper pagination disabling and any other things like that.
- Privilege levels have been replaced with "modes" -- mostly this is a semantic change as you can still send inputs at a given mode/privilege level, and most definitions will try to acquire a sane default/initial mode upon connection.
- There is a lot more NETCONF support generally -- while not all RFC RPCs are supported, there is still a "raw" RPC method that should allow you to send whatever you need to your NETCONF server.
- The default `bin` transport now disables strict key checking by default -- this has historically been a pain point for folks using scrapli for the first time. You *should* enable this... but... up to you!
- The default `bin` transport no longer disables looking up default ssh config files (`-F /dev/null`) by default -- that means it will automatically honor any of your ssh config file settings by default.
- There is no longer any `auth_secondary` -- this has historically been used for "enable" passwords. This functionality has been replaced by *lookups* which is basically an array of lookup keys and the value to use for that lookup -- this is then referenced in a definition like: `__lookup::enable` which would use the lookup with the key "enable".


## Python Changes

- No more paramiko, asyncssh, or ssh2-python -- all transport things happen in libscrapli/C dependencies now.
- TTP support has been removed -- TTP is great, it was just a little silly to retain extra API surface that was basically one line, you can easily handle this yourself!
- Everything but required args are forced to be keyword arguments (via `*`), this makes it easier to move args around without affecting user code.
- There is no longer a separate package for NETCONF, all NETCONF functionality lives in libscrapli and the scrapli package exposes that alongside the CLI functionality.
- Python 3.10+ only! At time of writing 3.10 is already only in security fixes anyway, so this should really not be a huge problem! That said, this should mostly work with only minor tweaks all the way back to 3.7ish if you really needed to make it work (type annotations being the big thing requiring 3.10).
- There is no longer any mixin shenanegins! This historically existed for us to have an async and sync version of everything w/ some common functionality -- now instead the same Cli/Netconf classes support methods in both async and sync flavors like: `get_config_async` and `get_config`.
- scrapli community has been deprecated -- this has some potential issues for a handful of platforms that had some "extra" things (looking at you FortiOS!). Supporting this will ultimately end up needing to be community/individually driven as retaining the type of customization that existed here (and AFAICT *only* here) is not easy to accomplish with the libscrapli backend.
- Python now supports handling NETCONF subscriptions -- this was not previously possible due to how the channel processed data. Please see the relevant example for how to set this up.


## Go Changes

- Rejoice! There is no more timeout options, timeouts are instead now governed by contexts as you would expect in any reasonable go package!
- There is (currently?) no "bring your own" transport option.
- Please see the [go installation section](installation.md#go) for details about getting libscrapli -- libscrapli is required and will be automatically fetched on initial execution, however you can handle this ahead of time if you'd prefer (or are doing things in a container for example).
- There is no more direct support for any kind of NETCONF subscription -- instead, please see the example section for this - there *is* support for fetching subscription/notification messages, you just need to set up the subscription a bit more on your own!
