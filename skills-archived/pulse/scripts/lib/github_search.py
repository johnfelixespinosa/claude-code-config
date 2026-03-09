"""GitHub Search API client for pulse skill."""

import re
import sys
import time
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from . import http

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"

# Depth configurations: per_page
DEPTH_CONFIG = {
    "quick": 10,
    "default": 25,
    "deep": 50,
}


def _log_error(msg: str):
    """Log error to stderr."""
    sys.stderr.write(f"[GITHUB ERROR] {msg}\n")
    sys.stderr.flush()


def _log_info(msg: str):
    """Log info to stderr."""
    sys.stderr.write(f"[GITHUB] {msg}\n")
    sys.stderr.flush()


def search_github(
    topic: str,
    from_date: str,
    to_date: str,
    depth: str = "default",
    mock_response: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Search GitHub for relevant repositories.

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

    per_page = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["default"])

    # GitHub search query: topic + created date filter
    query = f"{topic} created:>{from_date}"
    url = f"{GITHUB_SEARCH_URL}?q={quote(query)}&sort=stars&order=desc&per_page={per_page}"

    headers = {
        "Accept": "application/vnd.github.v3+json",
    }

    return http.get(url, headers=headers, timeout=30)


def parse_github_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse GitHub search response to extract repository items.

    Args:
        response: Raw API response

    Returns:
        List of item dicts
    """
    items = []

    if "message" in response and "errors" in response:
        _log_error(f"GitHub API error: {response.get('message', 'Unknown error')}")
        return items

    repos = response.get("items", [])

    for i, repo in enumerate(repos):
        if not isinstance(repo, dict):
            continue

        full_name = repo.get("full_name", "")
        if not full_name:
            continue

        # Parse date from created_at
        created_at = repo.get("created_at", "")
        date_str = None
        if created_at and len(created_at) >= 10:
            date_str = created_at[:10]  # YYYY-MM-DD from ISO 8601

        # Extract engagement
        stars = repo.get("stargazers_count")
        forks = repo.get("forks_count")

        # Build description
        description = str(repo.get("description", "") or "").strip()[:300]
        language = repo.get("language", "")

        # Compute relevance heuristic
        relevance = max(0.3, min(1.0, 0.95 - (i * 0.02)))

        item = {
            "id": f"GH{i+1}",
            "full_name": full_name,
            "description": description,
            "url": repo.get("html_url", ""),
            "language": language or "",
            "date": date_str,
            "engagement": {
                "stars": int(stars) if stars is not None else None,
                "forks": int(forks) if forks is not None else None,
            },
            "why_relevant": f"GitHub repo related to {full_name.split('/')[-1]}",
            "relevance": relevance,
        }

        items.append(item)

    return items
