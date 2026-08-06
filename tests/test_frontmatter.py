"""scripts/lib/frontmatter.py のユニットテスト。"""

from __future__ import annotations

from scripts.lib.frontmatter import read_frontmatter, write_frontmatter


def test_write_then_read_frontmatter_roundtrip() -> None:
    metadata = {
        "source_url": "https://code.claude.com/docs/en/agents",
        "fetched_at": "2026-08-06T00:00:00+00:00",
        "content_hash": "abc123",
    }
    body = "# Agents\n\nAgents allow Claude Code to work autonomously."

    markdown = write_frontmatter(metadata, body)
    parsed_metadata, parsed_body = read_frontmatter(markdown)

    assert parsed_metadata == metadata
    assert parsed_body == body + "\n"


def test_write_frontmatter_starts_with_delimiter() -> None:
    markdown = write_frontmatter({"source_url": "https://example.com"}, "本文")
    assert markdown.startswith("---\n")


def test_read_frontmatter_without_frontmatter_returns_empty_dict() -> None:
    text = "# No frontmatter here\n\nJust a plain markdown file."
    metadata, body = read_frontmatter(text)

    assert metadata == {}
    assert body == text


def test_read_frontmatter_with_unclosed_delimiter_returns_empty_dict() -> None:
    text = "---\nsource_url: https://example.com\n\n本文（閉じ区切りなし）"
    metadata, body = read_frontmatter(text)

    assert metadata == {}
    assert body == text
