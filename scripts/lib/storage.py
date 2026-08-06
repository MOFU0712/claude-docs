"""ページの保存・差分検知・INDEX.md再生成・gitコミットを行う共通処理。

`sync.py` と `fetch_page.py` の両方から利用される。
"""

from __future__ import annotations

import hashlib
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from scripts.lib.frontmatter import read_frontmatter, write_frontmatter
from scripts.lib.splitter import Page

CONTENT_DIR_NAME = "content"
INDEX_FILE_NAME = "INDEX.md"


def content_hash(body: str) -> str:
    """本文のsha256ハッシュを求める（差分検知に使用）。"""
    return hashlib.sha256(body.strip().encode("utf-8")).hexdigest()


def page_path(repo_root: Path, source_name: str, page_base_url: str, source_url: str) -> Path:
    """source_urlから保存先パス content/<source_name>/<相対パス>.md を求める。

    例: page_base_url=".../docs/en", source_url=".../docs/en/agents"
        -> content/<source_name>/agents.md
    """
    relative = source_url
    if relative.startswith(page_base_url):
        relative = relative[len(page_base_url) :]
    relative = relative.lstrip("/")
    if not relative:
        relative = "index"
    if not relative.endswith(".md"):
        relative = f"{relative}.md"
    return repo_root / CONTENT_DIR_NAME / source_name / relative


def has_changed(path: Path, new_hash: str) -> bool:
    """保存先ファイルが存在しない、または既存のcontent_hashと異なる場合Trueを返す。"""
    if not path.exists():
        return True
    existing_metadata, _ = read_frontmatter(path.read_text(encoding="utf-8"))
    return existing_metadata.get("content_hash") != new_hash


@dataclass
class SaveOutcome:
    """1ページ保存処理の結果。"""

    path: Path
    status: str  # "added" | "updated" | "unchanged"


def save_page(repo_root: Path, source_name: str, page_base_url: str, page: Page) -> SaveOutcome:
    """Pageを差分検知しつつcontent/配下に保存する。

    内容に変更がない場合は書き込みを行わず、statusを"unchanged"として返す。
    """
    path = page_path(repo_root, source_name, page_base_url, page.source_url)
    new_hash = content_hash(page.body)

    if not has_changed(path, new_hash):
        return SaveOutcome(path=path, status="unchanged")

    status = "updated" if path.exists() else "added"
    metadata = {
        "source_url": page.source_url,
        "fetched_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "content_hash": new_hash,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(write_frontmatter(metadata, page.body), encoding="utf-8")
    return SaveOutcome(path=path, status=status)


def rebuild_index(repo_root: Path) -> None:
    """content/配下の全ファイルから、ソースごとにグループ化したINDEX.mdを再生成する。"""
    content_dir = repo_root / CONTENT_DIR_NAME
    lines = ["# INDEX", "", "content/配下の同期済みドキュメント一覧（自動生成）。", ""]

    if content_dir.exists():
        for source_dir in sorted(p for p in content_dir.iterdir() if p.is_dir()):
            lines.append(f"## {source_dir.name}")
            lines.append("")
            for md_path in sorted(source_dir.rglob("*.md")):
                metadata, _ = read_frontmatter(md_path.read_text(encoding="utf-8"))
                fetched_at = metadata.get("fetched_at", "")
                relative = md_path.relative_to(repo_root).as_posix()
                lines.append(f"- [{md_path.stem}]({relative}) (fetched_at: {fetched_at})")
            lines.append("")

    (repo_root / INDEX_FILE_NAME).write_text("\n".join(lines).rstrip("\n") + "\n", encoding="utf-8")


def git_commit_if_changed(repo_root: Path, message: str) -> bool:
    """git add -A したうえで、差分があればcommitする。差分がなければFalseを返す。"""
    subprocess.run(["git", "add", "-A"], cwd=repo_root, check=True)
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    if not status.stdout.strip():
        return False
    subprocess.run(["git", "commit", "-m", message], cwd=repo_root, check=True)
    return True
