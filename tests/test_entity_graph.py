import pytest
import pandas as pd
import json
from intelligence.entity_graph import build_entity_graph


class TestBuildEntityGraph:
    def test_basic_graph(self, sample_df):
        result = build_entity_graph(sample_df)
        assert "nodes" in result
        assert "edges" in result
        assert "stats" in result
        assert result["stats"]["total_nodes"] > 0
        assert result["stats"]["total_edges"] > 0

    def test_top_entities_present(self, sample_df):
        result = build_entity_graph(sample_df)
        entity_names = [n["id"] for n in result["nodes"]]
        assert "nvidia" in entity_names
        assert "federal reserve" in entity_names

    def test_edge_weights(self, sample_df):
        result = build_entity_graph(sample_df)
        for edge in result["edges"]:
            assert edge["weight"] >= 2

    def test_empty_dataframe(self):
        df = pd.DataFrame()
        result = build_entity_graph(df)
        assert "error" in result

    def test_no_entities_column(self):
        df = pd.DataFrame({"title": ["test"], "text": ["hello"]})
        result = build_entity_graph(df)
        assert "error" in result

    def test_parsed_entities_column(self):
        articles = [
            {
                "title": "test",
                "text": "test article",
                "entities": json.dumps({"persons": ["john"], "orgs": ["acme"], "locations": []}),
                "_parsed_entities": json.loads(json.dumps({"persons": ["john"], "orgs": ["acme"], "locations": []})),
            },
        ]
        df = pd.DataFrame(articles)
        result = build_entity_graph(df)
        assert "error" not in result
        assert result["stats"]["total_nodes"] == 2

    def test_single_article_no_graph(self):
        articles = [
            {
                "title": "test",
                "text": "a single entity article",
                "entities": json.dumps({"persons": [], "orgs": ["acme"], "locations": []}),
                "_parsed_entities": {"persons": [], "orgs": ["acme"], "locations": []},
            },
        ]
        df = pd.DataFrame(articles)
        result = build_entity_graph(df)
        assert result["stats"]["total_nodes"] == 0

    def test_centrality_in_top_nodes(self, sample_df):
        result = build_entity_graph(sample_df)
        for node in result["nodes"]:
            if len(result["nodes"]) > 0:
                assert "centrality" in node
                assert "count" in node
                assert "sources" in node
