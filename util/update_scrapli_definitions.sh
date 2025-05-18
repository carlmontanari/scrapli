#!/bin/bash
set -euo pipefail

TARGET_DEFINITIONS_TAG="${1:-}"

ORIG_DIR=$(pwd)
TMP_DIR=$(mktemp -d)

if [[ "$TARGET_DEFINITIONS_TAG" =~ ^[0-9a-f]{7,40}$ ]]; then
    git clone --depth 1 https://github.com/scrapli/scrapli_definitions.git "$TMP_DIR"
    cd "$TMP_DIR"
    git checkout "$TARGET_DEFINITIONS_TAG"
    cd "$ORIG_DIR"
else
    git clone --depth 1 --branch "$TARGET_DEFINITIONS_TAG" https://github.com/scrapli/scrapli_definitions.git "$TMP_DIR"
fi

echo "cloned scrapli-definitions@$TARGET_DEFINITIONS_TAG into $TMP_DIR"

echo "removing old definitions..."
rm -f scrapli/definitions/*.yaml

echo "updating definitions..."
cp "$TMP_DIR"/definitions/*.yaml scrapli/definitions/

rm -rf "$TMP_DIR"

sed -i.bak -E "s|(__definitions_version__\s*=\s*\")[^\"]+(\".*)|\1${TARGET_DEFINITIONS_TAG#v}\2|g" scrapli/__init__.py
