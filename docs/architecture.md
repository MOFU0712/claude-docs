# 技術仕様書

## テクノロジースタック

| 項目 | 選定 | 理由 |
|---|---|---|
| 言語 | Python 3.11+ | テキスト処理（正規表現分割・frontmatter生成）とYAML操作が中心で、標準ライブラリ＋薄いライブラリで完結する。cronからの定期実行にも向く |
| HTTP取得 | `requests` | `llms-full.txt`・個別ページ`.md`の取得のみ。認証不要のシンプルなGETで足りる |
| YAML処理 | `PyYAML` | `sources.yaml`、`knowledge-share-repo`側`metadata.yaml`の読み書き |
| frontmatter処理 | 自前の薄いユーティリティ（`scripts/lib/frontmatter.py`） | 依存を増やさず、`---`区切りの単純なYAML frontmatterだけを扱えれば十分なため |
| バージョン管理 | Git（`~/claude-docs`、`~/project_tri/knowledge-share-repo`の2リポジトリ） | 両リポジトリとも既存の運用（後者はGitHub org `tripleize-inc`と連携済み）に準拠する |
| 実行環境 | ローカル（WSL2/Linux）＋ cron | 追加インフラを持たない方針（[product-requirements.md](./product-requirements.md)の非機能要件に準拠） |

## 開発ツールと手法

| 項目 | 選定 |
|---|---|
| パッケージ・環境管理 | `uv`（軽量・高速。`pyproject.toml`で依存を管理） |
| Lint / フォーマット | `ruff`（JS圏のESLint＋Prettierに相当する役割を1ツールで担う） |
| 型チェック | `mypy`（標準的な厳しさで運用。個人ツールのため過度なstrict設定はしない） |
| テスト | `pytest`（特に`splitter.py`のページ分割ロジック、`frontmatter.py`の読み書きロジックを中心にユニットテストを書く） |
| 品質チェックコマンド | `ruff check .` / `ruff format .` / `mypy scripts/` / `pytest` をコード変更後に必ず実行する |

## 技術的制約と要件

- **ネットワーク依存**: 同期処理には`code.claude.com` / `platform.claude.com`へのHTTPS GETが必須。オフライン環境では実行できない
- **認証不要・機密情報を扱わない**: 対象は公開ドキュメントのみ。`.env`や認証情報を読み書きするコードは持たない
- **`knowledge-share-repo`の既存運用ルールを厳守**:
  - 公開可な資料のみを`claude-docs/`カテゴリに置く
  - 追加・更新したファイルは必ず`metadata.yaml`に反映する（未記載ファイルはアプリ側に表示されない）
  - 通常の`git push`のみで完結させる。プルリクエスト必須ではないが強制もしない
- **破壊的git操作の禁止**: `git push --force`は両リポジトリとも行わない。`publish.py`のpushは明示的な実行確認を経てから行う（[functional-design.md](./functional-design.md)のユースケース3参照）
- **cron実行権限**: ユーザー権限で完結させ、システム全体の設定・他ユーザーに影響する操作は行わない

## パフォーマンス要件

- 全ソース（Claude Code + API/モデル、合計数百ページ規模）の同期が、通常のネットワーク環境で**数分以内**に完了すること
- `llms-full.txt`は数百KB〜MB級のテキストになり得るため、ストリーミング処理までは不要だが、メモリ上で一括処理してもリソース上問題ないことを確認する
- 差分検知（`content_hash`比較）により、変更のないファイルへの書き込み・git commit対象化を避け、無駄なI/Oとコミット履歴の肥大化を防ぐ
