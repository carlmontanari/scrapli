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

echo "removing old definition options..."
find scrapli/definition_options -type f -name "*.py" ! -name "__init__.py" -delete

echo "updating definition options..."
cp "$TMP_DIR"/options/*.py scrapli/definition_options/

rm -rf "$TMP_DIR"

sed -i.bak -E "s|(__definitions_version__ = )(.*)|\1\"${TARGET_DEFINITIONS_TAG#v}\"|g" scrapli/__init__.py
