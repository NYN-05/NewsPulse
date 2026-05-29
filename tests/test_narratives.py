import pytest
import pandas as pd
import json
from intelligence.narratives import (
    detect_narrative_phases,
    compute_narrative_mutation,
    compute_entity_narratives,
    find_emerging_topics,
    find_disappearing_topics,
)


class TestDetectNarrativePhases:
    def test_emerging(self):
        trajectory = [
            {"date": "2026-05-20", "count": 0},
            {"date": "2026-05-21", "count": 1},
            {"date": "2026-05-22", "count": 3},
            {"date": "2026-05-23", "count": 5},
        ]
        assert detect_narrative_phases(trajectory) == "emerging"

    def test_declining(self):
        trajectory = [
            {"date": "2026-05-20", "count": 10},
            {"date": "2026-05-21", "count": 7},
            {"date": "2026-05-22", "count": 4},
            {"date": "2026-05-23", "count": 2},
        ]
        assert detect_narrative_phases(trajectory) == "declining"

    def test_stable(self):
        trajectory = [
            {"date": "2026-05-20", "count": 5},
            {"date": "2026-05-21", "count": 5},
            {"date": "2026-05-22", "count": 5},
        ]
        assert detect_narrative_phases(trajectory) == "stable"

    def test_peaked(self):
        trajectory = [
            {"date": "2026-05-20", "count": 1},
            {"date": "2026-05-21", "count": 5},
            {"date": "2026-05-22", "count": 15},
            {"date": "2026-05-23", "count": 3},
        ]
        assert detect_narrative_phases(trajectory) == "peaked"

    def test_fading(self):
        trajectory = [
            {"date": "2026-05-20", "count": 20},
            {"date": "2026-05-21", "count": 10},
            {"date": "2026-05-22", "count": 3},
            {"date": "2026-05-23", "count": 1},
        ]
        assert detect_narrative_phases(trajectory) == "fading"

    def test_empty_trajectory(self):
        assert detect_narrative_phases([]) == "dormant"

    def test_single_point(self):
        trajectory = [{"date": "2026-05-20", "count": 5}]
        assert detect_narrative_phases(trajectory) in ("emerging", "stable")


class TestComputeNarrativeMutation:
    def test_basic_mutation(self, sample_df):
        mutations = compute_narrative_mutation(sample_df, window_days=30)
        assert isinstance(mutations, list)
        if mutations:
            m = mutations[0]
            assert "window" in m
            assert "keyword_retention_pct" in m or "drift_score" in m

    def test_empty_df(self):
        mutations = compute_narrative_mutation(pd.DataFrame(), window_days=7)
        assert mutations == []


class TestComputeEntityNarratives:
    def test_basic(self, sample_df):
        narratives = compute_entity_narratives(sample_df)
        assert isinstance(narratives, list)
        if narratives:
            n = narratives[0]
            assert "entity" in n
            assert "phase" in n
            assert "total_mentions" in n

    def test_entity_order(self, sample_df):
        narratives = compute_entity_narratives(sample_df)
        names = [n["entity"] for n in narratives]
        assert "nvidia" in names
        assert "federal reserve" in names

    def test_empty_df(self):
        assert compute_entity_narratives(pd.DataFrame()) == []


class TestFindEmergingTopics:
    def test_return_format(self):
        entity_narratives = [
            {"entity": "nvidia", "phase": "emerging", "total_mentions": 10, "trajectory": [{"date": "2026-05-20", "count": 5}]},
            {"entity": "fed", "phase": "declining", "total_mentions": 5, "trajectory": [{"date": "2026-05-20", "count": 2}]},
        ]
        result = find_emerging_topics(entity_narratives, [], top_n=5)
        assert isinstance(result, list)
        if result:
            assert result[0]["type"] == "entity"

    def test_no_emerging(self):
        narratives = [
            {"entity": "fed", "phase": "declining", "total_mentions": 5, "trajectory": []},
        ]
        result = find_emerging_topics(narratives, [], top_n=5)
        assert isinstance(result, list)


class TestFindDisappearingTopics:
    def test_return_format(self):
        entity_narratives = [
            {"entity": "old_tech", "phase": "fading", "total_mentions": 2, "trajectory": [{"date": "2026-05-20", "count": 1}]},
        ]
        result = find_disappearing_topics(entity_narratives, [], top_n=5)
        assert isinstance(result, list)

    def test_no_disappearing(self):
        narratives = [
            {"entity": "fed", "phase": "growing", "total_mentions": 5, "trajectory": []},
        ]
        result = find_disappearing_topics(narratives, [], top_n=5)
        assert isinstance(result, list)
