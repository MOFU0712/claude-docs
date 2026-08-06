"""scripts/lib/splitter.py のユニットテスト。"""

from __future__ import annotations

from pathlib import Path

from scripts.lib.splitter import split_pages

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "llms_full_sample.txt"
URL_FORMAT_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "llms_full_sample_url_format.txt"


def test_split_pages_returns_expected_count_and_fields() -> None:
    text = FIXTURE_PATH.read_text(encoding="utf-8")
    pages = split_pages(text)

    assert len(pages) == 3

    assert pages[0].title == "Getting Started"
    assert pages[0].source_url == "https://code.claude.com/docs/en/getting-started"
    assert pages[0].body.startswith("Claude Code is a command-line tool")

    assert pages[1].title == "Agents"
    assert pages[1].source_url == "https://code.claude.com/docs/en/agents"
    assert "autonomously" in pages[1].body

    assert pages[2].title == "Hooks"
    assert pages[2].source_url == "https://code.claude.com/docs/en/hooks"
    assert "PreToolUse" in pages[2].body


def test_split_pages_body_does_not_include_trailing_blank_lines() -> None:
    text = FIXTURE_PATH.read_text(encoding="utf-8")
    pages = split_pages(text)

    for page in pages:
        assert not page.body.endswith("\n\n")


def test_split_pages_empty_text_returns_empty_list() -> None:
    assert split_pages("") == []


def test_split_pages_text_without_page_header_returns_empty_list() -> None:
    assert split_pages("ただの本文で、区切りヘッダーがないテキスト。") == []


def test_split_pages_supports_url_bold_format() -> None:
    """platform.claude.com形式（`**URL:**`区切り）のllms-full.txtも分割できることを確認する。"""
    text = URL_FORMAT_FIXTURE_PATH.read_text(encoding="utf-8")
    pages = split_pages(text)

    assert len(pages) == 3

    assert pages[0].title == "Get started with Claude"
    assert pages[0].source_url == "https://platform.claude.com/docs/en/get-started"
    assert pages[0].body.startswith("Make your first API call")

    assert pages[1].title == "Intro to Claude"
    assert pages[1].source_url == "https://platform.claude.com/docs/en/intro"

    assert pages[2].title == "Classification"
    assert (
        pages[2].source_url
        == "https://platform.claude.com/docs/en/build-with-claude/classification"
    )
    assert "classify text" in pages[2].body
