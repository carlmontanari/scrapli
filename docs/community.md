# Community

## Contributing

Thanks for thinking about contributing, contributions are not expected, but are quite welcome.

Some notes/thoughts on contributing:

- Please do not open issues for "help" topics. Use discussions for this
- If you would like to contribute a feature, know that you will almost certainly need to be working in the zig programming language -- this is how scrapli can support Python and Go in a unified way which is pretty great, but of course this does introduce an extra layer of complexity. I'm happy to help work with you in doing this to some level, but won't be able to help you get going with zig basics
- Please try to help keep the scrapli flavors in sync when/if you contribute! For example, if we add a flag/knob to scrapli (py) we should be adding an equivalent flag to scrapligo -- this ensures that you can always have a consistent experience with scrapli regardless of the language you are using
- Please open a GitHub issue for any potential feature adds/changes to discuss them prior to opening a PR, this way everyone has a chance to chime in and make sure we're all on the same page!
- Please open an issue to discuss any bugs/bug fixes prior to opening a PR. When opening a bug, please try to have done a bit of research to confirm it is indeed a bug, and ideally how it can be reproduced, this saves me an enormous amount of time and energy and makes getting the bug fixed way faster!
- All PRs must pass tests/CI linting -- checkout the Makefile for some shortcuts for linting and testing. Yes, there are a zillion linters, some or many you may not agree with/like, tough cookies, let's try to keep things tidy!


## Thank Yous

Thank you to the following people who have made contributions in some form or fashion to scrapli -- and apologies to the many many others who have helped, thank you all very much!

- [Kevin Landreth](https://github.com/CrackerJackMack) for always being a great sounding board and for helping out a ton in scrapli's infancy
- [Dmitry Figol](https://github.com/dmfigol) for really helpful guidance on how best to build the API/overall structure of things very early on, and continued support/guidance
- [Javin Craig](https://github.com/javincraig) for very early testing help and extra eyes on loads of readme/docs
- [John (IPvZero) McGovern](https://github.com/IPvZero) for loads of testing, encouraging the nornir plugin along, and lots of great discussions
- [Ryan Bradshaw](https://github.com/rbraddev) for early testing and discussions on disabling paging, dealing with interactive inputs, and making the paramiko/ssh2-python transports plugins
- [Eric Tedor](https://github.com/etedor) for some interesting and challenging use cases that helped to improve some of the prompt matching decisions
- [Ron Frederick](https://github.com/ronf) for building the very awesome asyncssh library
- [Brett Canter](https://github.com/wonderbred) for building the very first `scrapli_community` platform! (ruckus_fastiron)
- [Alex Lardschneider](https://github.com/AlexLardschneider) for great conversation, many contributions to `scrapli_community`, and helping to improve various pieces of `scrapli` with great testing and troubleshooting
- [Marion](https://github.com/marionGh) for loads of testing hard to track down issues with the async transports
- [Roman Dodin](https://github.com/hellt) for all the support throughout scrapli's life in all the ways
- [netixx](https://github.com/netixx) for helping unravel some particularly fun decorator timeout shenanigans
- [SimPeccaud](https://github.com/SimPeccaud) for being awesome and helping out here and in other related(ish) endeavors like libscrapli and clabernetes

This list has not been kept up as well as it should, apologies for that! Thank you to everyone else who has contributed in any way to scrapli!
