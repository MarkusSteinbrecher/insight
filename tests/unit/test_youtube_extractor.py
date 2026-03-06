"""
Tests for insight.collector.youtube — AC-Y1 through AC-Y6.

Pure logic tests, no network access.
"""

from __future__ import annotations

import pytest

from insight.collector.youtube import extract_video_id, group_transcript_segments, format_timestamp


class TestVideoIdExtraction:
    """AC-Y1, AC-Y2"""

    def test_standard_watch_url(self):
        """AC-Y1: youtube.com/watch?v=ID"""
        assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_short_url(self):
        """AC-Y1: youtu.be/ID"""
        assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_embed_url(self):
        """AC-Y1: youtube.com/embed/ID"""
        assert extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_v_url(self):
        """AC-Y1: youtube.com/v/ID"""
        assert extract_video_id("https://www.youtube.com/v/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_mobile_url(self):
        """AC-Y1: m.youtube.com/watch?v=ID"""
        assert extract_video_id("https://m.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    def test_with_extra_params(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120&list=PLxyz"
        assert extract_video_id(url) == "dQw4w9WgXcQ"

    def test_non_youtube_url(self):
        """AC-Y2: returns None for non-YouTube URLs."""
        assert extract_video_id("https://vimeo.com/123456") is None

    def test_random_url(self):
        """AC-Y2: returns None for arbitrary URLs."""
        assert extract_video_id("https://example.com/page") is None

    def test_empty_string(self):
        assert extract_video_id("") is None


class TestTranscriptGrouping:
    """AC-Y3 through AC-Y6"""

    def test_groups_within_gap(self):
        """AC-Y3: segments within max_gap grouped into single block."""
        segments = [
            {"text": "Hello", "start": 0.0, "duration": 2.0},
            {"text": "world", "start": 2.5, "duration": 2.0},
            {"text": "today", "start": 5.0, "duration": 2.0},
        ]
        blocks = group_transcript_segments(segments, max_gap=5.0, max_duration=60.0)
        assert len(blocks) == 1
        assert blocks[0]["text"] == "Hello world today"
        assert blocks[0]["start"] == 0.0
        assert blocks[0]["end"] == 7.0

    def test_splits_on_gap(self):
        """AC-Y4: splits when gap exceeds max_gap."""
        segments = [
            {"text": "First part", "start": 0.0, "duration": 2.0},
            {"text": "Second part", "start": 10.0, "duration": 2.0},  # 8s gap
        ]
        blocks = group_transcript_segments(segments, max_gap=5.0, max_duration=60.0)
        assert len(blocks) == 2
        assert blocks[0]["text"] == "First part"
        assert blocks[1]["text"] == "Second part"

    def test_splits_on_duration(self):
        """AC-Y5: splits when accumulated duration exceeds max_duration."""
        segments = [
            {"text": f"Segment {i}", "start": i * 3.0, "duration": 2.5}
            for i in range(30)  # 30 segments, 3s apart = 90s total
        ]
        blocks = group_transcript_segments(segments, max_gap=5.0, max_duration=30.0)
        # Should split roughly every 30 seconds
        assert len(blocks) >= 3

    def test_empty_input(self):
        """AC-Y6: empty input returns empty list."""
        assert group_transcript_segments([]) == []

    def test_single_segment(self):
        segments = [{"text": "Only one", "start": 5.0, "duration": 3.0}]
        blocks = group_transcript_segments(segments)
        assert len(blocks) == 1
        assert blocks[0]["text"] == "Only one"
        assert blocks[0]["start"] == 5.0
        assert blocks[0]["end"] == 8.0

    def test_start_end_times_correct(self):
        """Start is first segment's start, end is last segment's end."""
        segments = [
            {"text": "A", "start": 10.0, "duration": 2.0},
            {"text": "B", "start": 13.0, "duration": 2.0},
        ]
        blocks = group_transcript_segments(segments, max_gap=5.0)
        assert blocks[0]["start"] == 10.0
        assert blocks[0]["end"] == 15.0


class TestTimestampFormatting:

    def test_seconds_only(self):
        assert format_timestamp(45.0) == "0:45"

    def test_minutes_and_seconds(self):
        assert format_timestamp(125.0) == "2:05"

    def test_hours(self):
        assert format_timestamp(3661.0) == "1:01:01"

    def test_zero(self):
        assert format_timestamp(0.0) == "0:00"

    def test_exact_minute(self):
        assert format_timestamp(60.0) == "1:00"
