#!/bin/bash
set -euo pipefail

LIBSCRAPLI_TAG="${1:-}"

if [[ -z "$LIBSCRAPLI_TAG" ]]; then
    echo "error: libscrapli tag must be set"
    exit 1
fi

LIBSCRAPLI_TAG="${LIBSCRAPLI_TAG#v}"

sed -i.bak -E "s|(LIBSCRAPLI_VERSION = )(.*)|\1\"${LIBSCRAPLI_TAG}\"|g" scrapli/ffi.py
sed -i.bak -E "s|(LIBSCRAPLI_VERSION = )(.*)|\1\"${LIBSCRAPLI_TAG}\"|g" setup.py
