import pytest
import json
import pandas as pd
from unittest.mock import patch, MagicMock
from intelligence.relationships import cross_domain_pipeline
from intelligence.narratives import narrative_pipeline
from intelligence.signals import signals_pipeline
from intelligence.entity_graph import build_entity_graph
from pipeline import pipeline_cleanup


class TestCrossDomainPipelineIntegration:
    def test_full_pipeline_output_structure(self, sample_df, sample_sector_map):
        with patch("intelligence.relationships._get_embeddings", return_value=None):
            with patch("intelligence.relationships._HAS_REQUESTS", False):
                result = cross_domain_pipeline(sample_df)
        assert "sector_map" in result
        assert "cross_domain_links" in result
        assert "impact_chains" in result
        assert "summary" in result
        assert result["summary"]["total_entities_mapped"] > 0
        assert "total_cross_domain_links" in result["summary"]

    def test_links_have_confidence(self, sample_df):
        with patch("intelligence.relationships._get_embeddings", return_value=None):
            with patch("intelligence.relationships._HAS_REQUESTS", False):
                result = cross_domain_pipeline(sample_df)
        for link in result["cross_domain_links"]:
            assert link.get("confidence") is not None

    def test_empty_dataframe(self):
        result = cross_domain_pipeline(pd.DataFrame())
        assert result["cross_domain_links"] == []
        assert result["impact_chains"] == []

    def test_sector_map_has_entities(self, sample_df):
        with patch("intelligence.relationships._get_embeddings", return_value=None):
            with patch("intelligence.relationships._HAS_REQUESTS", False):
                result = cross_domain_pipeline(sample_df)
        assert len(result["sector_map"]) > 0
        for name, info in result["sector_map"].items():
            assert "sector" in info
            assert "mention_count" in info

    def test_summary_fields(self, sample_df):
        with patch("intelligence.relationships._get_embeddings", return_value=None):
            with patch("intelligence.relationships._HAS_REQUESTS", False):
                result = cross_domain_pipeline(sample_df)
        summary = result["summary"]
        assert "llm_verified" in summary
        assert "causal_explanations" in summary
        assert "avg_confidence" in summary


class TestNarrativePipelineIntegration:
    def test_output_structure(self, sample_df):
        result = narrative_pipeline(sample_df)
        assert "mutations" in result
        assert "entity_narratives" in result
        assert "summary" in result

    def test_entity_narratives_have_confidence(self, sample_df):
        result = narrative_pipeline(sample_df)
        for n in result["entity_narratives"]:
            assert "confidence" in n
            assert n["confidence"] is not None

    def test_empty_df(self):
        result = narrative_pipeline(pd.DataFrame())
        assert result["mutations"] == []
        assert result["entity_narratives"] == []


class TestSignalsPipelineIntegration:
    def test_output_structure(self, sample_df):
        with patch("intelligence.signals.atomic_read_json", return_value=None):
            result = signals_pipeline(sample_df)
        assert "signals" in result
        assert "summary" in result

    def test_signals_have_fields(self, sample_df):
        with patch("intelligence.signals.atomic_read_json", return_value=None):
            result = signals_pipeline(sample_df)
        for s in result["signals"]:
            assert "type" in s
            assert "score" in s
            assert "signal" in s

    def test_empty_df(self):
        with patch("intelligence.signals.atomic_read_json", return_value=None):
            result = signals_pipeline(pd.DataFrame())
        assert result["signals"] == []


class TestPipelineCleanup:
    def test_cleanup_runs_without_error(self):
        pipeline_cleanup()

    def test_cleanup_idempotent(self):
        pipeline_cleanup()
        pipeline_cleanup()
