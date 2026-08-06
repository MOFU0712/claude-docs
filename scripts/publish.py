"""content/をknowledge-share-repo/claude-docs/へ公開するエントリポイント。

同期処理（sync.py / fetch_page.py）とは独立した、人手のトリガーを必要とする処理。
差分をプレビュー表示し、実行確認を得たときのみコピー・metadata.yaml更新・git commit・pushを行う。
エラー発生時は即座に中断し、knowledge-share-repo側に中途半端な変更を残さない。

実行例:
    uv run python scripts/publish.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import argparse  # noqa: E402
import subprocess  # noqa: E402
from dataclasses import dataclass  # noqa: E402

import yaml  # noqa: E402

from scripts.lib.frontmatter import read_frontmatter  # noqa: E402

REPO_ROOT = _REPO_ROOT
DEFAULT_CONTENT_DIR = REPO_ROOT / "content"
DEFAULT_TARGET_DIR = Path.home() / "project_tri" / "knowledge-share-repo" / "claude-docs"

_METADATA_HEADER = (
    "# このカテゴリに置く資料を1エントリずつ記載する。\n"
    "# 必須項目: path, title, description / 任意項目: tags, updated_at, owner\n"
    "#\n"
    "# このファイルは scripts/publish.py が自動生成・更新する。\n"
)


@dataclass
class DiffEntry:
    """公開対象1ファイルの差分状態。

    Attributes:
        relative_path: content/からの相対パス（knowledge-share-repo/claude-docs/内でも同一パス）。
        status: "added" | "updated" | "unchanged" のいずれか。
    """

    relative_path: str
    status: str


def compute_diff(content_dir: Path, target_dir: Path) -> list[DiffEntry]:
    """content/ と target_dir の内容を比較し、差分エントリのリストを返す。

    Args:
        content_dir: 比較元（claude-docsリポジトリのcontent/）。
        target_dir: 比較先（knowledge-share-repo/claude-docs/）。

    Returns:
        content_dir配下の全Markdownファイルについての差分エントリのリスト。
    """
    entries: list[DiffEntry] = []
    if not content_dir.exists():
        return entries

    for src_path in sorted(content_dir.rglob("*.md")):
        relative = src_path.relative_to(content_dir).as_posix()
        dst_path = target_dir / relative
        if not dst_path.exists():
            entries.append(DiffEntry(relative_path=relative, status="added"))
        elif src_path.read_text(encoding="utf-8") != dst_path.read_text(encoding="utf-8"):
            entries.append(DiffEntry(relative_path=relative, status="updated"))
        else:
            entries.append(DiffEntry(relative_path=relative, status="unchanged"))
    return entries


def print_preview(entries: list[DiffEntry]) -> None:
    """差分エントリをCLIにプレビュー表示する。

    Args:
        entries: compute_diff()の結果。
    """
    changed = [e for e in entries if e.status != "unchanged"]
    if not changed:
        print("公開対象の変更はありません。")
        return

    print(f"公開プレビュー（{len(changed)}件の変更）:")
    labels = {"added": "新規", "updated": "更新"}
    for entry in changed:
        print(f"  [{labels[entry.status]}] {entry.relative_path}")


def extract_title(md_path: Path) -> str:
    """本文冒頭のMarkdown見出し（# ...）からタイトルを求める。見つからなければファイル名を返す。

    Args:
        md_path: 対象Markdownファイルのパス。

    Returns:
        抽出したタイトル文字列。
    """
    _, body = read_frontmatter(md_path.read_text(encoding="utf-8"))
    for line in body.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return md_path.stem


def apply_changes(
    content_dir: Path, target_dir: Path, entries: list[DiffEntry]
) -> list[dict[str, object]]:
    """差分のあるファイルをコピーし、metadata.yamlを更新する。

    Args:
        content_dir: コピー元ディレクトリ（content/）。
        target_dir: コピー先ディレクトリ（knowledge-share-repo/claude-docs/）。
        entries: compute_diff()の結果。

    Returns:
        更新後のmetadata.yaml全エントリのリスト。
    """
    metadata_path = target_dir / "metadata.yaml"
    existing: dict[str, dict[str, object]] = {}
    if metadata_path.exists():
        raw = yaml.safe_load(metadata_path.read_text(encoding="utf-8")) or []
        for item in raw:
            existing[str(item["path"])] = item

    for entry in entries:
        if entry.status == "unchanged":
            continue
        src_path = content_dir / entry.relative_path
        dst_path = target_dir / entry.relative_path
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        dst_path.write_text(src_path.read_text(encoding="utf-8"), encoding="utf-8")

        fm_metadata, _ = read_frontmatter(src_path.read_text(encoding="utf-8"))
        source_name = Path(entry.relative_path).parts[0]
        fetched_at = fm_metadata.get("fetched_at", "")
        existing[entry.relative_path] = {
            "path": entry.relative_path,
            "title": extract_title(src_path),
            "description": "Anthropic公式ドキュメントのミラー",
            "tags": [source_name],
            "updated_at": fetched_at[:10] if fetched_at else "",
            "owner": "ai-lab",
        }

    files = [existing[key] for key in sorted(existing)]
    metadata_path.write_text(
        _METADATA_HEADER + yaml.safe_dump(files, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return files


def git_commit_and_push(target_repo_root: Path, message: str) -> None:
    """target_repo_root配下でgit add/commit/pushを行う。

    Args:
        target_repo_root: knowledge-share-repoのルートパス。
        message: コミットメッセージ。

    Raises:
        subprocess.CalledProcessError: git操作のいずれかが失敗した場合。
    """
    subprocess.run(["git", "add", "-A"], cwd=target_repo_root, check=True)
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=target_repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    if not status.stdout.strip():
        return
    subprocess.run(["git", "commit", "-m", message], cwd=target_repo_root, check=True)
    try:
        subprocess.run(["git", "push"], cwd=target_repo_root, check=True)
    except subprocess.CalledProcessError:
        # pushが失敗した場合、ローカルにのみcommitが残る中途半端な状態を避けるため
        # コミット前の状態にロールバックしてから呼び出し元に例外を伝播させる。
        subprocess.run(["git", "reset", "--hard", "HEAD~1"], cwd=target_repo_root, check=True)
        raise


def ask_confirmation() -> bool:
    """標準入力からy/nの確認を得る。

    Returns:
        入力が"y"（大文字小文字を問わない）であればTrue。
    """
    answer = input("上記の内容でknowledge-share-repoへ公開しますか？ [y/N]: ").strip().lower()
    return answer == "y"


def parse_args(argv: list[str]) -> argparse.Namespace:
    """コマンドライン引数を解析する。"""
    parser = argparse.ArgumentParser(
        description="content/をknowledge-share-repo/claude-docs/へ公開する"
    )
    parser.add_argument("--content-dir", type=Path, default=DEFAULT_CONTENT_DIR)
    parser.add_argument("--target-dir", type=Path, default=DEFAULT_TARGET_DIR)
    parser.add_argument(
        "--target-repo-root",
        type=Path,
        default=None,
        help="省略時はtarget-dirの1階層上（knowledge-share-repo直下）とみなす",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="確認プロンプトをスキップする（動作確認用。通常の対話実行では使用しない）",
    )
    return parser.parse_args(argv)


def main() -> None:
    """差分プレビュー→確認→コピー・metadata.yaml更新→commit・pushを行う。"""
    args = parse_args(sys.argv[1:])
    target_repo_root = args.target_repo_root or args.target_dir.parent

    entries = compute_diff(args.content_dir, args.target_dir)
    print_preview(entries)

    changed = [e for e in entries if e.status != "unchanged"]
    if not changed:
        return

    if not (args.yes or ask_confirmation()):
        print("中断しました（確認が得られなかったため、変更は行われていません）。")
        return

    try:
        files = apply_changes(args.content_dir, args.target_dir, entries)
        message = f"docs: publish claude-docs ({len(changed)} files updated)"
        git_commit_and_push(target_repo_root, message)
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"エラーが発生したため中断しました: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"公開が完了しました（metadata.yamlのエントリ数: {len(files)}）。")


if __name__ == "__main__":
    main()
