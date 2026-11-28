#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from urllib.error import URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

CLIS = [
    {
        "name": "gh",
        "latest": "https://github.com/cli/cli/releases/latest",
        "base": "https://github.com/cli/cli/releases/download/",
        "url": "{base}{tag}/gh_{version}_linux_amd64.tar.gz",
        "checksums": "{base}{tag}/gh_{version}_checksums.txt",
        "asset": "gh_{version}_linux_amd64.tar.gz",
    },
    {
        "name": "glab",
        "latest": "https://gitlab.com/gitlab-org/cli/-/releases/permalink/latest",
        "base": "https://gitlab.com/gitlab-org/cli/-/releases/",
        "url": "{base}{tag}/downloads/glab_{version}_linux_amd64.tar.gz",
        "checksums": "{base}{tag}/downloads/checksums.txt",
        "asset": "glab_{version}_linux_amd64.tar.gz",
    },
]


def run_git(path, args):
    r = subprocess.run(["git", "-C", path] + args, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"git {' '.join(args)}: {r.stderr}", file=sys.stderr)
        sys.exit(1)
    return r.stdout.strip()


def fetch(url):
    req = Request(url, headers={"User-Agent": "dsh-desk-flatpak"})
    with urlopen(req, timeout=60) as r:
        return r.geturl(), r.read().decode()


def update_clis(manifest_path):
    with open(manifest_path) as f:
        text = f.read()
    changed = False
    for cli in CLIS:
        name = cli["name"]
        try:
            tag = fetch(cli["latest"])[0].rstrip("/").rsplit("/", 1)[-1]
            fields = {"base": cli["base"], "tag": tag, "version": tag.removeprefix("v")}
            if f"{cli['base']}{tag}/" in text:
                print(f"{name}: already up to date ({tag})")
                continue
            sums = fetch(cli["checksums"].format(**fields))[1]
        except URLError as e:
            sys.exit(f"{name}: {e}")

        asset = cli["asset"].format(**fields)
        sha = next((p[0] for p in map(str.split, sums.splitlines()) if p[-1:] == [asset]), None)
        if sha is None:
            sys.exit(f"{name}: no sha256 for {asset} in checksums")

        old = re.search(rf"url:\s*{re.escape(cli['base'])}([^/\s]+)/", text)
        tail = cli["url"].format(**fields).removeprefix(cli["base"])
        text, n = re.subn(
            rf"(url:\s*{re.escape(cli['base'])})\S+(\n\s+sha256:\s*)\S+",
            lambda m: f"{m.group(1)}{tail}{m.group(2)}{sha}",
            text,
            count=1,
        )
        if n == 0:
            sys.exit(f"{name}: could not find url/sha256 in manifest")
        changed = True
        print(f"{name}: {old.group(1) if old else '?'} -> {tag}")

    if changed:
        with open(manifest_path, "w") as f:
            f.write(text)


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--source-dir",
        default="deepseek-harness",
    )
    p.add_argument(
        "--manifest",
        default="com.deepseek.harness.yml",
    )
    p.add_argument(
        "--metainfo",
        default="com.deepseek.harness.metainfo.xml",
    )
    args = p.parse_args()

    tag = run_git(
        args.source_dir, ["tag", "--sort=-creatordate", "dsh-v*", "--merged"]
    ).split("\n")[0]
    commit = run_git(args.source_dir, ["rev-parse", tag])
    date = datetime.strptime(
        run_git(args.source_dir, ["log", "-1", "--format=%ci", tag])[:10], "%Y-%m-%d"
    ).strftime("%Y-%m-%d")
    version = tag.removeprefix("dsh-v")
    print(f"tag={tag} commit={commit} version={version} date={date}")

    with open(args.manifest) as f:
        text = f.read()
    text, n = re.subn(
        r"(url:\s*https://github\.com/deepseek-ai/deepseek-harness\.git\n\s+tag:\s*)\S+(\n\s+commit:\s*)\S+",
        rf"\g<1>{tag}\g<2>{commit}",
        text,
        count=1,
    )
    if n == 0:
        sys.exit("Could not find tag/commit for deepseek-harness source in manifest")
    with open(args.manifest, "w") as f:
        f.write(text)

    tree = ET.parse(args.metainfo)
    root = tree.getroot()
    releases = root.find("releases")
    if releases is None:
        releases = ET.SubElement(root, "releases")
    existing = {r.get("version") for r in releases.findall("release")}
    if version not in existing:
        release_el = ET.Element("release", version=version, date=date)
        releases.insert(0, release_el)
        ET.indent(tree, space="  ")
        tree.write(args.metainfo, encoding="UTF-8", xml_declaration=True)
        with open(args.metainfo, "a") as f:
            f.write("\n")
        print(f"Added release {version}")
    else:
        print(f"Release {version} already exists")
    update_clis(args.manifest)
    print("Done.")


if __name__ == "__main__":
    main()
