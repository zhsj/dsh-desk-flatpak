#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

CACHE_DEST = "assets"

def arch_for_target(target: str) -> list[str]:
    if target.endswith("-x64"):
        return ["x86_64"]
    if target.endswith("-arm64"):
        return ["aarch64"]
    return []


def generate_sources(lock: dict) -> list[dict]:
    sources: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for target_name, t in lock.get("targets", {}).items():
        if not target_name.startswith("linux-"):
            continue
        only_arches = arch_for_target(target_name)

        node_url = (
            f"https://nodejs.org/dist/v{lock['nodeVersion']}/"
            f"node-v{lock['nodeVersion']}-{t['nodeArchive']}"
        )
        key = (node_url, t["nodeSha256"])
        if key not in seen:
            seen.add(key)
            entry: dict[str, object] = {
                "type": "file",
                "url": node_url,
                "sha256": t["nodeSha256"],
                "dest": CACHE_DEST,
                "dest-filename": t["nodeSha256"],
            }
            if only_arches:
                entry["only-arches"] = only_arches
            sources.append(entry)

        python_filename = (
            f"cpython-{lock['pythonVersion']}+{lock['pythonRelease']}-"
            f"{t['pythonTarget']}-install_only_stripped.tar.gz"
        )
        python_url = (
            f"https://github.com/astral-sh/python-build-standalone/releases/download/"
            f"{lock['pythonRelease']}/{python_filename}"
        )
        key = (python_url, t["pythonSha256"])
        if key not in seen:
            seen.add(key)
            entry = {
                "type": "file",
                "url": python_url,
                "sha256": t["pythonSha256"],
                "dest": CACHE_DEST,
                "dest-filename": t["pythonSha256"],
            }
            if only_arches:
                entry["only-arches"] = only_arches
            sources.append(entry)

        for wheel in t.get("wheels", []):
            key = (wheel["url"], wheel["sha256"])
            if key not in seen:
                seen.add(key)
                entry = {
                    "type": "file",
                    "url": wheel["url"],
                    "sha256": wheel["sha256"],
                    "dest": CACHE_DEST,
                    "dest-filename": wheel["sha256"],
                }
                if only_arches:
                    entry["only-arches"] = only_arches
                sources.append(entry)

    for wheel in lock.get("wheels", []):
        key = (wheel["url"], wheel["sha256"])
        if key not in seen:
            seen.add(key)
            sources.append({
                "type": "file",
                "url": wheel["url"],
                "sha256": wheel["sha256"],
                "dest": CACHE_DEST,
                "dest-filename": wheel["sha256"],
            })

    return sources


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--lock-file",
        type=Path,
        default=Path("deepseek-harness/scripts/primary-runtime/lock.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("generated/runtime-sources.json"),
    )
    args = parser.parse_args()

    lock = json.loads(args.lock_file.read_text())

    sources = generate_sources(lock)
    args.output.write_text(json.dumps(sources, indent=2) + "\n")

if __name__ == "__main__":
    main()
