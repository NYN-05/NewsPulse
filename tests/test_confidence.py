import pytest
from intelligence.confidence import (
    calibrate_relationship_confidence,
    calibrate_narrative_confidence,
    calibrate_signal_confidence,
    calibrate_batch,
)


class TestCalibrateRelationshipConfidence:
    def test_basic_calibration(self):
        link = {
            "source_entity": "nvidia",
            "target_entity": "fed",
            "source_sector": "technology",
            "target_sector": "finance",
            "cooccurrence_count": 10,
            "source_diversity": 5,
            "semantic_similarity": 0.8,
        }
        calibrate_relationship_confidence(link)
        assert "confidence" in link
        assert "confidence_label" in link
        assert "confidence_signals" in link
        assert link["confidence"] is not None
        assert 0.05 <= link["confidence"] <= 0.99
        assert link["confidence_label"] in ("high", "medium", "low")

    def test_confidence_never_none(self):
        link = {
            "source_entity": "a",
            "target_entity": "b",
            "source_sector": "tech",
            "target_sector": "finance",
            "cooccurrence_count": 0,
            "source_diversity": 0,
            "semantic_similarity": 0.0,
        }
        calibrate_relationship_confidence(link)
        assert link["confidence"] is not None

    def test_with_causal_evidence(self):
        link = {
            "source_entity": "nvidia",
            "target_entity": "fed",
            "source_sector": "technology",
            "target_sector": "finance",
            "cooccurrence_count": 10,
            "source_diversity": 5,
            "semantic_similarity": 0.8,
            "causal_direction": "nvidia->fed",
            "causal_mechanism": "economic impact via capital expenditure",
        }
        calibrate_relationship_confidence(link)
        assert link["confidence"] > 0.5

    def test_with_llm_result(self):
        link = {
            "source_entity": "nvidia",
            "target_entity": "fed",
            "source_sector": "technology",
            "target_sector": "finance",
            "cooccurrence_count": 5,
            "source_diversity": 3,
            "semantic_similarity": 0.6,
        }
        llm_result = {"verified": True, "confidence": 0.9}
        calibrate_relationship_confidence(link, llm_result)
        assert link["confidence"] > 0.6
        assert "confidence_signals" in link
        assert "llm_verification" in link["confidence_signals"]

    def test_with_llm_not_verified(self):
        link = {
            "source_entity": "a",
            "target_entity": "b",
            "source_sector": "tech",
            "target_sector": "finance",
            "cooccurrence_count": 1,
            "source_diversity": 1,
            "semantic_similarity": 0.3,
        }
        llm_result = {"verified": False, "confidence": 0.2}
        calibrate_relationship_confidence(link, llm_result)
        assert link["confidence"] < 0.5

    def test_mutates_input(self):
        link = {
            "source_entity": "a",
            "target_entity": "b",
            "source_sector": "tech",
            "target_sector": "finance",
            "cooccurrence_count": 5,
            "source_diversity": 3,
            "semantic_similarity": 0.6,
        }
        result = calibrate_relationship_confidence(link)
        assert result is link

    def test_confidence_labels_high(self):
        link = {
            "source_entity": "a",
            "target_entity": "b",
            "source_sector": "tech",
            "target_sector": "finance",
            "cooccurrence_count": 100,
            "source_diversity": 50,
            "semantic_similarity": 0.95,
            "causal_direction": "a->b",
            "causal_mechanism": "test",
        }
        calibrate_relationship_confidence(link)
        assert link["confidence_label"] == "high"

    def test_confidence_labels_low(self):
        link = {
            "source_entity": "a",
            "target_entity": "b",
            "source_sector": "tech",
            "target_sector": "finance",
            "cooccurrence_count": 0,
            "source_diversity": 0,
            "semantic_similarity": 0.0,
        }
        calibrate_relationship_confidence(link)
        assert link["confidence_label"] == "low"


class TestCalibrateNarrativeConfidence:
    def test_basic_narrative(self):
        narrative = {"entity": "nvidia", "total_mentions": 10, "recent_7_days": 5}
        calibrate_narrative_confidence(narrative)
        assert "confidence" in narrative
        assert "confidence_label" in narrative
        assert narrative["confidence"] is not None

    def test_empty_narrative(self):
        narrative = {}
        calibrate_narrative_confidence(narrative)
        assert narrative["confidence"] is not None


class TestCalibrateSignalConfidence:
    def test_basic_signal(self):
        signal = {"score": 0.8, "burst_factor": 2.5}
        calibrate_signal_confidence(signal)
        assert "confidence" in signal
        assert signal["confidence"] is not None

    def test_low_score_signal(self):
        signal = {"score": 0.1}
        calibrate_signal_confidence(signal)
        assert signal["confidence"] is not None

    def test_none_score_signal(self):
        signal = {"score": None}
        calibrate_signal_confidence(signal)
        assert signal["confidence"] is not None


class TestCalibrateBatch:
    def test_batch_relationships(self, sample_links):
        results = calibrate_batch(sample_links, item_type="relationship")
        assert len(results) == 2
        for link in results:
            assert link["confidence"] is not None

    def test_batch_narratives(self):
        narratives = [
            {"entity": "nvidia", "total_mentions": 10, "recent_7_days": 5},
            {"entity": "fed", "total_mentions": 3, "recent_7_days": 1},
        ]
        results = calibrate_batch(narratives, item_type="narrative")
        assert len(results) == 2
        for n in results:
            assert n["confidence"] is not None

    def test_batch_signals(self):
        signals = [
            {"score": 0.9, "burst_factor": 3.0},
            {"score": 0.2},
        ]
        results = calibrate_batch(signals, item_type="signal")
        assert len(results) == 2
        for s in results:
            assert s["confidence"] is not None

    def test_batch_empty(self):
        assert calibrate_batch([], "relationship") == []
        assert calibrate_batch([], "narrative") == []
        assert calibrate_batch([], "signal") == []
