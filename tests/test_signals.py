import pytest
import pandas as pd
import json
from intelligence.signals import (
    signal_new_relationships,
    detect_cross_domain_spillover,
    detect_signals,
)


class TestSignalNewRelationships:
    def test_no_prev_links(self, sample_df):
        signals = signal_new_relationships(sample_df, prev_links=None)
        assert signals == []

    def test_empty_prev_links(self, sample_df):
        signals = signal_new_relationships(sample_df, prev_links=[])
        assert isinstance(signals, list)

    def test_with_prev_links(self, sample_df):
        prev_links = [
            {"source_entity": "nvidia", "target_entity": "fed", "source_sector": "tech", "target_sector": "finance"},
        ]
        signals = signal_new_relationships(sample_df, prev_links=prev_links)
        assert isinstance(signals, list)
        for s in signals:
            assert "type" in s
            assert "signal" in s
            assert "score" in s

    def test_signal_types(self, sample_df):
        prev_links = []
        signals = signal_new_relationships(sample_df, prev_links=prev_links)
        for s in signals:
            assert s["type"] in ("emerging_relationship", "cross_domain_spillover", "anomaly")


class TestDetectCrossDomainSpillover:
    def test_not_enough_rows(self, sample_df):
        small_df = sample_df.head(2)
        signals = detect_cross_domain_spillover(small_df)
        assert signals == []

    def test_enough_rows(self, sample_df):
        big_df = pd.concat([sample_df] * 10, ignore_index=True)
        big_df["published"] = "2026-05-28"
        signals = detect_cross_domain_spillover(big_df)
        assert isinstance(signals, list)


class TestDetectSignals:
    def test_basic(self, sample_df):
        signals = detect_signals(sample_df)
        assert isinstance(signals, list)
        assert len(signals) <= 20

    def test_empty_df(self):
        signals = detect_signals(pd.DataFrame())
        assert isinstance(signals, list)

    def test_with_prev_links(self, sample_df):
        signals = detect_signals(sample_df, prev_links=[])
        assert isinstance(signals, list)

    def test_signal_structure(self, sample_df):
        signals = detect_signals(sample_df)
        for s in signals:
            assert "type" in s
            assert "signal" in s
            assert "score" in s
