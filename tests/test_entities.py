import pytest
import json
import pandas as pd
from nlp.entities import (
    get_entity_dict,
    extract_entities,
    extract_entities_batch,
)


class TestGetEntityDict:
    def test_with_parsed_entities(self):
        class MockRow:
            _parsed_entities = {"persons": ["john"], "orgs": ["acme"], "locations": ["nyc"]}
        result = get_entity_dict(MockRow())
        assert result == {"persons": ["john"], "orgs": ["acme"], "locations": ["nyc"]}

    def test_with_entities_json_string(self):
        class MockRow:
            entities = '{"persons": ["john"], "orgs": ["acme"], "locations": ["nyc"]}'
        result = get_entity_dict(MockRow())
        assert result == {"persons": ["john"], "orgs": ["acme"], "locations": ["nyc"]}

    def test_with_empty_entities(self):
        class MockRow:
            entities = ""
        result = get_entity_dict(MockRow())
        assert result == {"persons": [], "orgs": [], "locations": []}

    def test_with_malformed_json(self):
        class MockRow:
            entities = "not valid json"
        result = get_entity_dict(MockRow())
        assert result == {"persons": [], "orgs": [], "locations": []}

    def test_with_none_entities(self):
        class MockRow:
            entities = None
        result = get_entity_dict(MockRow())
        assert result == {"persons": [], "orgs": [], "locations": []}

    def test_prefers_parsed_entities(self):
        class MockRow:
            _parsed_entities = {"persons": ["from_parsed"], "orgs": [], "locations": []}
            entities = '{"persons": ["from_string"], "orgs": [], "locations": []}'
        result = get_entity_dict(MockRow())
        assert result["persons"] == ["from_parsed"]

    def test_namedtuple_style(self):
        Row = __import__("collections").namedtuple("Row", ["_parsed_entities", "entities"])
        row = Row(_parsed_entities={"persons": ["a"], "orgs": [], "locations": []}, entities=None)
        result = get_entity_dict(row)
        assert result["persons"] == ["a"]

    def test_object_without_entities(self):
        class MockRow:
            pass
        result = get_entity_dict(MockRow())
        assert result == {"persons": [], "orgs": [], "locations": []}


class TestExtractEntities:
    def test_regex_fallback(self):
        text = "John Smith works at Apple Inc in New York City"
        result = extract_entities(text, threshold=0.0)
        assert isinstance(result, dict)
        assert "persons" in result
        assert "orgs" in result
        assert "locations" in result

    def test_empty_text(self):
        result = extract_entities("", threshold=0.0)
        assert result == {"persons": [], "orgs": [], "locations": []}

    def test_short_text(self):
        result = extract_entities("Hi", threshold=0.0)
        assert result == {"persons": [], "orgs": [], "locations": []}


class TestExtractEntitiesBatch:
    def test_basic(self):
        texts = ["Apple Inc is a company", "John works there"]
        results = extract_entities_batch(texts, threshold=0.0)
        assert len(results) == 2
        for r in results:
            data = json.loads(r)
            assert "persons" in data
            assert "orgs" in data
            assert "locations" in data

    def test_empty_list(self):
        assert extract_entities_batch([], threshold=0.0) == []

    def test_long_text_truncation(self):
        long_text = "word " * 500
        result = extract_entities_batch([long_text], threshold=0.0)
        parsed = json.loads(result[0])
        entity_count = sum(len(v) for v in parsed.values())
        assert isinstance(entity_count, int)
