#!/bin/bash
set -ex
shopt -s nullglob

export DSH_HOME="${XDG_DATA_HOME}/dsh"

PYTHON_SITEDIR=$(python3 <<EOFPYTHON
import os
import site
print(os.path.relpath(site.getusersitepackages(), site.getuserbase()))
EOFPYTHON
)

for tool_dir in /app/tools/*; do
  if [[ -d "$tool_dir/bin" ]]; then
    export PATH="${PATH:+$PATH:}$tool_dir/bin"
  fi

  pydir="$tool_dir/$PYTHON_SITEDIR"
  if [[ -d "$pydir" ]]; then
    export PYTHONPATH="${PYTHONPATH:+$PYTHONPATH:}$pydir"
  fi
done

# For @deepseek-ai/libreoffice-kit
HOST_FONTS="${XDG_DATA_HOME}/fonts/.host-fonts"
rm -rf "$HOST_FONTS" && mkdir -p "$HOST_FONTS"
for dir in /run/host/fonts /run/host/local-fonts /run/host/user-fonts; do
  if [[ -d "$dir" ]]; then
    ln -sfn "$dir" "$HOST_FONTS/$(echo "$dir" | tr '/' '_')"
  fi
done

exec zypak-wrapper /app/main/deepseek-harness "$@"
