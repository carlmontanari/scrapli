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

Integration tests (coming soon!) test scrapli against auto generated ssh server that looks/feels like real network 
devices.

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

Executing the functional tests is a bit more complicated! First, thank you to Kristian Larsson for his great tool
 [vrnetlab](https://github.com/plajjan/vrnetlab)! All functional tests are built on this awesome platform that allows
  for easy creation of containerized network devices.

Basic functional tests exist for all "core" platform types (IOSXE, NXOS, IOSXR, EOS, Junos) as well as basic testing
 for Linux. Vrnetlab currently only supports the older emulation style NX-OS devices, and *not* the newer VM image
  n9kv. I have made some very minor tweaks to vrnetlab locally in order to get the n9kv image running. I also have
   made some changes to enable scp-server for IOSXE/NXOS devices to allow for config replaces with NAPALM right out
    of the box. You can get these tweaks in my fork of vrnetlab. Getting going with vrnetlab is fairly
     straightforward -- simply follow Kristian's great readme docs.
     
For the Arista EOS image -- prior to creating the container you should boot the device and enter the `zerotouch
 disable` command. This allows for the config to actually be saved and prevents the interfaces from cycling through
  interface types in the container (I'm not clear why it does that but executing this command before building the
   container "fixes" this!). An example qemu command to boot up the EOS device is:
         
```
qemu-system-x86_64 -enable-kvm -display none -machine pc -monitor tcp:0.0.0.0:4999,server,nowait -m 4096 -serial telnet:0.0.0.0:5999,server,nowait -drive if=ide,file=vEOS-lab-4.22.1F.vmdk -device pci-bridge,chassis_nr=1,id=pci.1 -device e1000,netdev=p00,mac=52:54:00:54:e9:00 -netdev user,id=p00,net=10.0.0.0/24,tftp=/tftpboot,hostfwd=tcp::2022-10.0.0.15:22,hostfwd=tcp::2023-10.0.0.15:23,hostfwd=udp::2161-10.0.0.15:161,hostfwd=tcp::2830-10.0.0.15:830,hostfwd=tcp::2080-10.0.0.15:80,hostfwd=tcp::2443-10.0.0.15:443
```

Once booted, connect to the device (telnet to container IP on port 5999 if using above command), issue the command
 `zerotouch disable`, save the config and then you can shut it down, and make the container.

The docker-compose file here will be looking for the container images matching this pattern, so this is an important
 bit! The container image names should be:

```
scrapli-cisco-iosxe
scrapli-cisco-nxos
scrapli-cisco-iosxr
scrapli-arista-eos
scrapli-juniper-junos
```

You can tag the image names on creation (following the vrnetlab readme docs), or create a new tag once the image is built:

```
docker tag [TAG OF IMAGE CREATED] scrapli-[VENDOR]-[OS]
```

*NOTE* If you are going to test scrapli, use [my fork of vrnetlab](https://github.com/carlmontanari/vrnetlab) -- I've
 enabled telnet, set ports, taken care of setting things up so that NAPALM can config replace, etc.


### Functional Tests

Once you have created the images, you can start all of the containers with a make command:

```
make start_dev_env
```

Conversely, you can terminate the containers:

```
make stop_dev_env
```

To start a specific platform container:

```
make start_dev_env_iosxe
```

Substitute "iosxe" for the platform type you want to start.

Most of the containers don't take too long to fire up, maybe a few minutes (running on my old macmini with Ubuntu, so
 not exactly a powerhouse!). That said, the IOS-XR device takes about 15 minutes to go to "healthy" status. Once
  booted up you can connect to their console or via SSH:

| Device        | Local IP      |
| --------------|---------------|
| iosxe         | 172.18.0.11   |
| nxos          | 172.18.0.12   |
| iosxr         | 172.18.0.13   |
| eos           | 172.18.0.14   |
| junos         | 172.18.0.15   |
| linux         | 172.18.0.20   |

The console port for all devices is 5000, so to connect to the console of the iosxe device you can simply telnet to
 that port locally:

```
telnet 172.18.0.11 5000
```

Credentials for all devices use the default vrnetlab credentials:

Username: `vrnetlab`

Password: `VR-netlab9`

You should also run the `prepare_devices` script in the functional tests, or use the Make commands to do so for you
. This script will deploy the base config needed for testing. The make commands for this step follow the same pattern
 as the others:

- `prepare_dev_env` will push the base config to all devices
- `prepare_dev_env_XYZ` where XYZ == "iosxe", "nxos", etc. will push the base config for the specified device.

Once the container(s) are ready, you can use the make commands to execute tests as needed:

- `test` will execute all currently implemented functional tests as well as the unit tests
- `test_functional` will execute all currently implemented functional tests
- `test_iosxe` will execute all unit tests and iosxe functional tests
- `test_nxos` will execute all unit tests and nxos functional tests
- `test_iosxr` will execute all unit tests and iosxr functional tests
- `test_eos` will execute all unit tests and eos functional tests
- `test_junos` will execute all unit tests and junos functional tests
- `test_linux` will execute all unit tests and basic linux functional tests (this is really intended to test the base
 `Scrape` driver instead of the network drivers)


### Other Functional Test Info

IOSXE is the only platform that is testing SSH key based authentication at the moment. The key is pushed via NAPALM in
 the setup phase. This was mostly done out of laziness, and in the future the other platforms may be tested with key
  based auth as well, but for now IOSXE is representative enough to provide some faith that key based auth works! 
