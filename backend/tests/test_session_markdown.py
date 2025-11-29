"""Unit tests for session markdown rendering."""

from app.schemas.session import (
    SessionLogSection,
    SessionMetric,
    SessionProcessingLogRequest,
    SessionTimelineEntry,
)
from app.services.session import render_processing_markdown


def test_render_processing_markdown_builds_sections():
    payload = SessionProcessingLogRequest(
        title="第1回 AIログ",
        summary="- 挨拶は明瞭\n- 声量は安定",
        metrics=[SessionMetric(label="話速", value=180, unit="wpm", comment="理想範囲内")],
        sections=[
            SessionLogSection(
                heading="音声分析",
                body="話速は安定しており、フィラーは少なめでした。",
            )
        ],
        timeline=[SessionTimelineEntry(timestamp=12.5, label="自己紹介", detail="声量◎")],
    )

    markdown = render_processing_markdown(payload)

    assert "# 第1回 AIログ" in markdown
    assert "|話速|180wpm|理想範囲内|" in markdown
    assert "## 音声分析" in markdown
    assert "12.5" in markdown


def test_render_processing_markdown_respects_raw_markdown():
    payload = SessionProcessingLogRequest(
        title="ignored",
        summary="ignored",
        raw_markdown="# 既存ログ\n本文",
    )

    markdown = render_processing_markdown(payload)

    assert markdown.startswith("# 既存ログ")
    assert "本文" in markdown
