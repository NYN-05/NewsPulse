import pytest
import pandas as pd
from unittest.mock import patch
from intelligence.relationships import (
    classify_entity_sector,
    build_sector_map,
    _calibrate_confidence,
    predict_cross_domain_impact,
    find_cross_domain_links,
)


class TestClassifyEntitySector:
    def test_known_entity(self):
        sector, conf = classify_entity_sector("nvidia", "org")
        assert sector == "technology"
        assert conf > 0.5

    def test_entity_with_context(self):
        sector, conf = classify_entity_sector("federal reserve", "org", ["central bank monetary policy"])
        assert sector == "finance"
        assert conf > 0.3

    def test_unknown_entity(self):
        sector, conf = classify_entity_sector("zzzzz", "org")
        assert isinstance(sector, str)
        assert 0 <= conf <= 1


class TestBuildSectorMap:
    def test_basic(self, sample_df):
        sector_map = build_sector_map(sample_df)
        assert isinstance(sector_map, dict)
        assert len(sector_map) > 0
        assert "nvidia" in sector_map
        assert "federal reserve" in sector_map

    def test_entity_structure(self, sample_df):
        sector_map = build_sector_map(sample_df)
        for entity_name, info in sector_map.items():
            assert "entity" in info
            assert "type" in info
            assert "sector" in info
            assert "confidence" in info
            assert "mention_count" in info

    def test_empty_df(self):
        assert build_sector_map(pd.DataFrame()) == {}

    def test_mention_count_accuracy(self, sample_df):
        sector_map = build_sector_map(sample_df)
        assert sector_map["nvidia"]["mention_count"] == 2
        assert sector_map["federal reserve"]["mention_count"] == 2


class TestCalibrateConfidence:
    def test_basic(self):
        link = {
            "source_entity": "nvidia",
            "target_entity": "fed",
            "source_sector": "tech",
            "target_sector": "finance",
            "cooccurrence_count": 5,
            "source_diversity": 3,
            "semantic_similarity": 0.6,
        }
        llm_result = {"verified": True, "confidence": 0.85, "causal_direction": "nvidia->fed", "causal_mechanism": "economic"}
        _calibrate_confidence(link, llm_result)
        assert link["verified"] is True
        assert link["causal_direction"] == "nvidia->fed"
        assert link["causal_mechanism"] == "economic"
        assert link["impact_prediction"] is not None
        assert link["explanation"] is not None

    def test_no_llm_result(self):
        link = {"source_entity": "a", "target_entity": "b"}
        _calibrate_confidence(link, None)
        assert link.get("verified") is None
        assert link.get("_llm_result") is None

    def test_mutates_in_place(self):
        link = {"source_entity": "a", "target_entity": "b"}
        result = _calibrate_confidence(link)
        assert result is link


class TestPredictCrossDomainImpact:
    def test_basic(self, sample_links, sample_sector_map):
        for link in sample_links:
            link["confidence"] = 0.75
            link["verified"] = True
            link["causal_direction"] = "nvidia->federal reserve"
            link["causal_mechanism"] = "economic"
            link["impact_prediction"] = None
            link["explanation"] = "test"
        results = predict_cross_domain_impact(sample_links, sample_sector_map)
        for link in results:
            assert "impact" in link
            assert link["impact"] is not None
            assert "predicted_effect" in link["impact"]
            assert "likelihood" in link["impact"]
            assert "timeframe" in link["impact"]
            assert "confidence_weighted" in link["impact"]
            assert 0 <= link["impact"]["likelihood"] <= 1

    def test_confidence_default_when_none(self):
        links = [{
            "source_entity": "nvidia",
            "target_entity": "fed",
            "source_sector": "technology",
            "target_sector": "finance",
            "cooccurrence_count": 5,
            "source_diversity": 3,
            "semantic_similarity": 0.6,
            "strength": 0.7,
            "confidence": None,
            "verified": False,
        }]
        results = predict_cross_domain_impact(links, {})
        for link in results:
            assert "impact" in link
            assert link["impact"]["likelihood"] > 0

    def test_missing_confidence_key(self):
        links = [{
            "source_entity": "nvidia",
            "target_entity": "fed",
            "source_sector": "technology",
            "target_sector": "finance",
        }]
        results = predict_cross_domain_impact(links, {})
        for link in results:
            assert "impact" in link

    def test_empty_links(self):
        assert predict_cross_domain_impact([], {}) == []


class TestFindCrossDomainLinks:
    def test_basic(self, sample_df, sample_sector_map):
        links = find_cross_domain_links(sample_df, sample_sector_map)
        assert isinstance(links, list)
        if links:
            link = links[0]
            assert "source_entity" in link
            assert "target_entity" in link
            assert "source_sector" in link
            assert "target_sector" in link
            assert "cooccurrence_count" in link
            assert "source_diversity" in link
            assert "strength" in link
            assert 0 <= link["strength"] <= 1

    def test_cross_sector_only(self, sample_df, sample_sector_map):
        links = find_cross_domain_links(sample_df, sample_sector_map)
        for link in links:
            assert link["source_sector"] != link["target_sector"]

    def test_empty_df(self, sample_sector_map):
        links = find_cross_domain_links(pd.DataFrame(), sample_sector_map)
        assert links == []
