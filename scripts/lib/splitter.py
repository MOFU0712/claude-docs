"""llms-full.txt を1ページ単位の Page に分割するロジック。

各ソースの llms-full.txt は、以下の形式でページが連続する構成になっている。

    # タイトル
    Source: <URL>

    <本文>

このモジュールは、その連結テキストをページ単位の Page オブジェクトに分割する。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_PAGE_HEADER_RE = re.compile(
    r"^# (?P<title>.+)\nSource: (?P<source_url>\S+)\n+",
    re.MULTILINE,
)


@dataclass
class Page:
    """分割された1ページ分のデータ。"""

    title: str
    source_url: str
    body: str


def split_pages(full_dump_text: str) -> list[Page]:
    """llms-full.txt形式のテキストをページ単位のPageリストに分割する。

    本文は要約・改変せず、区切りヘッダーを除いた部分をそのまま保持する。
    """
    matches = list(_PAGE_HEADER_RE.finditer(full_dump_text))
    pages: list[Page] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(full_dump_text)
        body = full_dump_text[start:end].strip("\n")
        pages.append(
            Page(
                title=match.group("title").strip(),
                source_url=match.group("source_url").strip(),
                body=body,
            )
        )
    return pages
