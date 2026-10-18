#!/usr/bin/env python3
"""Render the Telegram notice for a new upstream tag from its GitHub Release notes.

Only the Chinese section of the release body is used; commit lists and compare
links are intentionally omitted.

Environment:
  LATEST  the new tag, e.g. dsh-v0.2.1-rc.3

Exit codes:
  0  message printed on stdout
  3  the tag has no GitHub Release yet (release notes may still be publishing)

Stdout is Telegram HTML (sent with parse_mode=HTML).
"""

import html
import json
import os
import re
import sys
import urllib.error
import urllib.request

UPSTREAM = "deepseek-ai/deepseek-harness"
MAX_CHARS = 3800

EN_MARKER = re.compile(r'id="en-|^#{1,6}\s*New Features\b|^New Features\s*$', re.I)
CN_LINK_LINE = re.compile(r"^\[中文\]")
H3_LINE = re.compile(r"^<h3[^>]*>(.*?)</h3>\s*$", re.I)
MD_HEADING = re.compile(r"^(#{2,6})\s+(.*)$")
BULLET = re.compile(r"^[-*]\s+(.*)$")
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
BOLD = re.compile(r"\*\*(.+?)\*\*")
CODE = re.compile(r"`([^`]+)`")


def get_json(path: str):
    request = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "dsh-upstream-watch",
        },
    )
    token = os.environ.get("GITHUB_TOKEN_FOR_READ")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def inline(text: str) -> str:
    """Escape HTML, then turn markdown links/bold/code into Telegram HTML."""
    escaped = html.escape(text, quote=False)
    escaped = LINK.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', escaped)
    escaped = BOLD.sub(r"<b>\1</b>", escaped)
    escaped = CODE.sub(r"<code>\1</code>", escaped)
    return escaped


def chinese_section(body: str):
    """Yield ('heading'|'bullet'|'text', rendered) for the Chinese part only."""
    blocks = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line or CN_LINK_LINE.match(line):
            continue
        if EN_MARKER.search(line):
            break
        if line.startswith("Full Changelog"):
            continue

        match = H3_LINE.match(line)
        if match:
            blocks.append(("heading", inline(match.group(1))))
            continue
        match = MD_HEADING.match(line)
        if match:
            blocks.append(("heading", inline(match.group(2))))
            continue
        match = BULLET.match(line)
        if match:
            blocks.append(("bullet", inline(match.group(1))))
            continue
        blocks.append(("text", inline(line)))
    return blocks


def render(latest: str, release) -> str:
    headline = f"<code>{html.escape(latest)}</code>"
    published = (release.get("published_at") or "")[:10] if release else ""
    if published:
        headline += f" · {published}"
    lines = ["🚀 <b>DSH 上游新发版</b>", headline, ""]

    if release is None:
        lines.append("（该版本尚未发布发行说明）")
    else:
        blocks = chinese_section(release.get("body") or "")
        if not blocks:
            lines.append("（该版本未提供中文发行说明）")
        for kind, text in blocks:
            if kind == "heading":
                if lines and lines[-1] != "":
                    lines.append("")
                lines.append(f"<b>{text}</b>")
            elif kind == "bullet":
                lines.append(f"• {text}")
            else:
                lines.append(text)

    link = (
        release.get("html_url")
        if release
        else f"https://github.com/{UPSTREAM}/releases/tag/{latest}"
    )
    link_line = f'<a href="{link}">在 GitHub 查看发行页</a>'

    content = "\n".join(lines)
    note = "…（内容较长，完整说明见发行页）"
    budget = MAX_CHARS - len(link_line) - len(note) - 6
    if len(content) > budget:
        content = content[:budget].rsplit("\n", 1)[0].rstrip() + "\n\n" + note
    return content + "\n\n" + link_line


def main() -> int:
    latest = os.environ.get("LATEST", "").strip()
    if not latest:
        print("notify.py: LATEST is required", file=sys.stderr)
        return 1

    try:
        release = get_json(f"/repos/{UPSTREAM}/releases/tags/{latest}")
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return 3
        raise
    except (urllib.error.URLError, TimeoutError, ValueError) as error:
        print(f"release({latest}) failed: {error}", file=sys.stderr)
        return 3

    print(render(latest, release))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
