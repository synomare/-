#!/usr/bin/env sh
# Run a memory tool with whatever Python exists (python3 on Linux/macOS,
# python or py on Windows, where "python3" may be missing or a Store stub).
# Usage: sh memory/tools/run.sh <script.py> [args...]   (stdin is passed through)
dir=$(cd "$(dirname "$0")" && pwd)
script=$1; shift
for py in python3 python py; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; sys.exit(sys.version_info < (3, 7))' >/dev/null 2>&1; then
    PYTHONUTF8=1 PYTHONIOENCODING=utf-8 exec "$py" "$dir/$script" "$@"
  fi
done
echo "memory: Python 3 が見つからないので $script を実行できない" >&2
exit 0
