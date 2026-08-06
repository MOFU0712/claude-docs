"""Markdownファイルのfrontmatter（YAML）読み書きユーティリティ。

`---`区切りの単純なYAML frontmatterのみを扱う。
"""

from __future__ import annotations

import yaml

_DELIMITER = "---\n"


def write_frontmatter(metadata: dict[str, str], body: str) -> str:
    """frontmatter辞書と本文から、frontmatter付きMarkdown文字列を生成する。"""
    yaml_block = yaml.safe_dump(metadata, allow_unicode=True, sort_keys=False)
    return f"{_DELIMITER}{yaml_block}{_DELIMITER}\n{body.strip()}\n"


def read_frontmatter(markdown_text: str) -> tuple[dict[str, str], str]:
    """frontmatter付きMarkdown文字列を、frontmatter辞書と本文に分割する。

    frontmatterが存在しないテキストを渡した場合は、空辞書と元テキストをそのまま返す。
    """
    if not markdown_text.startswith(_DELIMITER):
        return {}, markdown_text

    end = markdown_text.find(_DELIMITER, len(_DELIMITER))
    if end == -1:
        return {}, markdown_text

    yaml_block = markdown_text[len(_DELIMITER) : end]
    body = markdown_text[end + len(_DELIMITER) :].lstrip("\n")
    metadata = yaml.safe_load(yaml_block) or {}
    return metadata, body
