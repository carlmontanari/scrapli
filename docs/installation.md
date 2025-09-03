# Installation

Installing scrapli varies depending on which flavor of scrapli you are wanting to use! Check out the appropriate section below based on your needs.


## Zig

Using libscrapli in zig is like using any other 0.14.0+ zig library, you can simply `zig fetch` and save it to your `build.zig.zon`:

```
zig fetch --save=libscrapli https://github.com/scrapli/libscrapli/archive/refs/tags/v0.0.1-beta.11.tar.gz
```


## Python

Due to the history of scrapli (py) using calendar versioning, and modern scrapli generally changing to using semantic versioning, there are now actually *two* scrapli projects on PyPI -- `scrapli` and `scrapli2`. Both are the same codebase, with the only difference being the versioning scheme. `scrapli` is still released using calendar versioning. This ensures no change of behavior from the "legacy" scrapli things, and also keeps pip from losing its mind comparing calendar and semantic versions. If you prefer to just use semantic versioning you can install `scrapli2`.

The simplest method of installing scrapli is simply to `pip` install it:

```
pip install scrapli
```

or

```
pip install scrapli2
```

You can install from main as well as follows:

```
pip install git+https://github.com/carlmontanari/scrapli
```

Or a specific commit hash or branch (respectively) like so:

```
pip install git+https://github.com/carlmontanari/scrapli.git@0d1e871
pip install git+https://github.com/carlmontanari/scrapli.git@some-feature#egg=scrapli2
```

*Note*: notice the `egg=scrapli2` part, thats important! Its needed because the pyproject.toml metadata in the repo has `scrapli2` (the semver version).

You can of course also just install from source:

```
git clone https://github.com/carlmontanari/scrapli
cd scrapli
pip install .
```

### Optional Extras

scrapli also has two optional extras -- textfsm/ntc-templates and genie. You can install those like:

```
pip install scrapli[textfsm]
pip install scrapli[genie]
```

Or alternatively the following to do both:

```
pip install scrapli[full]
```


## Go

Installation in a go project begins as you would expect. You can just use normal go toolchain things to include it in your project:

```
go get github.com/scrapli/scrapligo
```

Or at a tag/commit:

```
go get github.com/scrapli/scrapligo@v2.0.0
```

This gets you the source code, however it does *not* install libscrapli for you as there is no "install" step like we have with Python (via setuptools). You have a few options for how you can handle getting libscrapli when using scrapligo:

1. Do nothing.

If you elect to do nothing, the first time you run a program that is doing scrapligo things, libscrapli will be fetched and stored in a cache path. That path can be set via the `LIBSCRAPLI_CACHE_PATH` environment variable, or defaults to `XDG_CACHE_HOME` (if set) or
`$HOME/.cache/scrapli` on linux systems, or `$HOME/Library/Caches/scrapli` on Darwin systems.

libscrapli is fetched via HTTP whenever the libscrapli version (in `constants/versions.go`) of scrapligo is set to a tag. If you are using a development version that is pinned to a commit hash of libscrapli, you will need to have docker available as libscrapli will be fetched and built in a container.

2. Get it yourself:

You will likely want to use this option if you are building a container, don't want to wait for the things out lined in option one above to happen, or are needing to run things somewhere with no access to GitHub.

If you've cloned the scrapligo project and have normal go tools available, you can use the helper program in the build dir to fetch libscrapli:

```
go run build/write_libscrapli_to_cache/main.go
```

Alternatively you can fetch the libscrapli build for your specific platform (found in
[libscrapli releases](https://github.com/scrapli/libscrapli/releases)), or of course you can build libscrapli yourself. Once you've got the compiled shared object, you simply need to place it at the appropriate cache path or set the override path as outlined above.
