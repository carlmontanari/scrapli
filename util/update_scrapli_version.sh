#!/bin/bash
set -euo pipefail

SCRAPLI_VERSION="${1:-}"
SCRAPLI_CALENDAR_VERSION=$(date +%-Y.%-m.%-d)

if [[ -z "$SCRAPLI_VERSION" ]]; then
    echo "error: scrapli version must be set"
    exit 1
fi

sed -i.bak -E "s|(__version__ = )(.*)|\1\"${SCRAPLI_VERSION}\"|g" scrapli/__init__.py
sed -i.bak -E "s|(__calendar_version__ = )(.*)|\1\"${SCRAPLI_CALENDAR_VERSION}\"|g" scrapli/__init__.py
