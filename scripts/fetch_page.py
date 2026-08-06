"""個別URLを指定して1ページだけ取得・保存するエントリポイント。

sync.pyと共通の保存・差分検知・コミットロジック（scripts/lib/storage.py）を再利用する。

実行例:
    uv run python scripts/fetch_page.py https://code.claude.com/docs/en/agents
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import argparse  # noqa: E402
import logging  # noqa: E402

import requests  # noqa: E402

from scripts.lib.splitter import Page  # noqa: E402
from scripts.lib.storage import git_commit_if_changed, rebuild_index, save_page  # noqa: E402
from scripts.sync import Source, load_sources  # noqa: E402

REPO_ROOT = _REPO_ROOT
DEFAULT_TIMEOUT_SEC = 30

logger = logging.getLogger(__name__)


def resolve_source(url: str, sources: list[Source]) -> Source:
    """URLのprefixから、sources.yaml中の対応するSourceを求める。

    Args:
        url: 取得対象ページのURL。
        sources: `sources.yaml`から読み込んだSourceのリスト。

    Returns:
        `page_base_url`がurlのprefixと一致するSource。

    Raises:
        ValueError: 一致するソースが見つからない場合。
    """
    for source in sources:
        if url.startswith(source.page_base_url):
            return source
    known = ", ".join(s.name for s in sources)
    raise ValueError(
        f"URLに一致するソースがsources.yamlに見つかりません（既知のソース: {known}）: {url}"
    )


def _extract_title(body: str, fallback: str) -> str:
    """本文冒頭のMarkdown見出し（# ...）からタイトルを求める。見つからなければfallbackを返す。"""
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def fetch_page(url: str) -> Page:
    """指定URLに`.md`を付与してGETし、Pageとして返す。

    Args:
        url: 取得対象ページのURL（`.md`拡張子なし）。

    Returns:
        取得した本文を持つPage。

    Raises:
        requests.RequestException: リクエストが失敗した場合。
    """
    md_url = url if url.endswith(".md") else f"{url}.md"
    response = requests.get(md_url, timeout=DEFAULT_TIMEOUT_SEC)
    response.raise_for_status()
    body = response.text.strip()
    fallback_title = url.rstrip("/").rsplit("/", 1)[-1]
    return Page(title=_extract_title(body, fallback_title), source_url=url, body=body)


def parse_args(argv: list[str]) -> argparse.Namespace:
    """コマンドライン引数を解析する。"""
    parser = argparse.ArgumentParser(description="公式ドキュメントの個別ページを1件取得・保存する")
    parser.add_argument(
        "url",
        help="取得対象ページのURL（.md拡張子なし、例: https://code.claude.com/docs/en/agents）",
    )
    return parser.parse_args(argv)


def main() -> None:
    """URLを1件取得し、保存・差分検知・コミットを行う。"""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = parse_args(sys.argv[1:])

    sources = load_sources()
    try:
        source = resolve_source(args.url, sources)
    except ValueError as exc:
        logger.error(str(exc))
        sys.exit(1)

    try:
        page = fetch_page(args.url)
    except requests.RequestException as exc:
        logger.error("取得失敗: %s (%s)", args.url, exc)
        sys.exit(1)

    outcome = save_page(REPO_ROOT, source.name, source.page_base_url, page)
    logger.info("[%s] %s: %s", source.name, outcome.status, outcome.path)

    if outcome.status == "unchanged":
        return

    rebuild_index(REPO_ROOT)
    message = f"docs: add {args.url} via fetch_page"
    if git_commit_if_changed(REPO_ROOT, message):
        logger.info("コミットしました: %s", message)


if __name__ == "__main__":
    main()
