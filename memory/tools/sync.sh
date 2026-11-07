#!/usr/bin/env bash
# Commit changes under memory/ and deliver them to origin/main, whatever branch
# this session works on, so the next session (which starts from main) sees them.
#
# Usage: bash memory/tools/sync.sh ["short message"]
#
# - Commits only memory/ (other changes stay uncommitted / on this branch).
# - Cherry-picks this branch's memory-only commits that main lacks onto
#   origin/main in a temporary worktree and pushes. Commits already on main
#   (same patch) are skipped, so running it again is safe.
# - Retries if main moved meanwhile. On a merge conflict it stops and says so.
set -euo pipefail

repo=$(git rev-parse --show-toplevel)
cd "$repo"
msg=${1:-"update memory"}

git add -A memory
if ! git diff --cached --quiet -- memory; then
  git commit -q -m "memory: $msg" -- memory
fi

branch=$(git rev-parse --abbrev-ref HEAD)

fetch() {
  local i
  for i in 2 4 8 16; do
    git fetch -q origin main 2>/dev/null && return 0
    git ls-remote --exit-code origin main >/dev/null 2>&1 || return 1   # no main yet
    sleep "$i"
  done
  return 1
}

if ! fetch; then
  echo "origin/main がないので、このブランチをそのまま main として作る"
  git push -q origin HEAD:main
  exit 0
fi

# memory-only commits on this branch whose patch is not on main yet (oldest first)
picks=()
while read -r sign sha; do
  [ "$sign" = "+" ] || continue
  if [ -z "$(git diff-tree --no-commit-id --name-only -r "$sha" | grep -v '^memory/' || true)" ]; then
    picks+=("$sha")
  fi
done < <(git cherry origin/main HEAD)

if [ ${#picks[@]} -eq 0 ]; then
  echo "main は最新（送る記憶の変更なし）"
  exit 0
fi

for attempt in 1 2 3 4; do
  tmp=$(mktemp -d)
  git worktree add -q --detach "$tmp" origin/main
  if ! git -C "$tmp" cherry-pick --allow-empty --keep-redundant-commits "${picks[@]}" >/dev/null 2>&1; then
    git -C "$tmp" cherry-pick --abort >/dev/null 2>&1 || true
    git worktree remove --force "$tmp"
    echo "衝突: main の記憶が別のセッションで変わっている。git merge origin/main で取り込み、memory/ の衝突を直してから再実行すること。" >&2
    exit 1
  fi
  if git -C "$tmp" push -q origin HEAD:main 2>/dev/null; then
    git worktree remove --force "$tmp"
    echo "記憶の変更 ${#picks[@]} 件を main に送った（作業ブランチ: $branch）"
    exit 0
  fi
  git worktree remove --force "$tmp"
  sleep $((attempt * 2))
  fetch
done
echo "main へのプッシュに失敗した" >&2
exit 1
