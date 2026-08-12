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

# shared objects are stored w/ fully qualified (arch/platform/abi) names now so a stale lib can
# no longer be silently packaged into the wrong target's wheel, but we still clean up between
# iterations since the package-data globs match *all* libscrapli objects -- without this each
# successive wheel would also contain all the previous targets' libs
rm scrapli/lib/*.dylib || true
rm scrapli/lib/*.so.* || true

for target in \
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
