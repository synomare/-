#!/usr/bin/env python3
"""SessionStart hook: print a short memory status that Claude sees at startup.

Shows this session's ID (so the journal entry can point at the transcript) and
how many journal entries are newer than the last /dream.
"""
import json
import os
import re
import sys
from pathlib import Path

MEMORY_DIR = Path(__file__).resolve().parent.parent


def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    remote = os.environ.get("CLAUDE_CODE_REMOTE_SESSION_ID", "")
    session_id = "session_" + remote[4:] if remote.startswith("cse_") else payload.get("session_id", "")

    last = "none"
    log = MEMORY_DIR / "dream-log.md"
    if log.exists():
        m = re.search(r"<!-- last-dream: (\S+) -->", log.read_text(encoding="utf-8"))
        if m:
            last = m.group(1)

    journal = sorted(p.name for p in (MEMORY_DIR / "journal").glob("*.md"))
    # the marker holds the last processed journal name (without .md); names sort by date
    pending = [n for n in journal if last == "none" or n[:-3] > last]

    lines = [f"[memory] このセッションの ID: {session_id or '不明'}"]
    if payload.get("transcript_path"):
        lines.append(f"[memory] ローカルのトランスクリプト: {payload['transcript_path']}")
    lines.append(f"[memory] 最後の dreaming: {last} / それ以降の journal: {len(pending)} 件")
    if len(pending) >= 5:
        lines.append("[memory] 未整理のセッションがたまっている。区切りのよいところで /dream を提案するとよい。")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
