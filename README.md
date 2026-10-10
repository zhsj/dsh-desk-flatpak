# dsh-desk-flatpak

Flatpak packaging of the official [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)
desktop app, with Linux/Flatpak patches applied.

App ID: `com.deepseek.harness`

## Install

```bash
flatpak remote-add --if-not-exists --user --no-gpg-verify \
  dsh oci+https://zhsj.me/dsh-desk-flatpak
flatpak install --user dsh com.deepseek.harness
flatpak run com.deepseek.harness
```

## Build

```bash
docker run \
  --rm -it \
  -v "$(pwd)":/workspace \
  -w /workspace \
  --privileged \
  ghcr.io/flathub-infra/flatpak-github-actions:freedesktop-26.08 \
  dbus-run-session -- flatpak-builder \
    --repo=repo-dir \
    --disable-rofiles-fuse \
    --force-clean \
    --install-deps-from=flathub \
    build-dir com.deepseek.harness.yml
```
