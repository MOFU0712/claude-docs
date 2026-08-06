# 初回実装 設計

## 実装アプローチ

`docs/functional-design.md`のコンポーネント設計をそのままPythonモジュールに対応させる。共通処理（HTTP取得・分割・差分検知・frontmatter・コミット）を`scripts/lib/`に集約し、`sync.py`と`fetch_page.py`が共有することで、両者の差分検知ロジックの重複を避ける。

処理の流れは大きく4段階に分解する。

1. **取得**: `llms-full.txt`または個別`.md`をHTTPで取得する（`lib/http.py`想定 → 実際は`sync.py`/`fetch_page.py`内の共通ヘルパー関数として実装し、モジュール数を増やしすぎない）
2. **分割・整形**: `llms-full.txt`をページ単位に分割し、各ページのタイトル・source_url・本文を得る（`lib/splitter.py`）
3. **差分検知・保存**: 既存ファイルのfrontmatterと比較し、変更があるものだけ書き込む（`lib/frontmatter.py` + 呼び出し側のハッシュ比較）
4. **索引化・コミット**: `INDEX.md`を再生成し、変更があれば`git add` / `git commit`する

`publish.py`は上記4段階とは独立した第5の処理として、`content/`を読み取り専用の入力として扱い、`knowledge-share-repo`側への書き込み・差分プレビュー・確認・pushを行う。

## 変更するコンポーネント

| ファイル | 責務 |
|---|---|
| `sources.yaml` | ソース定義（`name` / `full_dump` / `page_base_url`） |
| `scripts/lib/splitter.py` | `llms-full.txt`のテキストを`Page`（title, source_url, body）のリストに分割する純粋関数 |
| `scripts/lib/frontmatter.py` | Markdown文字列とfrontmatter辞書の相互変換（`read_frontmatter()` / `write_frontmatter()`） |
| `scripts/sync.py` | 全ソースを走査し、取得→分割→差分検知→保存→INDEX.md再生成→コミットまでを行うCLIエントリポイント |
| `scripts/fetch_page.py` | 単一URLを引数に取り、`sync.py`と共通の保存・コミットロジックを再利用するCLIエントリポイント |
| `scripts/publish.py` | `content/`と`knowledge-share-repo/claude-docs/`を比較し、プレビュー表示→確認→コピー・`metadata.yaml`更新→コミット・pushを行うCLIエントリポイント |
| `tests/test_splitter.py` | `splitter.py`のユニットテスト（実際のllms-full.txtから切り出した固定フィクスチャを使用） |
| `tests/test_frontmatter.py` | `frontmatter.py`のユニットテスト |
| `pyproject.toml` | 依存関係（requests, PyYAML）、ruff/mypy/pytest設定 |
| `README.md` | セットアップ手順・実行コマンド一覧 |

`sync.py`と`fetch_page.py`の共通処理（保存・ハッシュ比較・コミット）は、どちらか一方に実装して import するのではなく、`scripts/lib/`にもう1モジュール（`storage.py`）を追加して共有する。これにより`docs/functional-design.md`が定義した「差分検知・commit処理を共通ロジックとして再利用する」という設計方針に合致させる。

| 追加ファイル（設計時点で確定） | 責務 |
|---|---|
| `scripts/lib/storage.py` | `Page`を受け取り、`content_hash`比較・ファイル書き込み・`INDEX.md`再生成・git commitを行う共通処理 |

## データ構造の変更

### `Page`（`splitter.py`が生成する中間データ）

```python
@dataclass
class Page:
    title: str
    source_url: str
    body: str
```

### `Source`（`sources.yaml`の1エントリに対応）

```python
@dataclass
class Source:
    name: str
    full_dump: str
    page_base_url: str
```

### frontmatter辞書（`frontmatter.py`が読み書きする対象）

```python
{
    "source_url": str,
    "fetched_at": str,   # ISO 8601
    "content_hash": str, # 本文のsha256等
}
```

### `sync.py` / `fetch_page.py`実行結果のサマリー（ログ出力・コミットメッセージ生成に使用）

```python
@dataclass
class SyncResult:
    source_name: str
    added: list[str]
    updated: list[str]
    unchanged_count: int
    failed: list[str]
```

`glossary.md`のCLI/ログ用語（新規・更新・変更なし・取得失敗）とこの`SyncResult`のフィールドを一致させる。

## 影響範囲の分析

- 本作業は新規リポジトリでの初回実装であり、既存コードへの影響はない
- `knowledge-share-repo`への影響は`publish.py`の実データ実行時のみ発生する。今回の初回実装では、`publish.py`の動作確認をダミーの一時gitリポジトリに対して行い、実リポジトリへの書き込み・pushは行わない（`requirements.md`の制約事項に対応）
- `content/`はgit管理下に置くが、初回実装完了時点では`sync.py`を最低1回手動実行して実データが入った状態を確認する。このコミットは`claude-docs`リポジトリ内で完結し、社外・他リポジトリには影響しない
- cron登録は行わないため、OS設定・crontabへの影響はない（`requirements.md`のスコープ外事項）
