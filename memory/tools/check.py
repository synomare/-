#!/usr/bin/env python3
"""Check the memory folder: MEMORY.md read limits and broken relative links.

Usage:
  python3 memory/tools/check.py          # report, exit 1 if problems
  python3 memory/tools/check.py --hook   # PostToolUse hook mode (reads hook JSON on stdin)

In hook mode it only runs when the edited file is inside memory/, and reports
problems on stderr with exit code 2 so Claude sees them and can fix them.
"""
import json
import os
import re
import sys
from pathlib import Path

MEMORY_DIR = Path(__file__).resolve().parent.parent
INDEX = MEMORY_DIR / "MEMORY.md"
MAX_LINES = 200
MAX_BYTES = 25 * 1024
WARN_LINES = 150

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


def check_index():
    problems, warnings = [], []
    if not INDEX.exists():
        problems.append("memory/MEMORY.md がない")
        return problems, warnings
    data = INDEX.read_bytes()
    lines = data.decode("utf-8", "replace").count("\n") + 1
    if lines > MAX_LINES or len(data) > MAX_BYTES:
        problems.append(
            f"memory/MEMORY.md が上限超過 ({lines} 行 / {len(data)} bytes, 上限 {MAX_LINES} 行・{MAX_BYTES} bytes)。"
            " 詳細を notes/ や wiki/ に移し、古い項目を消して短くすること。"
        )
    elif lines > WARN_LINES:
        warnings.append(f"memory/MEMORY.md が {lines} 行。{MAX_LINES} 行に近いので、詳細を wiki/ に移すことを検討。")
    return problems, warnings


def check_links():
    broken = []
    for md in MEMORY_DIR.rglob("*.md"):
        text = md.read_text(encoding="utf-8", errors="replace")
        # ignore links inside fenced code blocks
        text = re.sub(r"```.*?```", "", text, flags=re.S)
        for target in LINK_RE.findall(text):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            path = target.split("#", 1)[0]
            if not path:
                continue
            if not (md.parent / path).resolve().exists():
                broken.append(f"{md.relative_to(MEMORY_DIR.parent)} -> {target}")
    return broken


def main():
    hook = "--hook" in sys.argv
    if hook:
        try:
            payload = json.load(sys.stdin)
        except Exception:
            return 0
        fp = (payload.get("tool_input") or {}).get("file_path") or ""
        try:
            Path(fp).resolve().relative_to(MEMORY_DIR)
        except ValueError:
            return 0

    problems, warnings = check_index()
    broken = check_links()
    if broken:
        problems.append("memory/ 内の壊れたリンク:\n  " + "\n  ".join(broken))

    if hook:
        if problems:
            print("\n".join(problems + warnings), file=sys.stderr)
            return 2
        if warnings:
            print("\n".join(warnings), file=sys.stderr)
        return 0

    for w in warnings:
        print("warning:", w)
    for p in problems:
        print("problem:", p)
    if not problems and not warnings:
        print("ok: MEMORY.md は上限内、壊れたリンクなし")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
