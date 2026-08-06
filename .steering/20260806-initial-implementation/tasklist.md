# 初回実装 タスクリスト

凡例: [ ] 未着手 / [x] 完了

## 1. プロジェクト基盤

- [ ] `pyproject.toml`作成（uv管理、依存: `requests`, `PyYAML`、開発依存: `ruff`, `mypy`, `pytest`）
- [ ] `.gitignore`作成（`.venv/`, `__pycache__/`, `*.pyc`等）
- [ ] `uv sync`で仮想環境構築を確認
- [ ] `sources.yaml`作成（`claude-code`: `code.claude.com/docs`、`api-models`: `platform.claude.com/docs`の2エントリ）

## 2. 共通ロジック（scripts/lib/）

- [ ] `scripts/lib/splitter.py`: `llms-full.txt`のテキストを`Page`のリストに分割する`split_pages()`を実装
- [ ] `scripts/lib/frontmatter.py`: `read_frontmatter()` / `write_frontmatter()`を実装
- [ ] `scripts/lib/storage.py`: `Page`を受け取り、`content_hash`比較・書き込み・`INDEX.md`再生成・git commitを行う共通処理を実装
- [ ] 上記3モジュールについて`mypy`の型チェックを通す

## 3. テスト（scripts/lib/対象）

- [ ] `tests/test_splitter.py`: 実際の`llms-full.txt`から切り出した固定フィクスチャで、ページ数・タイトル・`source_url`の分割結果を検証
- [ ] `tests/test_frontmatter.py`: frontmatter付きMarkdownの読み書きが正しく往復することを検証
- [ ] `pytest`が全て通ることを確認（外部ネットワークアクセスなし）

## 4. sync.py

- [ ] `Source`データクラスと`sources.yaml`読み込み処理を実装
- [ ] 共通HTTP取得ヘルパー（タイムアウト指定）を実装
- [ ] 各ソースについて「取得→分割→差分検知→保存」を行うループを実装
- [ ] 1ソースの失敗が他ソースの処理を止めないこと（try/exceptで継続）を実装
- [ ] 実行後に`SyncResult`のサマリー（新規/更新/変更なし/取得失敗）をログ出力する処理を実装
- [ ] `INDEX.md`再生成、変更があればgit commitする処理を実装
- [ ] `claude-code`・`api-models`の実データに対して手動実行し、`content/`配下にファイルが生成されることを確認
- [ ] 変更なしの状態で再実行し、差分検知により書き込み・コミットがスキップされることを確認

## 5. fetch_page.py

- [ ] 引数でURLを受け取り、`.md`を付与して取得する処理を実装
- [ ] `sync.py`と共通の保存・差分検知・コミットロジック（`storage.py`）を再利用する形で実装
- [ ] 実際のURL1件を指定して手動実行し、動作を確認

## 6. publish.py

- [ ] `content/`と`knowledge-share-repo/claude-docs/`の差分を検出する処理を実装
- [ ] 差分内容（新規/更新/削除されるファイル一覧）をプレビュー表示する処理を実装
- [ ] ユーザーの実行確認（y/n等）を経てからコピー・`metadata.yaml`生成/更新を行う処理を実装
- [ ] 確認後に`knowledge-share-repo`側でgit add/commit/pushを行う処理を実装
- [ ] エラー発生時に処理を即座に中断する例外処理を実装
- [ ] ダミーの一時gitリポジトリ2つ（`content/`役・`knowledge-share-repo`役）を使い、コピー・`metadata.yaml`生成・プレビュー・確認・commitの一連の動作を確認（実リポジトリへは触れない）

## 7. ドキュメント・仕上げ

- [ ] `README.md`作成（セットアップ手順、各スクリプトの実行方法、cron登録の想定手順を記載）
- [ ] `ruff check . && ruff format --check . && mypy scripts/ && pytest`が全て成功することを確認
- [ ] `git status`で差分を確認し、日本語のコミットメッセージ（Conventional Commits形式）でコミット

## 完了条件

- [ ] `requirements.md`の受け入れ条件をすべて満たしている
- [ ] `sync.py`の手動実行により`content/`に実データが投入されている
- [ ] `publish.py`はダミーリポジトリでの動作確認が完了している（実`knowledge-share-repo`への公開は本タスクリストの範囲外、別途ユーザーの判断で実施）
- [ ] 品質チェックコマンドがすべて成功している
- [ ] ユーザーが「コミットしました」と回答した時点で、本タスクリストを完了とする
