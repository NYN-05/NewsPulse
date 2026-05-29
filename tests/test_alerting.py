import pytest
from unittest.mock import patch
from intelligence.alerting import alerting_pipeline, eval_relationship_alerts


class TestEvalRelationshipAlerts:
    def test_new_relationship(self):
        links = [{"source_entity": "a", "target_entity": "b", "source_sector": "tech", "target_sector": "finance", "strength": 0.9, "confidence": 0.85}]
        alerts = eval_relationship_alerts(links, [])
        assert len(alerts) == 1
        assert alerts[0]["severity"] in ("high", "medium", "low")

    def test_existing_relationship_skipped(self):
        links = [{"source_entity": "a", "target_entity": "b", "source_sector": "tech", "target_sector": "finance", "strength": 0.9, "confidence": 0.85}]
        alerts = eval_relationship_alerts(links, [{"source_entity": "a", "target_entity": "b"}])
        assert len(alerts) == 0

    def test_empty_links(self):
        assert eval_relationship_alerts([], []) == []


class TestAlertingPipeline:
    def test_basic(self, sample_links):
        for link in sample_links:
            link["confidence"] = 0.75
            link["strength"] = 0.8
        with patch("intelligence.alerting.atomic_read_json", return_value=[]):
            result = alerting_pipeline(sample_links, [], [], [])
        assert "alerts" in result
        assert "summary" in result

    def test_empty_inputs(self):
        with patch("intelligence.alerting.atomic_read_json", return_value=[]):
            result = alerting_pipeline([], [], [], [])
        assert result["alerts"] == []
        assert result["summary"]["total_alerts"] == 0

    def test_summary_structure(self, sample_links):
        for link in sample_links:
            link["confidence"] = 0.75
            link["strength"] = 0.8
        with patch("intelligence.alerting.atomic_read_json", return_value=[]):
            result = alerting_pipeline(sample_links, [], [], [])
        summary = result["summary"]
        assert "total_alerts" in summary
        assert "high_severity" in summary
        assert "medium_severity" in summary
        assert "low_severity" in summary
        assert "alert_types" in summary
        assert "generated_at" in summary
