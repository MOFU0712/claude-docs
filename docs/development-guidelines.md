# 開発ガイドライン

## コーディング規約

- PEP8に準拠し、`ruff check` / `ruff format`を通すことを必須とする
- すべての関数・スクリプトのエントリポイントに型ヒントを付与し、`mypy`を通すことを必須とする
- スクリプトは`def main() -> None:` を持ち、`if __name__ == "__main__": main()`で起動する構成に統一する
- 外部HTTPリクエストは共通のヘルパー経由で行い、タイムアウト（例: 30秒）を必ず指定する
- **エラー時の方針を処理単位で分ける**:
  - `sync.py`は1つのソース（例: Claude Code）の取得に失敗しても、他のソースの同期は継続する。失敗はログに残し、最後にサマリーとして報告する
  - `publish.py`は差分プレビュー〜git push確認までの間にエラーが起きた場合、即座に中断し、`knowledge-share-repo`側を中途半端な状態にしない
- 関数は単一責務を意識し、「取得」「分割」「差分検知」「保存」「コミット」を別関数に分離する（[functional-design.md](./functional-design.md)のコンポーネント設計に対応させる）

## 命名規則

| 対象 | 規則 | 例 |
|---|---|---|
| Pythonの変数・関数 | snake_case | `fetch_page`, `content_hash` |
| Pythonの定数 | UPPER_SNAKE_CASE | `DEFAULT_TIMEOUT_SEC` |
| `content/`配下のディレクトリ名 | `sources.yaml`の`name`と一致させる（kebab-case） | `claude-code/`, `api-models/` |
| `content/`配下のファイル名 | 取得元URLのパスをそのまま踏襲する | `agents.md`, `admin-setup.md` |
| frontmatterのキー | snake_case | `source_url`, `fetched_at`, `content_hash` |

## スタイリング規約（Markdown出力規約）

本プロダクトにUIは存在しないため、一般的な「スタイリング規約」は「取得したMarkdownの扱い方の規約」と読み替える。

- 取得した本文は公式サイトの内容をできる限りそのまま保持し、要約・言い換え・意訳を加えない（[product-requirements.md](./product-requirements.md)の「忠実なリファレンス」という目的に直結するため）
- 各ファイル冒頭に`source_url` / `fetched_at` / `content_hash`のfrontmatterを必ず付与する
- 見出しレベルは元のMarkdownをそのまま踏襲し、独自に変更しない
- 本文中の相対リンクなど、変換が必要な最低限の処理を除き、リンク切れの修復などはスコープ外とする

## テスト規約

- `pytest`で`scripts/lib/`配下のロジック（`splitter.py`、`frontmatter.py`）を中心にユニットテストを書く
- `splitter.py`のテストは、実際の`llms-full.txt`から一部を切り出した固定のサンプルテキストをフィクスチャとして用意し、ページ数・タイトル・`source_url`が正しく分割されることを検証する
- 外部ネットワークアクセスを伴うテストは書かない（HTTP取得部分はモック化する）
- `publish.py`のgit操作は、一時ディレクトリ上に作成したダミーのgitリポジトリを対象にテストする（実際の`knowledge-share-repo`には触れない）
- コード変更後は`ruff check . && ruff format --check . && mypy scripts/ && pytest`を必ず実行する

## Git規約

- コミットメッセージはConventional Commits形式に従う（グローバル`~/.claude/CLAUDE.md`の規約に準拠）
- `claude-docs`リポジトリ:
  - `sync.py`実行時: `docs: sync N files from <source> (YYYY-MM-DD)`
  - `fetch_page.py`実行時: `docs: add <url> via fetch_page`
  - 設計ドキュメント（`docs/`, `.steering/`）の変更: `docs: ...`で内容が分かるメッセージにする
- `knowledge-share-repo`への公開コミット（`publish.py`実行時）: `docs: publish claude-docs (N files updated)`のように、変更件数が分かるメッセージにする
- 両リポジトリとも`git push --force`は行わない。通常の`push`のみで完結させる
- `knowledge-share-repo`へのpushは、`publish.py`が差分プレビューを表示し、実行確認を得たあとにのみ行う
