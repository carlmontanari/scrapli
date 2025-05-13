#!/usr/bin/env bash
set -euo pipefail

TARGET_TAG="${1:-}"

LATEST_TAGS=(
    $(curl -s "https://api.github.com/repos/scrapli/libscrapli/tags" \
        | jq -r '.[].name' \
        | sort -Vr \
        | head -n 5)
)

prompt_for_tag() {
  echo "recent tags:"
  select version in "${LATEST_TAGS[@]}"; do
    if [[ -n "$version" ]]; then
      TARGET_TAG="$version"
      break
    else
      echo "try again..."
    fi
  done
}

if [[ -n "$TARGET_TAG" ]]; then
  if [[ ! " ${LATEST_TAGS[*]} " =~ " ${TARGET_TAG} " ]]; then
    echo "provided tag '$TARGET_TAG' is not valid"
    echo
    prompt_for_tag
  fi
else
    prompt_for_tag
fi

sed -i.bak -E "s|(LIBSCRAPLI_VERSION = )(.*)|\1\"${TARGET_TAG#v}\"|g" scrapli/ffi.py

git diff -- scrapli/ffi.py

read -p "looks good? (y/n): " confirm

if [[ "$confirm" == [yY] ]]; then
  rm scrapli/ffi.py.bak
else
  echo "restoring...."
  mv scrapli/ffi.py.bak scrapli/ffi.py
fi
