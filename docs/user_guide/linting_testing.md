# Linting and Testing


## Linting

This project uses [black](https://github.com/psf/black) for auto-formatting. In addition to black, nox will execute
 [pylama](https://github.com/klen/pylama), and [pydocstyle](https://github.com/PyCQA/pydocstyle) for linting purposes
 . Nox will also run  [mypy](https://github.com/python/mypy), with strict type checking. Docstring linting is
  handled by [darglint](https://github.com/terrencepreilly/darglint) which has been quite handy!

All commits to this repository will trigger a GitHub action which runs nox, but of course its nicer to just run that
 before making a commit to ensure that it will pass all tests!


### Typing

As stated, this project is 100% type checked and will remain that way. The value this adds for IDE auto-completion
 and just general sanity checking/forcing writing of more type-check-able code is worth the small overhead in effort.


## Testing

Testing is broken into three main categories -- unit, integration, and functional.


Unit is what you would expect -- unit testing the code. 

Integration tests run scrapli against auto generated ssh server that looks/feels like real network devices.

Functional testing connects to virtual devices in order to more accurately test the code. 

Unit tests cover quite a bit of the code base due to lots of patching low level things to ensure code paths go where 
they should go. This gives a pretty high level of confidence that at least object instantiation and channel 
read/writes will generally work! 

Functional tests against virtual devices provide a much higher guarantee of things working as they should, and are 
reproducible by end users to boot!


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

In order to try to be as consistent as possible when running functional testing, we rely on the very awesome 
[containerlab](https://github.com/srl-labs/containerlab) project. Containerlab allows us to have a reliable and 
consistent testing environment and spin it up easily on any linux host (with nested virtualization capabilities).

You can see the containerlab topology file in the `.clab` directory at the root of scrapli. The topology file in 
this directory outlines the container images that containerlab requires in order to spin up the topology. 
Unfortunately, networking vendors suck at giving us free and easy access to container images for testing (notable 
exception of Nokia and SR-Linux, so shout out to them!), so you are going to need to bring your own images to use.

For the Arista EOS platform, you can simply create an account on the Arista website and download the cEOS container 
image and import it into docker. The other platforms all require you to obtain a Qcow2 disk image of the platform, 
and to use the [boxen](https://github.com/carlmontanari/boxen) project to convert the disk image into a container 
image that containerlab can launch. The containerlab topology file indicates the version of the platforms the 
testing suite expects -- other versions may be fine, but try to stick to the versions here if you can so tests run 
exactly as expected! Once you have the Qcow files in hand, you can use boxen to build the container image -- please 
check out the boxen docs for how to do this.

If you elect to run tests with boxen *only* (in "local" mode -- not described here, but should be straight forward 
enough) and *not* use containerlab - set the `SCRAPLI_HOST_FWD` environment variable to some non-empty string; this 
will force scrapli to connect to localhost on the ports described below rather than the clab specified (bridged) IP 
addresses:

| Device        | Local Port |
| --------------|------------|
| iosxe         | 21022      |
| iosxr         | 22022      |
| nxos          | 23022      |
| eos           | 24022      |
| junos         | 25022      |


### Deploying/Destroying Containerlab Test Environment

Once you have created the images, you can start containerlab with a make command:

```
make deploy_clab
```

Conversely, you can terminate the containers:

```
make destroy_clab
```


### Ensuring Base Test Configs

To ensure that the base test configs are enforced, run the `prepare_dev_env` make directive, this uses scrapli-cfg 
to load and replace the configurations running on these devices. This will do things like ensure telnet is enabled 
(which is not the case by default for most platforms in clab/boxen), etc..


### Running Functional Tests

To run functional tests you can simply use the make directive:

`make test_functional`

If you are adding tests and/or need to "regenerate" the expected output, you can use the `--update` flag like:

`python -m pytest tests/functional --update`

This flag causes the test suite to capture the output and write it into the expected directory. This expected output 
is then compared to the "real" output we get from the device during subsequent tests.


### Other Functional Test Info

IOSXE is the only platform that is testing SSH key based authentication at the moment. The key is pushed via NAPALM in
 the setup phase. This was mostly done out of laziness, and in the future the other platforms may be tested with key
  based auth as well, but for now IOSXE is representative enough to provide some faith that key based auth works! 
