"""
Baseline configuration and discovery ledger for topic research.

A baseline file defines the topic, search keywords, tracks discovered sources,
and records discovery run history. Stored as YAML at
knowledge-base/baselines/{slug}.yaml.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date

import yaml


_DEFAULT_BASELINES_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "knowledge-base", "baselines"
)


@dataclass
class RunRecord:
    date: str
    keywords_used: list[str]
    found: int
    new: int
    already_collected: int


@dataclass
class SourceRecord:
    url: str
    title: str
    source_type: str
    source_id: str


@dataclass
class Baseline:
    topic: str
    title: str
    question: str
    keywords: list[str] = field(default_factory=list)
    youtube_keywords: list[str] = field(default_factory=list)
    sources: list[SourceRecord] = field(default_factory=list)
    runs: list[RunRecord] = field(default_factory=list)

    @property
    def source_urls(self) -> set[str]:
        return {s.url for s in self.sources if s.url}

    @property
    def source_ids(self) -> set[str]:
        return {s.source_id for s in self.sources if s.source_id}


def baseline_path(topic: str, baselines_dir: str | None = None) -> str:
    """Return the expected file path for a topic's baseline."""
    base = baselines_dir or _DEFAULT_BASELINES_DIR
    return os.path.join(base, f"{topic}.yaml")


def load_baseline(topic: str, baselines_dir: str | None = None) -> Baseline:
    """Load a baseline file for a topic."""
    path = baseline_path(topic, baselines_dir)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"No baseline found at {path}")

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    if not data or not isinstance(data, dict):
        raise ValueError(f"Invalid baseline file: {path}")

    sources = [
        SourceRecord(
            url=s["url"],
            title=s.get("title", ""),
            source_type=s.get("source_type", "web"),
            source_id=s.get("source_id", ""),
        )
        for s in data.get("sources", [])
    ]

    runs = [
        RunRecord(
            date=str(r["date"]),
            keywords_used=r.get("keywords_used", []),
            found=r.get("found", 0),
            new=r.get("new", 0),
            already_collected=r.get("already_collected", 0),
        )
        for r in data.get("runs", [])
    ]

    return Baseline(
        topic=data.get("topic", topic),
        title=data.get("title", ""),
        question=data.get("question", ""),
        keywords=data.get("keywords", []),
        youtube_keywords=data.get("youtube_keywords", []),
        sources=sources,
        runs=runs,
    )


def save_baseline(baseline: Baseline, baselines_dir: str | None = None) -> str:
    """Save a baseline to disk. Returns the file path."""
    path = baseline_path(baseline.topic, baselines_dir)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    data = {
        "topic": baseline.topic,
        "title": baseline.title,
        "question": baseline.question,
        "keywords": baseline.keywords,
        "youtube_keywords": baseline.youtube_keywords,
        "sources": [
            {
                "url": s.url,
                "title": s.title,
                "source_type": s.source_type,
                "source_id": s.source_id,
            }
            for s in baseline.sources
        ],
        "runs": [
            {
                "date": r.date,
                "keywords_used": r.keywords_used,
                "found": r.found,
                "new": r.new,
                "already_collected": r.already_collected,
            }
            for r in baseline.runs
        ],
    }

    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    return path


def record_run(
    baseline: Baseline,
    keywords_used: list[str],
    found: int,
    new: int,
    already_collected: int,
) -> None:
    """Add a discovery run record to the baseline."""
    baseline.runs.append(RunRecord(
        date=date.today().isoformat(),
        keywords_used=keywords_used,
        found=found,
        new=new,
        already_collected=already_collected,
    ))


def add_sources(baseline: Baseline, sources: list[SourceRecord]) -> int:
    """Add new sources to the baseline. Returns count of sources added.

    Deduplicates by URL for web sources, by source_id for URL-less sources (PDFs).
    """
    existing_urls = baseline.source_urls
    existing_ids = baseline.source_ids
    added = 0
    for s in sources:
        if s.url:
            if s.url not in existing_urls:
                baseline.sources.append(s)
                existing_urls.add(s.url)
                added += 1
        elif s.source_id:
            if s.source_id not in existing_ids:
                baseline.sources.append(s)
                existing_ids.add(s.source_id)
                added += 1
        else:
            baseline.sources.append(s)
            added += 1
    return added
