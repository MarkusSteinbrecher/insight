"""
YouTube video extractor for the Collector.

Fetches transcripts via youtube-transcript-api, groups into
paragraph-level content blocks with timestamp anchors. Extracts
video metadata via page scraping or oEmbed API.
"""

from __future__ import annotations

import hashlib
import json
import re
from urllib.parse import urlparse, parse_qs


def extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats."""
    parsed = urlparse(url)

    if parsed.hostname in ("youtu.be",):
        return parsed.path.lstrip("/")

    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]
        if parsed.path.startswith("/embed/"):
            return parsed.path.split("/")[2]
        if parsed.path.startswith("/v/"):
            return parsed.path.split("/")[2]

    return None


def fetch_transcript(video_id: str) -> list[dict]:
    """
    Fetch transcript segments for a YouTube video.

    Returns list of dicts with keys: text, start, duration.
    Prefers manually created captions over auto-generated.
    """
    from youtube_transcript_api import YouTubeTranscriptApi

    ytt_api = YouTubeTranscriptApi()
    transcript = ytt_api.fetch(video_id)

    return [
        {
            "text": snippet.text,
            "start": snippet.start,
            "duration": snippet.duration,
        }
        for snippet in transcript
    ]


def fetch_video_metadata(video_id: str) -> dict:
    """Fetch video metadata via oEmbed API."""
    import urllib.request

    oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
    try:
        with urllib.request.urlopen(oembed_url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {
                "title": data.get("title", ""),
                "author": data.get("author_name", ""),
                "channel_url": data.get("author_url", ""),
            }
    except Exception:
        return {"title": "", "author": "", "channel_url": ""}


def group_transcript_segments(segments: list[dict],
                              max_gap: float = 5.0,
                              max_duration: float = 60.0) -> list[dict]:
    """
    Group consecutive transcript segments into paragraph-level blocks.

    Groups segments until either:
    - A gap > max_gap seconds between segments
    - Accumulated duration > max_duration seconds
    - A sentence-ending punctuation followed by a pause

    Returns list of dicts with keys: text, start, end.
    """
    if not segments:
        return []

    blocks = []
    current_texts = []
    current_start = segments[0]["start"]
    current_end = segments[0]["start"] + segments[0]["duration"]

    for i, seg in enumerate(segments):
        seg_end = seg["start"] + seg["duration"]

        # Check if we should start a new block
        if current_texts:
            gap = seg["start"] - current_end
            duration_so_far = seg["start"] - current_start

            if gap > max_gap or duration_so_far > max_duration:
                # Flush current block
                blocks.append({
                    "text": " ".join(current_texts),
                    "start": current_start,
                    "end": current_end,
                })
                current_texts = []
                current_start = seg["start"]

        current_texts.append(seg["text"])
        current_end = seg_end

    # Flush remaining
    if current_texts:
        blocks.append({
            "text": " ".join(current_texts),
            "start": current_start,
            "end": current_end,
        })

    return blocks


def format_timestamp(seconds: float) -> str:
    """Format seconds as H:MM:SS or M:SS."""
    total = int(seconds)
    h = total // 3600
    m = (total % 3600) // 60
    s = total % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def extract_youtube_source(url: str, topic: str, source_id: str, graph) -> dict:
    """
    Full extraction pipeline for a YouTube video.

    Fetches transcript and metadata, groups into content blocks,
    writes Source + ContentBlock nodes to the graph.

    Returns a summary dict.
    """
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError(f"Could not extract video ID from URL: {url}")

    # Fetch metadata
    metadata = fetch_video_metadata(video_id)

    # Fetch and group transcript
    raw_segments = fetch_transcript(video_id)
    blocks = group_transcript_segments(raw_segments)

    if not blocks:
        raise ValueError(f"No transcript content for video {video_id}")

    # Compute content hash
    all_text = "\n".join(b["text"] for b in blocks)
    content_hash = hashlib.sha256(all_text.encode("utf-8")).hexdigest()

    # Canonical URL
    canonical_url = f"https://www.youtube.com/watch?v={video_id}"

    # Total duration from last segment
    total_duration = raw_segments[-1]["start"] + raw_segments[-1]["duration"] if raw_segments else 0

    # Write Source node
    graph.add_source(
        source_id=source_id,
        topic=topic,
        source_type="youtube",
        title=metadata.get("title", f"YouTube video {video_id}"),
        url=canonical_url,
        author=metadata.get("author", ""),
        content_hash=content_hash,
        metadata={
            "video_id": video_id,
            "channel_url": metadata.get("channel_url", ""),
            "duration_seconds": round(total_duration),
            "transcript_segments": len(raw_segments),
        },
    )

    # Write ContentBlock nodes
    for i, block in enumerate(blocks):
        block_id = f"{source_id}:block-{i+1:03d}"
        start_seconds = round(block["start"])
        timestamp_display = format_timestamp(block["start"])

        graph.add_content_block(
            block_id=block_id,
            source_id=source_id,
            text=block["text"],
            position=i + 1,
            location_type="timestamp",
            location_value=f"t:{start_seconds}",
            format="prose",
            section_path=f"[{timestamp_display}]",
            metadata={
                "start": round(block["start"], 1),
                "end": round(block["end"], 1),
                "timestamp_url": f"{canonical_url}&t={start_seconds}",
            },
        )

    return {
        "source_id": source_id,
        "title": metadata.get("title", ""),
        "author": metadata.get("author", ""),
        "block_count": len(blocks),
        "content_length": len(all_text),
        "duration": format_timestamp(total_duration),
        "transcript_segments": len(raw_segments),
    }
