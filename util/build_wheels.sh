#!/bin/bash
set -euo pipefail

# build path if you already have libscrapli somewhere, otherwise tmp dir
created_temp_dir=false
if [[ $# -eq 0 && -z "${LIBSCRAPLI_BUILD_PATH:-}" ]]; then
    LIBSCRAPLI_BUILD_PATH=$(mktemp -d)
    created_temp_dir=true
fi

if [[ "$created_temp_dir" = true ]]; then
    trap 'rm -rf "$LIBSCRAPLI_BUILD_PATH"' EXIT
fi

echo "building libscrapli in $LIBSCRAPLI_BUILD_PATH"

# have to make sure we remove the lib if it exists, then do so at each
# iteration, otherwise we'll end up just putting whatever the first target
# shared object would be in all the wheels
rm scrapli/lib/*.dylib || true
rm scrapli/lib/*.so.* || true

for target in \
    x86_64-macos \
    aarch64-macos \
    x86_64-linux-gnu \
    x86_64-linux-musl \
    aarch64-linux-gnu \
    aarch64-linux-musl; do
    echo "building wheel for $target..."
    LIBSCRAPLI_BUILD_PATH="${LIBSCRAPLI_BUILD_PATH}" \
        LIBSCRAPLI_ZIG_TRIPLE="$target" \
        python -m build --wheel

    rm scrapli/lib/*.dylib || true
    rm scrapli/lib/*.so.* || true
done
