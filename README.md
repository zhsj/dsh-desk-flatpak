# dsh-desk-flatpak

Flatpak packaging of the official [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)
desktop app, with Linux/Flatpak patches applied.

App ID: `com.deepseek.harness`

## Build

```bash
docker run \
  -e https_proxy=http://172.17.0.1:1081 \
  --rm -it \
  -v "$(pwd)":/workspace \
  -w /workspace \
  --privileged \
  ghcr.io/flathub-infra/flatpak-github-actions:freedesktop-25.08 \
  dbus-run-session -- flatpak-builder \
    --repo=repo-dir \
    --disable-rofiles-fuse \
    --force-clean \
    --install-deps-from=flathub \
    build-dir com.deepseek.harness.yml
```

## Install

```bash
flatpak install --user ./repo-dir com.deepseek.harness --reinstall
```

## Run

```bash
flatpak run com.deepseek.harness
```
