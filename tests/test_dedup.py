import pytest
import pandas as pd
import hashlib
from quality.dedup import (
    deduplicate_exact,
    deduplicate_semantic_lsh,
    canonicalize_url,
    normalize_title,
    fuzzy_hash,
    deduplicate_by_fuzzy_hash,
)


class TestCanonicalizeUrl:
    def test_remove_trailing_slash(self):
        assert canonicalize_url("https://example.com/page/") == "https://example.com/page"

    def test_remove_www(self):
        assert canonicalize_url("https://www.example.com/page") == "https://example.com/page"

    def test_lowercase(self):
        assert canonicalize_url("HTTPS://Example.COM/Page") == "https://example.com/page"

    def test_remove_utm(self):
        result = canonicalize_url("https://example.com/page?utm_source=google&id=123")
        assert "utm_source" not in result
        assert "id=123" in result


class TestNormalizeTitle:
    def test_lowercase(self):
        assert normalize_title("Hello World") == "hello world"

    def test_strip_whitespace(self):
        assert normalize_title("  hello world  ") == "hello world"

    def test_collapse_spaces(self):
        assert normalize_title("hello   world") == "hello world"

    def test_remove_special_chars(self):
        result = normalize_title("Breaking: News! [Update]")
        assert ":" not in result
        assert "!" not in result
        assert "[" not in result
        assert "]" not in result


class TestFuzzyHash:
    def test_deterministic(self):
        assert fuzzy_hash("hello world") == fuzzy_hash("hello world")

    def test_shuffle(self):
        assert fuzzy_hash("hello world") == fuzzy_hash("world hello")

    def test_different_inputs(self):
        assert fuzzy_hash("hello world") != fuzzy_hash("hello there")


class TestDeduplicateExact:
    def test_removes_duplicates(self):
        df = pd.DataFrame({
            "title": ["hello", "hello", "world"],
            "text": ["a", "b", "c"],
        })
        result = deduplicate_exact(df)
        assert len(result) == 2

    def test_preserves_unique(self):
        df = pd.DataFrame({
            "title": ["hello", "world", "foo"],
            "text": ["a", "b", "c"],
        })
        result = deduplicate_exact(df)
        assert len(result) == 3

    def test_empty_df(self):
        df = pd.DataFrame({"title": [], "text": []})
        result = deduplicate_exact(df)
        assert len(result) == 0


class TestDeduplicateByFuzzyHash:
    def test_removes_similar(self):
        df = pd.DataFrame({
            "title": ["a", "b"],
            "text": [
                "The quick brown fox jumps over the lazy dog",
                "The quick brown fox jumps over the lazy dog today",
            ],
        })
        result = deduplicate_by_fuzzy_hash(df)
        assert len(result) <= 1

    def test_preserves_different(self):
        df = pd.DataFrame({
            "title": ["a", "b"],
            "text": [
                "The quick brown fox",
                "Completely different article content here",
            ],
        })
        result = deduplicate_by_fuzzy_hash(df)
        assert len(result) == 2


class TestDeduplicateSemanticLsh:
    def test_removes_duplicates(self):
        df = pd.DataFrame({
            "title": ["a", "b"],
            "text": ["hello world", "hello world"],
        })
        result = deduplicate_semantic_lsh(df, threshold=0.9)
        assert len(result) == 1

    def test_preserves_unique(self):
        df = pd.DataFrame({
            "title": ["a", "b"],
            "text": ["hello world", "completely different"],
        })
        result = deduplicate_semantic_lsh(df, threshold=0.9)
        assert len(result) == 2

    def test_empty_df(self):
        df = pd.DataFrame({"title": [], "text": []})
        result = deduplicate_semantic_lsh(df)
        assert len(result) == 0
