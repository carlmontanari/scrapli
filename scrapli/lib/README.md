scrapli.lib
===========

This package holds the libscrapli shared objects for your platform. There is nothing in here in
version control, but it will be populated for wheels, or after an sdist installation. The ffi loader 
will (if the override path is not set) load the libscrapli shared object from here. If you are
cloning scrapli for development or just wanting to use directly from source, you can run
`pip install .` or `pip install -e .` -- this will build she shared object for your platform and
dump it here.