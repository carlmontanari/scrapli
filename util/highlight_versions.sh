#!/bin/bash
set -euo pipefail

# lil helper to highlight all the places there are versions of things that may need to be updated
# during release or just maintenance stuff. ignores action versions (dependabots problem) and the
# actual requirements files
PURPLE=$(printf '\033[1;35m')
CYAN=$(printf '\033[1;36m')
NC=$(printf '\033[0m')

PATTERN_SEMVER='[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?'
PATTERN_CALVER='\d{4}\.\d{1,2}\.\d{1,2}'
PATTERN_PYTHON='3\.\d+'
PATTERN_PYVER='py[0-9]+'
PATTERN_HASH='[a-f0-9]{7,}'

PATTERN_VERSIONS="${PATTERN_SEMVER}|${PATTERN_CALVER}|${PATTERN_PYTHON}|${PATTERN_PYVER}|${PATTERN_HASH}"

highlight_version() {
    echo -e "\n${CYAN}=============== $1 :: $3${NC}"
    grep -E "$2" "$1" --color=never | grep -E "${PATTERN_VERSIONS}"
}

# file :: re to match the line :: nice name to print
locations=(
    "pyproject.toml                 ^requires.*ziglang              ziglang"
    "pyproject.toml                 ^\\s*python_version\\s=         mypy python"
    "pyproject.toml                 ^\\s*requires-python\\s=        minumum python"
    "pyproject.toml                 ^\\s*target-version\\s=         black target"
    "scrapli/ffi.py                 ^LIBSCRAPLI_VERSION\\s=         libscrapli"
    "scrapli/__init__.py            ^__version__\\s=                scrapli"
    "scrapli/__init__.py            ^__calendar_version__\\s=       calendar scrapli"
    "scrapli/__init__.py            ^__definitions_version__\\s=    definitions"
    ".github/vars.env               PYTHON_VERSION=                 ci primary python"
    ".github/workflows/test.yaml    ^\s+version:\\s                 ci unit test pythons"
    "Makefile                       ghcr.io/scrapli/                local/ci clab setup"
)

for entry in "${locations[@]}"; do
    read -r file pattern label <<<"$entry"
    highlight_version "$file" "$pattern" "$label"
done
