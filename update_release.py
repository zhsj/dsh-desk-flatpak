#!/usr/bin/env python3
import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from xml.etree import ElementTree as ET


def run_git(path, args):
    r = subprocess.run(["git", "-C", path] + args, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"git {' '.join(args)}: {r.stderr}", file=sys.stderr)
        sys.exit(1)
    return r.stdout.strip()


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
    print("Done.")


if __name__ == "__main__":
    main()
