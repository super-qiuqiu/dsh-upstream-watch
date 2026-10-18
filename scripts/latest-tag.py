#!/usr/bin/env python3
"""Print the newest `dsh-v*` tag from stdin by semver-ish precedence.

Reads one tag per line (blank lines ignored) and prints the greatest one.
A final release sorts after its prereleases (`dsh-v0.2.1` > `dsh-v0.2.1-rc.2`),
and numeric prerelease identifiers sort numerically (`.rc.10` > `.rc.2`).
"""

import re
import sys

TAG_RE = re.compile(r"^dsh-v(\d+)\.(\d+)\.(\d+)(?:-(.+))?$")


def sort_key(tag: str):
    match = TAG_RE.match(tag)
    if not match:
        return ((0, 0, 0), (-1,))
    numbers = tuple(int(part) for part in match.groups()[:3])
    prerelease = match.group(4)
    if prerelease is None:
        return (numbers, (1,))
    identifiers = []
    for piece in prerelease.split("."):
        identifiers.append((1, int(piece)) if piece.isdigit() else (0, piece))
    return (numbers, (0, tuple(identifiers)))


def main() -> int:
    tags = [line.strip() for line in sys.stdin if line.strip()]
    if not tags:
        print("latest-tag.py: no tags on stdin", file=sys.stderr)
        return 1
    print(max(tags, key=sort_key))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
