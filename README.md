# claude-docs

Anthropic公式ドキュメント（[Claude Code](https://code.claude.com/docs) / [API・モデル](https://platform.claude.com/docs)）を、要約・改変せずに忠実なMarkdownとしてローカルにミラーするツールです。

- **同期（sync）**: 定期的に公式サイトの最新内容を`content/`配下に取得し、`claude-docs`リポジトリにコミットする
- **取得（fetch）**: 個別ページを1件だけ指定して取得する
- **公開（publish）**: `content/`の内容を、全社ナレッジ共有リポジトリ（`knowledge-share-repo`）へ手動で公開する

詳細な設計・用語定義は [`docs/`](./docs/) を参照してください。

## セットアップ

```bash
# 依存関係のインストール（uvが必要）
uv sync
```

## 使い方

### 同期（全ソース）

```bash
uv run python scripts/sync.py
```

`sources.yaml`に定義された全ソースの`llms-full.txt`を取得し、ページ単位に分割して`content/<source>/`配下に保存します。内容に変更があったファイルのみ書き込み・コミット対象になります（`content_hash`による差分検知）。実行結果は新規/更新/変更なし/取得失敗の件数でサマリー表示されます。1ソースの取得に失敗しても他のソースの同期は継続します。

### 個別ページの取得

```bash
uv run python scripts/fetch_page.py https://code.claude.com/docs/en/agents
```

指定したURL1件だけを取得・保存します。保存先ソース（`content/claude-code/`か`content/api-models/`か）は、URLと`sources.yaml`の`page_base_url`の一致で自動判定されます。差分検知・コミットのロジックは`sync.py`と共通です。

### 全社ナレッジ共有リポジトリへの公開

```bash
uv run python scripts/publish.py
```

`content/`と`knowledge-share-repo/claude-docs/`の差分をプレビュー表示し、`y`と回答したときのみ、対象ファイルのコピー・`metadata.yaml`の更新・`knowledge-share-repo`側でのgit commit・pushを行います。処理途中でエラーが発生した場合は、コミット済みでpushに失敗したケースも含めてロールバックし、`knowledge-share-repo`側に中途半端な変更を残しません。

同期（`sync.py` / `fetch_page.py`）とは完全に独立しており、`publish.py`を実行しない限り全社への公開は行われません。

## 品質チェック

コード変更後は、以下を全て実行してすべて成功することを確認してください。

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy scripts/
uv run pytest
```

## 定期実行（cron）の想定手順

本リポジトリ自体はcron登録を行いません。`sync.py`を手動実行で検証したうえで、`schedule`スキル等を使って別途、以下のようなコマンドを定期実行するジョブを登録することを想定しています。

```bash
cd /home/tsutsui_kana/claude-docs && uv run python scripts/sync.py
```

`publish.py`は人手のトリガーを必要とする処理のため、cron登録の対象にはしません。

## ディレクトリ構成

構成の詳細は [`docs/repository-structure.md`](./docs/repository-structure.md) を参照してください。

```
claude-docs/
├── sources.yaml        # 同期対象ソースの定義（新ソース追加時はここに1エントリ追加するのみ）
├── content/             # 取得した公式ドキュメントの本体（ミラー、生成物）
├── INDEX.md             # content/配下の索引（自動生成）
├── scripts/
│   ├── sync.py
│   ├── fetch_page.py
│   ├── publish.py
│   └── lib/
│       ├── splitter.py
│       ├── frontmatter.py
│       └── storage.py
└── tests/
```
