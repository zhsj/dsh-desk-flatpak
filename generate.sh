#!/bin/bash
set -ex
mkdir -p generated
${FLATPAK_NODE_GENERATOR:-flatpak-node-generator} pnpm ./deepseek-harness/pnpm-lock.yaml \
  --pnpm-store-version v11 --output ./generated/node-sources.json
./generate-runtime-sources.py
