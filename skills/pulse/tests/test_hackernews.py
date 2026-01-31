"""Tests for hackernews module."""

import json
import sys
import unittest
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib import hackernews


class TestDateToUnix(unittest.TestCase):
    def test_converts_date_string(self):
        result = hackernews._date_to_unix("2026-01-15")
        self.assertIsInstance(result, int)
        self.assertGreater(result, 0)

    def test_different_dates_give_different_timestamps(self):
        t1 = hackernews._date_to_unix("2026-01-01")
        t2 = hackernews._date_to_unix("2026-01-15")
        self.assertGreater(t2, t1)


class TestSearchHn(unittest.TestCase):
    def test_mock_response_passthrough(self):
        mock = {"hits": [], "nbHits": 0}
        result = hackernews.search_hn("test", "2026-01-01", "2026-01-31", mock_response=mock)
        self.assertEqual(result, mock)


class TestParseHnResponse(unittest.TestCase):
    def test_parses_sample_fixture(self):
        fixture_path = Path(__file__).parent.parent / "fixtures" / "hn_sample.json"
        with open(fixture_path) as f:
            data = json.load(f)

        items = hackernews.parse_hn_response(data)

        self.assertEqual(len(items), 5)
        self.assertEqual(items[0]["id"], "HN1")
        self.assertIn("title", items[0])
        self.assertIn("url", items[0])
        self.assertIn("engagement", items[0])

    def test_extracts_engagement(self):
        fixture_path = Path(__file__).parent.parent / "fixtures" / "hn_sample.json"
        with open(fixture_path) as f:
            data = json.load(f)

        items = hackernews.parse_hn_response(data)

        eng = items[0]["engagement"]
        self.assertEqual(eng["points"], 342)
        self.assertEqual(eng["num_comments"], 87)

    def test_extracts_date(self):
        fixture_path = Path(__file__).parent.parent / "fixtures" / "hn_sample.json"
        with open(fixture_path) as f:
            data = json.load(f)

        items = hackernews.parse_hn_response(data)

        # First item has created_at_i = 1737936000 = 2025-01-27 (approximate)
        self.assertIsNotNone(items[0]["date"])
        self.assertRegex(items[0]["date"], r'^\d{4}-\d{2}-\d{2}$')

    def test_empty_response(self):
        result = hackernews.parse_hn_response({})
        self.assertEqual(result, [])

    def test_error_response(self):
        result = hackernews.parse_hn_response({"error": "Rate limit exceeded"})
        self.assertEqual(result, [])

    def test_no_title_skipped(self):
        data = {"hits": [{"objectID": "123", "title": "", "url": ""}]}
        result = hackernews.parse_hn_response(data)
        self.assertEqual(len(result), 0)

    def test_relevance_decreases_with_position(self):
        fixture_path = Path(__file__).parent.parent / "fixtures" / "hn_sample.json"
        with open(fixture_path) as f:
            data = json.load(f)

        items = hackernews.parse_hn_response(data)

        self.assertGreater(items[0]["relevance"], items[-1]["relevance"])


class TestDepthConfig(unittest.TestCase):
    def test_quick_depth_exists(self):
        self.assertIn("quick", hackernews.DEPTH_CONFIG)

    def test_default_depth_exists(self):
        self.assertIn("default", hackernews.DEPTH_CONFIG)

    def test_deep_depth_exists(self):
        self.assertIn("deep", hackernews.DEPTH_CONFIG)

    def test_deep_has_more_hits(self):
        self.assertGreater(
            hackernews.DEPTH_CONFIG["deep"],
            hackernews.DEPTH_CONFIG["quick"]
        )


if __name__ == "__main__":
    unittest.main()
