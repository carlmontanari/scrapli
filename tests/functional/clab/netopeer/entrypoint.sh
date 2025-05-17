#!/bin/sh

set -e

/yang/run-plugins.sh

netopeer2-server -d -t 10 -c MSG