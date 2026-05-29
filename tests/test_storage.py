import pytest
import pandas as pd
import json
import hashlib
from storage.manager import DataManager
from vector_store.chroma_store import index_articles


class TestDataManager:
    def test_load_empty(self, tmp_data_dir):
        mgr = DataManager()
        df = mgr.load_raw()
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_save_and_load_raw(self, tmp_data_dir):
        mgr = DataManager()
        df = pd.DataFrame({"title": ["test"], "text": ["hello"]})
        mgr.save_raw(df)
        loaded = mgr.load_raw(force_reload=True)
        assert len(loaded) == 1
        assert loaded.iloc[0]["title"] == "test"

    def test_merge_new_articles(self, tmp_data_dir):
        mgr = DataManager()
        new = [{"title": "a", "text": "hello", "source": "reuters", "link": "http://example.com/a", "published": "2026-05-28"}]
        result = mgr.merge_new_articles(new)
        assert len(result) == 1

    def test_merge_deduplicates(self, tmp_data_dir):
        mgr = DataManager()
        articles = [
            {"title": "a", "text": "hello", "source": "reuters", "link": "http://example.com/a", "published": "2026-05-28"},
            {"title": "a", "text": "hello", "source": "reuters", "link": "http://example.com/a", "published": "2026-05-28"},
        ]
        result = mgr.merge_new_articles(articles)
        assert len(result) == 1

    def test_get_existing_keys(self, tmp_data_dir):
        mgr = DataManager()
        df = pd.DataFrame({
            "title": ["a", "b"],
            "link": ["http://a.com", "http://b.com"],
            "source": ["reuters", "ap"],
        })
        keys = mgr.get_existing_keys(df)
        assert len(keys) == 2
        assert ("a", "http://a.com", "reuters") in keys

    def test_drop_redundant_columns(self, tmp_data_dir):
        mgr = DataManager()
        df = pd.DataFrame({"title": ["a"], "text_tmp": ["hello"]})
        result = mgr.drop_redundant_columns(df)
        assert "text_tmp" not in result.columns
        assert "title" in result.columns


class TestVectorStore:
    def test_index_empty_articles(self):
        df = pd.DataFrame({"title": [], "text": []})
        result = index_articles(df)
        assert result == 0

    def test_index_articles_structure(self, sample_df):
        result = index_articles(sample_df)
        assert isinstance(result, int)
