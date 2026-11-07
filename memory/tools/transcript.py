#!/usr/bin/env python3
"""Read Claude Code session transcripts (JSONL) as plain text.

Usage:
  python3 memory/tools/transcript.py list
  python3 memory/tools/transcript.py show [PATH_OR_ID] [--tools]
  python3 memory/tools/transcript.py search PATTERN

Only transcripts on this machine are visible (in a cloud session: the current
one). Earlier cloud sessions are read with the claude-code-remote MCP tools
list_sessions / list_events instead.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path.home() / ".claude" / "projects"


def files():
    return sorted(ROOT.glob("*/*.jsonl"), key=lambda p: p.stat().st_mtime)


def resolve(arg):
    if not arg:
        fs = files()
        return fs[-1] if fs else None
    p = Path(arg)
    if p.exists():
        return p
    for f in files():
        if arg in f.stem:
            return f
    return None


def text_of(content, with_tools):
    if isinstance(content, str):
        return content
    out = []
    for block in content or []:
        t = block.get("type")
        if t == "text":
            out.append(block.get("text", ""))
        elif with_tools and t == "tool_use":
            out.append(f"[tool {block.get('name')}] {json.dumps(block.get('input'), ensure_ascii=False)[:500]}")
        elif with_tools and t == "tool_result":
            c = block.get("content")
            c = text_of(c, False) if isinstance(c, list) else str(c)
            out.append(f"[result] {c[:500]}")
    return "\n".join(x for x in out if x)


def entries(path, with_tools=False):
    for line in path.open(encoding="utf-8", errors="replace"):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("type") not in ("user", "assistant") or e.get("isMeta"):
            continue
        msg = e.get("message") or {}
        txt = text_of(msg.get("content"), with_tools).strip()
        if txt:
            yield e.get("timestamp", "")[:19], msg.get("role", e["type"]), txt


for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass


def main(argv):
    if not argv or argv[0] == "list":
        for f in files():
            print(f"{f.stem}  {f.stat().st_size // 1024} KB  {f}")
        return 0
    cmd, rest = argv[0], argv[1:]
    with_tools = "--tools" in rest
    rest = [a for a in rest if a != "--tools"]
    if cmd == "show":
        path = resolve(rest[0] if rest else None)
        if not path:
            print("transcript not found", file=sys.stderr)
            return 1
        for ts, role, txt in entries(path, with_tools):
            print(f"--- {ts} {role}\n{txt}\n")
        return 0
    if cmd == "search" and rest:
        rx = re.compile(rest[0], re.I)
        for f in files():
            for ts, role, txt in entries(f, True):
                for ln in txt.splitlines():
                    if rx.search(ln):
                        print(f"{f.stem[:8]} {ts} {role}: {ln[:300]}")
        return 0
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
