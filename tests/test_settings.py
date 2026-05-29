import pytest
import os
import json
import pandas as pd
from config.settings import (
    get,
    load_config,
    path_for,
    atomic_write_json,
    atomic_read_json,
)


class TestGetConfig:
    def test_get_existing(self, mock_config):
        val = get("intelligence.llm_max_links")
        assert val == 20

    def test_get_nested(self, mock_config):
        val = get("paths.data_dir")
        assert val is not None

    def test_get_default(self, mock_config):
        val = get("nonexistent.key", default="fallback")
        assert val == "fallback"

    def test_get_none_default(self, mock_config):
        val = get("nonexistent")
        assert val is None

    def test_get_quality(self, mock_config):
        val = get("quality.dedup_threshold")
        assert val == 0.85


class TestPathFor:
    def test_path_for_output(self, mock_config, tmp_path):
        assert path_for("output_dir") is not None

    def test_path_for_nonexistent(self, mock_config):
        result = path_for("nonexistent")
        assert result == ""

    def test_path_for_returns_absolute(self, mock_config):
        data_dir = path_for("data_dir")
        assert os.path.isabs(data_dir) or data_dir == ""


class TestAtomicWriteRead:
    def test_write_then_read(self, tmp_path):
        filepath = tmp_path / "test.json"
        data = {"key": "value", "number": 42, "list": [1, 2, 3]}
        atomic_write_json(str(filepath), data)
        assert filepath.exists()
        result = atomic_read_json(str(filepath))
        assert result == data

    def test_read_nonexistent(self):
        result = atomic_read_json("C:\\nonexistent\\path\\file.json")
        assert result is None

    def test_write_empty_dict(self, tmp_path):
        filepath = tmp_path / "empty.json"
        atomic_write_json(str(filepath), {})
        result = atomic_read_json(str(filepath))
        assert result == {}

    def test_write_none(self, tmp_path):
        filepath = tmp_path / "none.json"
        atomic_write_json(str(filepath), None)
        result = atomic_read_json(str(filepath))
        assert result is None

    def test_overwrite_file(self, tmp_path):
        filepath = tmp_path / "overwrite.json"
        atomic_write_json(str(filepath), {"first": True})
        atomic_write_json(str(filepath), {"second": True})
        result = atomic_read_json(str(filepath))
        assert result == {"second": True}


class TestLoadConfig:
    def test_load_config(self, tmp_path):
        yaml_path = tmp_path / "test_config.yaml"
        yaml_path.write_text("test_key: test_value\npaths:\n  data_dir: C:\\tmp\\data")
        result = load_config(str(yaml_path))
        assert result["test_key"] == "test_value"
