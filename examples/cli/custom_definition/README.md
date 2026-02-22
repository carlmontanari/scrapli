# Custom Definition

Scrapli "platform definitions" define how to interact with a given device type -- i.e. the shape of
the prompt to look for, and the available "modes" of the device. Many device definitions are
included in scrapli by packaging a target version/hash of the
[scrapli_definitions](https://github.com/scrapli/scrapli_definitions) definition files at release
time, however, if your platform is not represented in the defintions, or is not packaged yet due to
a new release not being generated, or whatever other reason, you can simply point scrapli to your
defintiion YAML file to bring that functionality directly to scrapli.

Note that the allowable schema can be gleaned from either the core libscrapli types
[here](https://github.com/scrapli/libscrapli/blob/main/src/cli-platform.zig), or the slightly easier  to consume pydantic schema in the definitions test suite
[here](https://github.com/scrapli/scrapli_definitions/blob/main/tests/schema.py).
