#!/usr/bin/env python3
"""Release guard. Every Screenly/edge-apps-actions ref in the reusable
workflows, examples and README must be one exact vYY.M.PATCH version. On a tag
push it must equal the tag; otherwise, if that version is already released,
the shipped code must not have changed since (the pins weren't bumped).
Run from the repo root."""

import os
import re
import subprocess
import sys
from pathlib import Path

PINNED = [
    ".github/workflows/checks.yml",
    ".github/workflows/initialize.yml",
    ".github/workflows/update.yml",
    "examples",
    "README.md",
]
SHIPPED = [
    "checks",
    "initialize",
    "update",
    "scripts",
    ".github/workflows/checks.yml",
    ".github/workflows/initialize.yml",
    ".github/workflows/update.yml",
]
# Take each ref whole, so @main or @v26.10.2-rc.1 can't hide behind a match.
REF_RE = re.compile(r"Screenly/edge-apps-actions/[^@\s]+@([^\s\"'`)>]+)")
VERSION_RE = re.compile(r"v\d+\.\d+\.\d+")


def pinned_files():
    for entry in map(Path, PINNED):
        if entry.is_dir():
            yield from sorted(p for p in entry.rglob("*") if p.is_file())
        elif entry.is_file():
            yield entry


def find_refs():
    refs = []
    for path in pinned_files():
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            refs += [(path, number, m.group(1)) for m in REF_RE.finditer(line)]
    return refs


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, text=True)


def main():
    refs = find_refs()
    if not refs:
        print("::error::Found no Screenly/edge-apps-actions refs in the reusable workflows, examples or README.")
        return 1

    versions = sorted({version for _, _, version in refs})
    if len(versions) != 1 or not VERSION_RE.fullmatch(versions[0]):
        print(
            "::error::Expected every Screenly/edge-apps-actions ref to be one exact "
            f"vYY.M.PATCH version, found: {' '.join(versions)}"
        )
        for path, number, version in refs:
            print(f"{path}:{number}: @{version}")
        return 1
    pin = versions[0]
    print(f"All pins use {pin}")

    ref = os.environ.get("GITHUB_REF", "")
    if ref.startswith("refs/tags/"):
        tag = ref.removeprefix("refs/tags/")
        if pin != tag:
            print(f"::error::Tag {tag}, but the pins point at {pin}. This release's reusable workflows run the {pin} actions.")
            return 1
        return 0

    if git("rev-parse", "-q", "--verify", f"refs/tags/{pin}").returncode == 0:
        diff = git("diff", "--stat", pin, "HEAD", "--", *SHIPPED)
        if diff.returncode != 0:
            print(f"::error::Could not compare HEAD with {pin}: {diff.stderr.strip()}")
            return 1
        if diff.stdout.strip():
            print(
                f"::error::The shipped actions/workflows changed since {pin}, but the pins still "
                f"point at {pin}. Bump every pin to the next version (see CONTRIBUTING.md, 'Pushing tags')."
            )
            print(diff.stdout, end="")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
