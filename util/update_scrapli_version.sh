#!/bin/bash
set -euo pipefail

SCRAPLI_VERSION="${1:-}"

if [[ -z "$SCRAPLI_VERSION" ]]; then
    echo "error: scrapli version must be set"
    exit 1
fi

sed -i.bak -E "s|(__version__\s*=\s*\")[^\"]+(\".*)|\1${SCRAPLI_VERSION}\2|g" scrapli/__init__.py
