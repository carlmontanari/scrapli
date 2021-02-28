# Installation


## Standard Installation

As outlined in the quick start, you should be able to pip install scrapli "normally":

```
pip install scrapli
```


## Installing current master branch

To install from the source repositories master branch:

```
pip install git+https://github.com/carlmontanari/scrapli
```


## Installing current develop branch

To install from the source repositories develop branch:

```
pip install -e git+https://github.com/carlmontanari/scrapli.git@develop#egg=scrapli
```


## Installation from Source

To install from source:

```
git clone https://github.com/carlmontanari/scrapli
cd scrapli
python setup.py install
```


## Optional Extras

scrapli has made an effort to have as few dependencies as possible -- in fact to have ZERO dependencies! The "core" of
 scrapli can run with nothing other than standard library! If for any reason you wish to use paramiko, ssh2-python, 
or asyncssh as a transport, however, you of course need to install those. These "extras" can be installed via pip:

```
pip install scrapli[paramiko]
```

The available optional installation extras options are:

- paramiko
- ssh2
- asyncssh  
- textfsm (textfsm and ntc-templates)
- ttp (ttp template parser)  
- genie (genie/pyats)
- netconf (scrapli_netconf)
- community (scrapli_community)


If you would like to install all optional extras, you can do so with the `full` option:

```
pip install scrapli[full]
``` 


## Supported Platforms

As for platforms to *run* scrapli on -- it has and will be tested on MacOS and Ubuntu regularly and should work on any
 POSIX system. Windows at one point was being tested very minimally via GitHub Actions builds, however this is no
  longer the case as it is just not worth the effort. While scrapli should work on Windows when using the paramiko or
   ssh2-python transport drivers, it is not "officially" supported. It is *strongly* recommended/preferred for folks
    to use WSL/Cygwin instead of Windows.
