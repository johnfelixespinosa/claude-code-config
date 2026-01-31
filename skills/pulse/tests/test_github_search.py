"""Tests for github_search module."""

import json
import sys
import unittest
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib import github_search


class TestSearchGithub(unittest.TestCase):
    def test_mock_response_passthrough(self):
        mock = {"total_count": 0, "items": []}
        result = github_search.search_github("test", "2026-01-01", "2026-01-31", mock_response=mock)
        self.assertEqual(result, mock)


class TestParseGithubResponse(unittest.TestCase):
    def test_parses_sample_fixture(self):
        fixture_path = Path(__file__).parent.parent / "fixtures" / "github_sample.json"
        with open(fixture_path) as f:
            data = json.load(f)

        items = github_search.parse_github_response(data)

        self.assertEqual(len(items), 5)
        self.assertEqual(items[0]["id"], "GH1")
        self.assertIn("full_name", items[0])
        self.assertIn("url", items[0])
        self.assertIn("engagement", items[0])

    def test_extracts_engagement(self):
        fixture_path = Path(__file__).parent.parent / "fixtures" / "github_sample.json"
        with open(fixture_path) as f:
            data = json.load(f)

        items = github_search.parse_github_response(data)

        eng = items[0]["engagement"]
        self.assertEqual(eng["stars"], 1245)
        self.assertEqual(eng["forks"], 189)

    def test_extracts_date(self):
        fixture_path = Path(__file__).parent.parent / "fixtures" / "github_sample.json"
        with open(fixture_path) as f:
            data = json.load(f)

        items = github_search.parse_github_response(data)

        self.assertEqual(items[0]["date"], "2026-01-15")

    def test_extracts_language(self):
        fixture_path = Path(__file__).parent.parent / "fixtures" / "github_sample.json"
        with open(fixture_path) as f:
            data = json.load(f)

        items = github_search.parse_github_response(data)

        self.assertEqual(items[0]["language"], "Python")

    def test_empty_response(self):
        result = github_search.parse_github_response({"items": []})
        self.assertEqual(result, [])

    def test_error_response(self):
        result = github_search.parse_github_response({
            "message": "API rate limit exceeded",
            "errors": [{"message": "rate limit"}]
        })
        self.assertEqual(result, [])

    def test_no_full_name_skipped(self):
        data = {"items": [{"full_name": "", "html_url": "https://github.com/x/y"}]}
        result = github_search.parse_github_response(data)
        self.assertEqual(len(result), 0)

    def test_relevance_decreases_with_position(self):
        fixture_path = Path(__file__).parent.parent / "fixtures" / "github_sample.json"
        with open(fixture_path) as f:
            data = json.load(f)

        items = github_search.parse_github_response(data)

        self.assertGreater(items[0]["relevance"], items[-1]["relevance"])


class TestDepthConfig(unittest.TestCase):
    def test_quick_depth_exists(self):
        self.assertIn("quick", github_search.DEPTH_CONFIG)

    def test_default_depth_exists(self):
        self.assertIn("default", github_search.DEPTH_CONFIG)

    def test_deep_depth_exists(self):
        self.assertIn("deep", github_search.DEPTH_CONFIG)

    def test_deep_has_more_results(self):
        self.assertGreater(
            github_search.DEPTH_CONFIG["deep"],
            github_search.DEPTH_CONFIG["quick"]
        )


if __name__ == "__main__":
    unittest.main()
