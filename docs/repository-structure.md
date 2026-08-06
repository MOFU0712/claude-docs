# リポジトリ構造定義書

## フォルダ・ファイル構成

```
claude-docs/
├── README.md
├── pyproject.toml            # 依存関係・ruff/mypy/pytest設定
├── .gitignore
│
├── docs/                     # 永続ドキュメント（本ファイルの分類）
│   ├── product-requirements.md
│   ├── functional-design.md
│   ├── architecture.md
│   ├── repository-structure.md
│   ├── development-guidelines.md
│   └── glossary.md
│
├── .steering/                 # 作業単位ドキュメント
│   └── 20260806-initial-implementation/
│       ├── requirements.md
│       ├── design.md
│       └── tasklist.md
│
├── sources.yaml               # 同期対象ソースの定義
│
├── content/                   # 取得した公式ドキュメントの本体（ミラー）
│   ├── claude-code/
│   │   ├── admin-setup.md
│   │   ├── agents.md
│   │   └── ...
│   └── api-models/
│       ├── get-started.md
│       └── ...
├── INDEX.md                   # content/ 配下の索引（自動生成）
│
├── scripts/
│   ├── sync.py                 # 定期同期のエントリポイント
│   ├── fetch_page.py           # 個別URL取得のエントリポイント
│   ├── publish.py               # knowledge-share-repoへの公開エントリポイント
│   └── lib/
│       ├── splitter.py          # llms-full.txt のページ分割ロジック
│       └── frontmatter.py       # frontmatter読み書きユーティリティ
│
└── tests/
    ├── test_splitter.py
    └── test_frontmatter.py
```

参考: 公開先の`knowledge-share-repo`（既存・別リポジトリ）は次の構成を持つ。

```
knowledge-share-repo/                 # 既存の全社ナレッジ共有リポジトリ
├── meeting-notes/
├── claude-code-settings/
├── standardization/
├── design/
└── claude-docs/                       # 本プロダクトが新設するカテゴリ
    ├── metadata.yaml                  # 公開ファイルの一覧（publish.pyが生成・更新）
    ├── claude-code/
    │   └── ...
    └── api-models/
        └── ...
```

## ディレクトリの役割

| ディレクトリ / ファイル | 役割 |
|---|---|
| `docs/` | アプリケーション全体の恒久的な設計ドキュメント。大きな設計変更時のみ更新 |
| `.steering/` | 作業単位のステアリングドキュメント。作業ごとにディレクトリを新設 |
| `sources.yaml` | 同期対象の公式ドキュメントソース定義。新しいソースを追加する唯一の変更点 |
| `content/` | 取得した公式ドキュメントの実体（Markdown）。`sync.py`/`fetch_page.py`が書き込む、生成物としての性質を持つディレクトリ |
| `INDEX.md` | `content/`の索引。`sync.py`実行のたびに自動再生成される |
| `scripts/` | 同期・取得・公開を行う実行スクリプト本体 |
| `scripts/lib/` | 複数スクリプトから共有されるロジック（分割・frontmatter処理） |
| `tests/` | `scripts/lib/`のロジックに対するユニットテスト |

## ファイル配置ルール

- **永続ドキュメント（`docs/`）と生成物（`content/`）を混同しない**: `content/`配下は`sync.py`等が上書きする生成物であり、手動編集は行わない
- **`content/<source>/`のディレクトリ名は`sources.yaml`の`name`と一致させる**: Claude Codeは`claude-code/`、API/モデルは`api-models/`とする
- **`content/`配下のファイルパスは、取得元サイトのURLパス構造をそのまま踏襲する**: 例）`https://code.claude.com/docs/en/agents.md` → `content/claude-code/agents.md`
- **新しいソースを追加する際は`sources.yaml`に1エントリ追加するのみとし、`scripts/`のコード変更を発生させない**
- **`knowledge-share-repo/claude-docs/`配下の構成は`content/`と同一のディレクトリ構造をそのまま踏襲する**: `publish.py`は`content/`をそのままコピーし、`metadata.yaml`のみを`knowledge-share-repo`の既存フォーマットに合わせて生成する
- **`.steering/`配下は日付＋タイトルの命名規則（`YYYYMMDD-タイトル`）を守る**
