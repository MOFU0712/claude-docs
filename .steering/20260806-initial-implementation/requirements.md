# 初回実装 要求内容

## 変更・追加する機能の説明

`docs/`配下で承認済みの6つの永続ドキュメント（product-requirements.md〜glossary.md）に基づき、本プロジェクトの初回実装を行う。具体的には以下を新規に作成する。

- `sources.yaml`（Claude Code / API・モデルの2ソースを定義）
- `scripts/sync.py`（定期同期のエントリポイント）
- `scripts/fetch_page.py`（個別URL取得のエントリポイント）
- `scripts/publish.py`（knowledge-share-repoへの公開エントリポイント）
- `scripts/lib/splitter.py`（llms-full.txtのページ分割ロジック）
- `scripts/lib/frontmatter.py`（frontmatter読み書きユーティリティ）
- `tests/test_splitter.py` / `tests/test_frontmatter.py`
- `pyproject.toml`（uv / ruff / mypy / pytest設定）
- `README.md`（セットアップ・使い方）
- `.gitignore`
- `INDEX.md`（初回同期後に自動生成される索引。空の状態から開始）

定期実行（cron）の登録は、`sync.py`が手動実行で正しく動作することを確認した後、`schedule`スキル等を使って別途行う（初回実装のスコープ外とする）。

## ユーザーストーリー

- 筒井として、`uv run python scripts/sync.py`を実行すると、Claude CodeとAPI/モデルの公式ドキュメントが`content/`配下にMarkdownとして保存され、`claude-docs`リポジトリにコミットされてほしい。
- 筒井として、`uv run python scripts/fetch_page.py <URL>`を実行すると、指定したページ1件だけを取得・保存・コミットできてほしい。
- 筒井として、再度`sync.py`を実行したとき、内容に変更のないファイルは書き換えられず、コミットにも含まれてほしくない。
- 筒井として、`uv run python scripts/publish.py`を実行すると、`content/`との差分がプレビュー表示され、確認に応じたときのみ`knowledge-share-repo/claude-docs/`へコピー・`metadata.yaml`更新・git push が行われてほしい。
- 筒井として、コード変更後に`ruff check` / `ruff format --check` / `mypy` / `pytest`をまとめて実行し、全て通ることを確認したい。

## 受け入れ条件

- [ ] `sources.yaml`に`claude-code`（code.claude.com/docs）と`api-models`（platform.claude.com/docs）の2ソースが定義されている
- [ ] `sync.py`を実行すると、両ソースの`llms-full.txt`を取得し、`content/claude-code/`・`content/api-models/`配下にページ単位のMarkdownファイル（frontmatter付き）が生成される
- [ ] `sync.py`の再実行時、内容に変更のないファイルは上書きされず、gitコミットにも含まれない（`content_hash`による差分検知）
- [ ] `sync.py`実行後、`INDEX.md`が最新の状態に自動再生成される
- [ ] `sync.py`は1ソースの取得に失敗しても中断せず、他のソースの同期を継続し、最後に失敗をサマリー表示する
- [ ] `fetch_page.py <URL>`を実行すると、指定した1ページのみが取得・保存され、`sync.py`と同じ差分検知・コミットロジックが適用される
- [ ] `publish.py`を実行すると、`content/`と`knowledge-share-repo/claude-docs/`の差分がプレビュー表示され、ユーザーが確認したときのみコピー・`metadata.yaml`更新・git commit・pushが行われる
- [ ] `publish.py`実行中にエラーが発生した場合、`knowledge-share-repo`側に中途半端な変更を残さず中断する
- [ ] `tests/`のユニットテスト（`splitter.py`・`frontmatter.py`対象）が実ネットワークアクセスなしで実行でき、全て通る
- [ ] `ruff check . && ruff format --check . && mypy scripts/ && pytest`がすべて成功する
- [ ] `README.md`に、セットアップ手順・各スクリプトの実行方法・cron登録の想定手順が記載されている

## 制約事項

- `.env`ファイルの読み取りや、認証情報・機密情報のハードコードは行わない（公式ドキュメントサイトは認証不要のため、そもそも秘密情報を扱わない設計とする）
- `claude-docs`・`knowledge-share-repo`のいずれに対しても`git push --force`は行わない
- `knowledge-share-repo`へのpushは、`publish.py`の確認フローを経た場合にのみ行い、本ステアリング作業中に実際の公開（実データでのpush）は行わない。動作確認はダミーの一時gitリポジトリに対して行う
- 自動テストでは外部ネットワークアクセスを行わない（HTTP取得部分はモック化する）
- cronへの実際の登録（`schedule`スキル利用等）は初回実装のスコープ外とし、`sync.py`単体の手動実行確認をもって完了とする
- 1ファイル1000行を超える実装は行わない（`development-guidelines.md`の単一責務の原則に従い、必要に応じてファイルを分割する）
