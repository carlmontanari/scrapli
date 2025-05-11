#!/bin/sh

set -e

/yang/dummy-actions.py &
/yang/boring-counter.py &
/yang/some-data.py &