"""
Discovery module for the Collector.

Checks candidate URLs against the source registry in the graph.
No fetching — graph lookup only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse, urlencode, parse_qs


# Tracking parameters to strip during normalization
_TRACKING_PARAMS = {"utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "ref", "source"}


@dataclass
class DiscoveryResult:
    new: list[str]
    existing: list[str]
    total: int


def normalize_url(url: str) -> str:
    """
    Normalize a URL for deduplication comparison.

    - Lowercase scheme and hostname
    - Strip www. prefix
    - Remove trailing slash
    - Remove known tracking parameters
    - Preserve path, query (minus tracking), and fragment
    """
    parsed = urlparse(url)

    scheme = parsed.scheme.lower() or "https"
    hostname = (parsed.hostname or "").lower()
    hostname = re.sub(r"^www\.", "", hostname)

    path = parsed.path.rstrip("/")

    # Filter out tracking params
    query_params = parse_qs(parsed.query, keep_blank_values=True)
    filtered = {k: v for k, v in query_params.items() if k.lower() not in _TRACKING_PARAMS}

    query = urlencode(filtered, doseq=True) if filtered else ""

    # Reconstruct
    port = f":{parsed.port}" if parsed.port and parsed.port not in (80, 443) else ""
    normalized = f"{scheme}://{hostname}{port}{path}"
    if query:
        normalized += f"?{query}"

    return normalized


def detect_source_type(url: str) -> str:
    """Detect the source type from a URL."""
    lower = url.lower()
    if "youtube.com/watch" in lower or "youtu.be/" in lower:
        return "youtube"
    if lower.endswith(".pdf"):
        return "pdf"
    return "web"


def check_urls(urls: list[str], topic: str, graph) -> DiscoveryResult:
    """
    Check candidate URLs against the source registry.

    Returns a DiscoveryResult with new and existing URL lists.
    URL comparison uses normalized forms.
    """
    existing_urls = graph.get_existing_urls(topic)
    normalized_existing = {normalize_url(u) for u in existing_urls}

    new = []
    existing = []

    for url in urls:
        if normalize_url(url) in normalized_existing:
            existing.append(url)
        else:
            new.append(url)

    return DiscoveryResult(
        new=new,
        existing=existing,
        total=len(new) + len(existing),
    )
