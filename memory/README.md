# memory/ — エージェントの記憶

Anthropic の記事「Components of agent memory」
(https://www.anthropic.com/research/components-of-agent-memory) の 4 層 + dreaming を、
Claude Code のクラウドセッション向けに作ったもの。

クラウドのコンテナはセッションごとに作り直されるため、Claude Code 標準の auto memory
（`~/.claude/projects/.../memory/`）は次のセッションに残らない。そこで記憶をリポジトリに置き、git で持ち越す。

## 4 つの層

| 層 | 記事での役割 | ここでの置き場所 |
| --- | --- | --- |
| 1. トランスクリプト | 全セッションの記録。他の層を検証するための「正解」 | クラウドのセッション履歴（`list_sessions` / `list_events` で読める）と、現セッションのローカル JSONL。**リポジトリには入れない**（公開リポジトリのため）。`journal/` が各セッションへの目印になる |
| 2. メモ（notes） | 作業中に書き留めた気づき | `notes/` — 1 トピック 1 ファイル |
| 3. 表現（representations） | トピックごとにまとめ、互いにリンクした wiki | `wiki/` — 1 トピック 1 ページ、`wiki/index.md` から辿れる |
| 4. 注入コンテキスト | 毎セッション最初に読み込む小さな要約 | `MEMORY.md`（`CLAUDE.md` から `@memory/MEMORY.md` で読み込み）。200 行以内 |

さらに **dreaming**（`/dream`）が、トランスクリプトとメモを読み直して誤りを直し、wiki を作り、
大事なものを `MEMORY.md` に昇格させ、古いものを消す。記録は `dream-log.md`。

## 運用のルール（記事の知見から）

- **目的を伝え、手順は縛らない。** 何を書くかは Claude が判断する。「失敗だけ書け」のような固定ルールは強いモデルの効果を下げる。
- **見れば分かることは書かない。** コード・ファイル・画面から読み取れることではなく、計画・方針・試して確かめたルール・ユーザーの好みを書く。
- **確かめたかどうかを書く。** 検証済みの事実には「(確認済み YYYY-MM-DD)」などと書き添える。
- **書き手ごとに別ファイル。** 並行して書くと上書きし合う（記事では共有テーブルで 57 件中 16 件が失われた）。
  ここでもセッションごとに別ブランチなので、普段の記録は `journal/` と `notes/` の個別ファイルに書き、
  共有ファイル `MEMORY.md` の大きな書き換えは主に `/dream` で行う（マージ時の衝突を減らすため）。
- **wiki は抽象化する。** 元資料を写すだけの wiki は膨らむだけ（記事では元資料の 1.77 倍）。要点・判断・リンクを書く。
- **検索と組み合わせる。** wiki で当たりをつけ、細部はトランスクリプトや元ファイルを検索して確かめる。

## journal/

各セッションで 1 ファイル: `journal/YYYY-MM-DD_<ID8文字>.md`。ID8文字はクラウドなら `session_01` に続く 8 文字（例 `2026-11-07_RzuyKJaM.md`）、ローカルならセッション UUID の先頭 8 文字。
ローカルのセッションのトランスクリプトはその PC にしかなく、クラウドの dreaming からは読めない。そのぶん journal を少し詳しく書く。
セッション ID（`session_...`）、何をしたか、何を学んだか、どの notes を書いたかを数行で。
dreaming がどのトランスクリプトを読み直すべきかの目印になる。
セッション ID は SessionStart フックが最初に表示する。

## tools/

- `tools/check.py` — `MEMORY.md` の行数・サイズと、`memory/` 内の壊れたリンクを検査する。
  `Write`/`Edit` 後のフックからも自動で呼ばれる。
- `tools/transcript.py` — ローカルのトランスクリプト（JSONL）を読みやすく表示・検索する。
- `tools/sync.sh` — 記憶の変更を `main` に届ける（下記）。
- `tools/session_start.py` — SessionStart フック。セッション ID と、dreaming していないセッション数を表示する。

## 次のセッションへ持ち越すには

新しいセッションは `main` から始まる。記憶を変えたら次を実行する:

```
bash memory/tools/sync.sh "短い説明"
```

`memory/` だけをコミットし、このブランチの記憶のコミットのうち `main` にまだないものを
`main` の上に cherry-pick してプッシュする（作業ブランチのコードは `main` に入らない）。
何度実行しても安全。別のセッションと同じファイルを同時に変えて衝突したときは止まって知らせる。

ユーザーは `memory/` の変更に限り `main` へ直接プッシュすることを許可している。

## 手元の PC（Windows など）で使う

リポジトリをクローンして Claude Code を起動すれば同じように動く。必要なのは Git（Windows なら Git for Windows。Claude Code 自体が必要とする）と Python 3。
フックは `tools/run.sh` 経由で `python3` / `python` / `py` のどれかを使う。改行コードは `.gitattributes` で LF に固定している。
Python が見つからないときフックは何もせずに終わる（作業は止めない）。

## 自動の dreaming

毎週 1 回、スケジュールされたタスクが新しいセッションで `/dream` を実行し、結果を `sync.sh` で `main` に届ける。
