# AGENTS.md — dsh-desk-flatpak

给 coding agent 的项目约定文档。修改本仓库前请先读完，尤其是「不可随意改动」一节。

## 项目概述

为 [deepseek-harness](https://github.com/deepseek-ai/deepseek-harness) 官方桌面应用做 Flatpak 打包，并叠加 Linux/Flatpak 适配补丁。

- App ID：`com.deepseek.harness`
- 上游引用方式：manifest 里以 `git` source 固定到 `dsh-v*` tag + commit
- 分发：OCI registry（`ghcr.io`）+ GitHub Pages 仓库站点（`https://zhsj.me/dsh-desk-flatpak`）

`com.deepseek.harness.yml` 是唯一构建入口，具体配置（runtime 版本、finish-args、模块结构、CI 流程）以其实际内容为准，本文档不重复。

## 构建与验证

改完 manifest 或补丁后**必须实际构建一次**（上游产物路径、runtime 准备脚本、补丁都可能失效）：

```bash
docker run --rm -it -v "$(pwd)":/workspace -w /workspace --privileged \
  ghcr.io/flathub-infra/flatpak-github-actions:freedesktop-26.08 \
  dbus-run-session -- flatpak-builder --repo=repo-dir --disable-rofiles-fuse \
  --force-clean --install-deps-from=flathub build-dir com.deepseek.harness.yml
```

冒烟：`flatpak run com.deepseek.harness`

## 版本升级流程

```bash
# 1. 准备/更新本地上游克隆（deepseek-harness/，已被 .gitignore 忽略）
# 2. 更新 manifest + metainfo
python3 update_release.py
# 3. 构建验证；补丁可能需要 rebase
```

`update_release.py` 行为：

- 取 `--merged` 的最新 `dsh-v*` tag（按 creatordate 排序）及其 commit、日期
- 正则替换 manifest 中 `deepseek-harness.git` source 的 `tag:` 与 `commit:`
- 若 metainfo 的 `<releases>` 中没有该版本，则插入到最前面（版本名为去掉 `dsh-v` 前缀的 tag）
- 找不到 manifest 中的 tag/commit 模式会直接报错退出

升级后必须实际构建一次：`package:dir` 产物路径、runtime 准备脚本、补丁都可能随上游变化。

## 补丁管理

补丁基于本地 `deepseek-harness/` 仓库的 `linux-flatpak` 分支调试并生成：

1. 在 `deepseek-harness/` 创建/切换到 `linux-flatpak` 分支
2. 在该分支上做所有 Linux/Flatpak 适配修改，每个独立功能一个 commit
3. 合并成一个补丁：
   ```bash
   git format-patch --stdout master..linux-flatpak > ../linux-desktop.patch
   ```
4. manifest 中通过 `sources[].type: patch` 引用，配合 `options: [-d, deepseek-harness]` 指定目标目录

## Commit 规范

Commit message 附带 `Assisted-by: AGENT_NAME:MODEL_VERSION` trailer。
