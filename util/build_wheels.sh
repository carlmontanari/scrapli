#!/bin/bash
set -euo pipefail

for target in \
    x86_64-macos \
    aarch64-macos \
    x86_64-linux-gnu \
    x86_64-linux-musl \
    aarch64-linux-gnu \
    aarch64-linux-musl; do
    LIBSCRAPLI_BUILD_PATH=./tmp LIBSCRAPLI_ZIG_TRIPLE="$target" python -m build --wheel
done
