#!/bin/sh
export DSH_HOME="${XDG_DATA_HOME}/dsh"

# For @deepseek-ai/libreoffice-kit
HOST_FONTS="${XDG_DATA_HOME}/fonts/.host-fonts"
rm -rf "$HOST_FONTS" && mkdir -p "$HOST_FONTS"
for dir in /run/host/fonts /run/host/local-fonts /run/host/user-fonts; do
  [ -d "$dir" ] && ln -sfn "$dir" "$HOST_FONTS/$(echo "$dir" | tr '/' '_')"
done

exec zypak-wrapper /app/main/deepseek-harness "$@"
