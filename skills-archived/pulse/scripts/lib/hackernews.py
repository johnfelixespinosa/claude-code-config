"""HackerNews Algolia API client for pulse skill."""

import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from . import http

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search"

# Depth configurations: hitsPerPage
DEPTH_CONFIG = {
    "quick": 10,
    "default": 25,
    "deep": 50,
}


def _log_error(msg: str):
    """Log error to stderr."""
    sys.stderr.write(f"[HN ERROR] {msg}\n")
    sys.stderr.flush()


def _log_info(msg: str):
    """Log info to stderr."""
    sys.stderr.write(f"[HN] {msg}\n")
    sys.stderr.flush()


def _date_to_unix(date_str: str) -> int:
    """Convert YYYY-MM-DD to Unix timestamp."""
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def search_hn(
    topic: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
    mock_response: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Search HackerNews for relevant stories using Algolia API.

    Args:
        topic: Search topic
        from_date: Start date (YYYY-MM-DD)
        to_date: End date (YYYY-MM-DD)
        depth: Research depth - "quick", "default", or "deep"
        mock_response: Mock response for testing

    Returns:
        Raw API response
    """
    if mock_response is not None:
        return mock_response

    hits_per_page = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["default"])

    from_unix = _date_to_unix(from_date)
    to_unix = _date_to_unix(to_date) + 86400  # Include the end date

    url = (
        f"{HN_SEARCH_URL}"
        f"?query={quote(topic)}"
        f"&tags=story"
        f"&numericFilters=created_at_i>{from_unix},created_at_i<{to_unix}"
        f"&hitsPerPage={hits_per_page}"
    )

    return http.get(url, timeout=30)


def parse_hn_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse HN Algolia response to extract story items.

    Args:
        response: Raw API response

    Returns:
        List of item dicts
    """
    items = []

    if "error" in response and response["error"]:
        _log_error(f"HN API error: {response['error']}")
        return items

    hits = response.get("hits", [])

    for i, hit in enumerate(hits):
        if not isinstance(hit, dict):
            continue

        title = hit.get("title", "")
        if not title:
            continue

        # Build URL
        object_id = hit.get("objectID", "")
        story_url = hit.get("url", "")
        hn_url = f"https://news.ycombinator.com/item?id={object_id}" if object_id else ""

        # Parse date from created_at_i (unix timestamp)
        created_at_i = hit.get("created_at_i")
        date_str = None
        if created_at_i:
            try:
                dt = datetime.fromtimestamp(int(created_at_i), tz=timezone.utc)
                date_str = dt.strftime("%Y-%m-%d")
            except (ValueError, TypeError, OSError):
                pass

        # Extract engagement
        points = hit.get("points")
        num_comments = hit.get("num_comments")

        # Compute relevance heuristic based on position in results
        # Algolia returns results sorted by relevance
        relevance = max(0.3, min(1.0, 0.95 - (i * 0.02)))

        item = {
            "id": f"HN{i+1}",
            "title": str(title).strip()[:200],
            "url": hn_url,
            "story_url": story_url or "",
            "author": str(hit.get("author", "")).strip(),
            "date": date_str,
            "engagement": {
                "points": int(points) if points is not None else None,
                "num_comments": int(num_comments) if num_comments is not None else None,
            },
            "why_relevant": f"HN story: {title[:80]}",
            "relevance": relevance,
        }

        items.append(item)

    return items
