# 実行環境について

- Claude Code のクラウドセッション。コンテナはセッションごとに作り直され、新しいセッションは `main` から始まる。(確認済み 2026-11-07)
- 標準の auto memory（`~/.claude/projects/.../memory/`）はコンテナと一緒に消えるので、記憶はリポジトリの `memory/` に置く。(確認済み 2026-11-07)
- リポジトリ `synomare/-` は公開。秘密情報は記憶に書かない。(確認済み 2026-11-07)
- 環境変数 `CLAUDE_CODE_REMOTE_SESSION_ID` は `cse_XXXX`。`get_session` / `list_events` に渡す ID は `session_XXXX`（末尾が同じ）。(確認済み 2026-11-07)
