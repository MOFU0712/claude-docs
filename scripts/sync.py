"""sources.yamlに定義された全ソースを同期するエントリポイント。

各ソースについて「取得 → 分割 → 差分検知 → 保存」を行い、INDEX.mdを再生成したうえで
claude-docsリポジトリにgit commitする。1ソースの取得失敗は他ソースの処理を止めない。
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import requests
import yaml

from scripts.lib.splitter import Page, split_pages
from scripts.lib.storage import git_commit_if_changed, rebuild_index, save_page

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCES_FILE = REPO_ROOT / "sources.yaml"
DEFAULT_TIMEOUT_SEC = 30

logger = logging.getLogger(__name__)


@dataclass
class Source:
    """sources.yamlの1エントリ。"""

    name: str
    full_dump: str
    page_base_url: str


@dataclass
class SyncResult:
    """1ソース分の同期結果サマリー。"""

    source_name: str
    added: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    unchanged_count: int = 0
    failed: list[str] = field(default_factory=list)


def load_sources(path: Path = SOURCES_FILE) -> list[Source]:
    """sources.yamlを読み込み、Sourceのリストを返す。"""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return [Source(**entry) for entry in raw["sources"]]


def fetch_text(url: str) -> str:
    """指定URLをGETし、本文テキストを返す。"""
    response = requests.get(url, timeout=DEFAULT_TIMEOUT_SEC)
    response.raise_for_status()
    return response.text


def sync_source(repo_root: Path, source: Source) -> SyncResult:
    """1ソースの取得→分割→差分検知→保存を行う。"""
    result = SyncResult(source_name=source.name)
    try:
        full_dump_text = fetch_text(source.full_dump)
    except requests.RequestException as exc:
        logger.warning("ソース '%s' の取得に失敗しました: %s", source.name, exc)
        result.failed.append(source.full_dump)
        return result

    pages: list[Page] = split_pages(full_dump_text)
    for page in pages:
        try:
            outcome = save_page(repo_root, source.name, source.page_base_url, page)
        except OSError as exc:
            logger.warning("ページ '%s' の保存に失敗しました: %s", page.source_url, exc)
            result.failed.append(page.source_url)
            continue

        if outcome.status == "added":
            result.added.append(str(outcome.path))
        elif outcome.status == "updated":
            result.updated.append(str(outcome.path))
        else:
            result.unchanged_count += 1

    return result


def log_summary(results: list[SyncResult]) -> None:
    """全ソースの同期結果サマリー（新規/更新/変更なし/取得失敗）をログ出力する。"""
    for result in results:
        logger.info(
            "[%s] 新規:%d 更新:%d 変更なし:%d 取得失敗:%d",
            result.source_name,
            len(result.added),
            len(result.updated),
            result.unchanged_count,
            len(result.failed),
        )
        for failed_url in result.failed:
            logger.warning("  取得失敗: %s", failed_url)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    sources = load_sources()
    results = [sync_source(REPO_ROOT, source) for source in sources]
    log_summary(results)

    rebuild_index(REPO_ROOT)

    total_changed = sum(len(r.added) + len(r.updated) for r in results)
    source_names = ", ".join(r.source_name for r in results)
    today = date.today().isoformat()
    message = f"docs: sync {total_changed} files from {source_names} ({today})"
    if git_commit_if_changed(REPO_ROOT, message):
        logger.info("コミットしました: %s", message)
    else:
        logger.info("変更がないため、コミットはスキップされました")

    if any(r.failed for r in results):
        sys.exit(1)


if __name__ == "__main__":
    main()
