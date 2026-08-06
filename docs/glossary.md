# ユビキタス言語定義

## ドメイン用語の定義

| 用語 | 定義 |
|---|---|
| ソース（source） | 同期対象となる公式ドキュメント群の単位。現状は「Claude Code」「API/モデル」の2つ。`sources.yaml`の1エントリに対応する |
| 同期（sync） | あるソースの`llms-full.txt`を取得し、ページ単位に分割、差分検知、`content/`への保存、`INDEX.md`再生成、`claude-docs`リポジトリへのgit commitまでを行う一連の処理 |
| 取得（fetch） | 個別の1ページURLを指定して、そのページの生Markdownだけを取得・保存する処理（`sync`のサブセット） |
| ミラー（mirror） | 公式ドキュメントの内容を要約・改変せず、そのまま複製したローカルコピー。本プロダクトの中核概念 |
| 差分検知 | 前回取得時の`content_hash`と今回取得した本文のハッシュ値を比較し、変更があったファイルだけを更新対象とする仕組み |
| フロントマター（frontmatter） | 各Markdownファイル冒頭に付与するYAMLメタデータ（`source_url` / `fetched_at` / `content_hash`） |
| 索引（INDEX.md） | `content/`配下の全ファイルを一覧化した、自動生成されるドキュメント |
| 公開（publish） | `content/`配下のファイルを`knowledge-share-repo/claude-docs/`へコピーし、`metadata.yaml`を更新したうえで、実行確認を経てgit pushする処理。同期とは独立した、人手のトリガーを必要とする処理 |
| カテゴリ（category） | `knowledge-share-repo`側の分類単位。トップレベルフォルダ1つが1カテゴリに対応する。本プロダクトは`claude-docs`カテゴリを新設する |

## ビジネス用語の定義

| 用語 | 定義 |
|---|---|
| 全社ナレッジ共有リポジトリ（knowledge-share-repo） | 部門・プロジェクトを越えて全社で共有したい資料を一元管理する、既存の社内リポジトリ（`~/project_tri/knowledge-share-repo`） |
| knowledge-share-app | `knowledge-share-repo`を取り込み、非エンジニアも含めた全社員が検索・閲覧・ダウンロードできるようにする社内Webアプリ |
| 一次ユーザー | 筒井本人。Claude Codeからの参照を主目的とする |
| 二次ユーザー | `knowledge-share-app`経由で本ドキュメント群を閲覧する全社員 |

## CLI/ログ用語（UI/UX用語の代替）

本プロダクトはGUIを持たないため、「UI/UX用語」は「CLI実行時の出力・ログで統一して使う用語」と読み替える。`sync.py` / `fetch_page.py` / `publish.py`の出力は、以下の語を一貫して使う。

| 用語 | 意味 |
|---|---|
| 新規 | これまで存在しなかったファイルが今回追加された状態 |
| 更新 | 既存ファイルの`content_hash`が変化し、上書きされた状態 |
| 変更なし | ハッシュが一致し、書き込みをスキップした状態 |
| 取得失敗 | HTTPリクエストが失敗し、当該ソース・ページの処理をスキップした状態 |

## 英語・日本語対応表

| 英語 | 日本語 |
|---|---|
| source | ソース |
| sync | 同期 |
| fetch | 取得 |
| mirror | ミラー |
| publish | 公開 |
| content hash | コンテンツハッシュ |
| frontmatter | フロントマター |
| diff detection | 差分検知 |
| category | カテゴリ |

## コード上の命名規則

用語とコード上の識別子は以下のように対応させる。

| 用語 | 対応するコード上の識別子 |
|---|---|
| ソース | `sources.yaml`の各エントリ、Python側では`Source`（型/データクラス） |
| 同期 | `scripts/sync.py`、関数`sync_source()` |
| 取得（個別） | `scripts/fetch_page.py`、関数`fetch_page()` |
| 差分検知 | `content_hash`フィールド、関数`has_changed()` |
| 公開 | `scripts/publish.py`、関数`publish()` |
| フロントマター読み書き | `scripts/lib/frontmatter.py`の`read_frontmatter()` / `write_frontmatter()` |
| ページ分割 | `scripts/lib/splitter.py`の`split_pages()` |
