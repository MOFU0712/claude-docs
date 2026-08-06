"""llms-full.txt を1ページ単位の Page に分割するロジック。

Mintlifyベースの llms-full.txt は、サイトによって以下の2種類のページ区切り形式が使われる。

    # タイトル
    Source: <URL>

    <本文>

    # タイトル

    **URL:** <URL>

    <本文>

このモジュールは、どちらの形式で連結されたテキストも同じ Page オブジェクトのリストに分割する。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# 「# タイトル」直後に「Source: URL」または「**URL:** URL」が続く行をページ区切りとみなす。
_PAGE_HEADER_RE = re.compile(
    r"^# (?P<title>.+)\n"
    r"(?:Source: (?P<url_a>\S+)\n+|\n\*\*URL:\*\* (?P<url_b>\S+)\n+)",
    re.MULTILINE,
)


@dataclass
class Page:
    """分割された1ページ分のデータ。

    Attributes:
        title: ページタイトル。
        source_url: 取得元の公式ページURL。
        body: 区切りヘッダーを除いた本文（要約・改変なし）。
    """

    title: str
    source_url: str
    body: str


def split_pages(full_dump_text: str) -> list[Page]:
    """llms-full.txt形式のテキストをページ単位のPageリストに分割する。

    本文は要約・改変せず、区切りヘッダーを除いた部分をそのまま保持する。

    Args:
        full_dump_text: llms-full.txtの全文（複数ページが連結されたテキスト）。

    Returns:
        検出順のPageのリスト。区切りヘッダーが1件も見つからない場合は空リスト。
    """
    matches = list(_PAGE_HEADER_RE.finditer(full_dump_text))
    pages: list[Page] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(full_dump_text)
        body = full_dump_text[start:end].strip("\n")
        source_url = match.group("url_a") or match.group("url_b") or ""
        pages.append(
            Page(
                title=match.group("title").strip(),
                source_url=source_url.strip(),
                body=body,
            )
        )
    return pages
