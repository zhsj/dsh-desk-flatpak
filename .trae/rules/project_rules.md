# Project Rules: dsh-desk-flatpak

## 项目概述

Flatpak 打包 [deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) 桌面程序，参考 [AUR deepseek-harness-desktop](https://aur.archlinux.org/deepseek-harness-desktop.git) 提供的 patch。

## 关键文件

| 文件 | 用途 |
|------|------|
| `com.deepseek.harness.yml` | Flatpak manifest 主配置 |
| `linux-desktop.patch` | 适配 Linux/Flatpak 平台的合并补丁（git format-patch --stdout 生成） |
| `deepseek-harness.sh` | zypak wrapper 启动脚本 |
| `com.deepseek.harness.desktop` | 桌面入口文件 |
| `com.deepseek.harness.metainfo.xml` | AppStream 元数据 |
| `.github/workflows/flatpak.yml` | GitHub Actions 构建/发布工作流 |

## Flatpak 构建

### Runtime 配置

- **Runtime**: `org.freedesktop.Platform` `25.08`
- **SDK**: `org.freedesktop.Sdk` `25.08`
- **SDK Extension**: `org.freedesktop.Sdk.Extension.node24`
- **BaseApp**: `org.electronjs.Electron2.BaseApp` `25.08`

### 构建命令

```bash
flatpak-builder --user --install --force-clean build-dir com.deepseek.harness.yml
```

### 运行命令

```bash
flatpak run com.deepseek.harness
```

## GitHub Actions

工作流 `.github/workflows/flatpak.yml`：push 到 `master`、PR、手动触发时构建 Flatpak bundle，产物作为 workflow artifact 上传；不发布 GitHub Release。

- 容器镜像：`ghcr.io/flathub-infra/flatpak-github-actions:freedesktop-25.08`，预装 `org.freedesktop.Platform//25.08` 和 `org.freedesktop.Sdk//25.08`
- 其余依赖（`sdk-extensions` 的 node24、`base` 的 Electron2.BaseApp）由 action 通过 `flatpak-builder --install-deps-from=flathub` 自动安装（input `repository-name`，默认 `flathub`），无需手动 `flatpak install`
- 使用 `flatpak/flatpak-github-actions/flatpak-builder@v6`，`with` 只写非默认值（`manifest-path`/`bundle`/`artifact-name`/`build-dir`/`repo-dir`/`verbose`），`arch`、`state-dir` 等默认值不写
- 目录：`build-dir` / `repo-dir`，`.flatpak-builder` 用 action 默认值（`state-dir`，同时是 actions/cache 的缓存目录）
- 产物：artifact 名为 `com.deepseek.harness-x86_64.flatpak`，bundle 文件名为 `com.deepseek.harness.flatpak`
- 只构建 x86_64：manifest 里 `DSH_DESKTOP_TARGET_ARCH: x64` 是常量，aarch64 会产出错误架构的产物

## 补丁管理

补丁基于本地 `deepseek-harness/` 仓库的 `linux-flatpak` 分支调试并生成：

1. 在 `deepseek-harness/` 目录创建/切换到 `linux-flatpak` 分支
2. 在该分支上应用所有 Linux/Flatpak 适配修改（每个独立功能一个 commit）
3. 使用 `git format-patch --stdout` 将相对于 `master` 的修改合并为一个补丁文件：`git format-patch --stdout master..linux-flatpak > ../linux-desktop.patch`
4. 补丁在 manifest 的 `sources.patch.paths` 中引用，`-d deepseek-harness` 指定目标目录

## 依赖源

- 不使用镜像或代理：pnpm/npm 走官方默认源 `https://registry.npmjs.org/`，Electron 二进制从 GitHub releases 下载
- manifest 中不设置 `NPM_CONFIG_REGISTRY`、`DSH_DESKTOP_NPM_REGISTRY`、`ELECTRON_MIRROR`
- `apps/desktop/scripts/desktop-release-environment.mjs` 的 `resolveNpmRegistry` 在 `DSH_DESKTOP_NPM_REGISTRY` 未设置时回退到 `DEFAULT_NPM_REGISTRY`（`https://registry.npmjs.org/`）
- `pnpm-lock.yaml` 中不含任何 registry 地址，`pnpm install --frozen-lockfile` 可直接使用

## 应用运行时

### Zypak Wrapper

Electron 应用在 Flatpak 中必须通过 `zypak-wrapper` 运行：

```sh
#!/bin/sh
exec zypak-wrapper /app/main/deepseek-harness "$@"
```

### 应用安装路径

- 构建产物 `linux-unpacked` 的内容安装在 `/app/main/` 目录
- 启动脚本安装在 `/app/bin/deepseek-harness`

### 配置与数据路径

- `DSH_HOME=$XDG_DATA_HOME/dsh`（写入 `finish-args` 的 `--env`）
- 确保配置文件持久化在 Flatpak 沙箱内

### 权限（finish-args）

- `--share=ipc`
- `--socket=wayland`
- `--device=dri`
- `--socket=pulseaudio`
- `--share=network`
- 不包含 `--socket=x11`（Wayland only）
- 不包含 `--filesystem=home`

## 图标生成

Flatpak SDK 中**没有** ImageMagick 的 `convert` 命令，使用 `ffmpeg` 替代：

```bash
for size in 512 256 128 64 48; do
  ffmpeg -y -loglevel error -i /app/main/resources/icon.png \
    -vf "scale=${size}:${size}" \
    "/app/share/icons/hicolor/${size}x${size}/apps/com.deepseek.harness.png"
done
```

图标源文件来自 `/app/main/resources/icon.png`（electron-builder 打包时复制）。

## PNPM 安装

在 Flatpak 构建中，pnpm 安装在当前构建目录（`/run/build/dsh-desktop/node_modules/.bin`），通过 `build-options.append-path` 加入 PATH：

```yaml
build-options:
  append-path: /usr/lib/sdk/node24/bin:/run/build/dsh-desktop/node_modules/.bin
```

安装命令：`npm install pnpm@11.7.0`

## 构建缓存

- `ELECTRON_BUILDER_CACHE: /run/build/dsh-desktop/.electron-builder-cache`
- `ELECTRON_CACHE: /run/build/dsh-desktop/.electron-cache`
- pnpm store 自动缓存在 `.pnpm-store/` 目录
- 共享下载缓存在 `deepseek-harness/apps/desktop/.desktop-build/downloads`

## 构建顺序

1. `npm install pnpm@11.7.0`
2. `cd deepseek-harness`
3. `pnpm install --frozen-lockfile`
4. `pnpm --filter @deepseek-ai/dsh-desktop run package:dir`
5. 复制 `linux-unpacked` 到 `/app/main/`

`package:dir` 不带目标参数，按构建主机解析出 `linux-x64`（补丁已注册该目标），内部会执行 `prepare:runtime` 和 `prepare:primary-runtime` 脚本。

## Commit 规范

Commit message 需要加上 `Assisted-by: AGENT_NAME:MODEL_VERSION` 格式的信息。

## .gitignore

```
deepseek-harness/
/build-dir/
/repo-dir/
/.flatpak-builder/
/flatpak_app/
/repo/
*.flatpak
```

## 常用调试方法

由于无法从 terminal 读取命令输出结果，必须通过在当前项目的 `.git/agents` 目录创建临时文件的方式，将命令输出重定向到临时文件并读取结果。
