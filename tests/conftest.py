import sys
import os
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(autouse=True)
def mock_config(monkeypatch):
    monkeypatch.setattr(
        "config.settings._CONFIG",
        {
            "paths": {
                "data_dir": str(Path(__file__).parent / "test_data"),
                "output_dir": str(Path(__file__).parent / "test_data" / "output"),
                "news_csv": "raw_articles.csv",
                "analyzed_parquet": "analyzed_articles.parquet",
            },
            "intelligence": {
                "llm_verification": False,
                "llm_max_links": 20,
                "enable_multi_agent": False,
                "enable_temporal": False,
                "enable_briefings": False,
                "enable_causal": False,
            },
            "quality": {
                "dedup_threshold": 0.85,
                "enable_semantic_dedup": False,
            },
            "alerts": {"enabled": False},
            "causal": {"enabled": False},
            "neo4j": {"enabled": False},
            "export": {"enabled": False},
            "scheduler": {"enabled": False, "interval_minutes": 15},
        },
    )
    monkeypatch.setattr("config.settings._SETTINGS", None)


@pytest.fixture
def sample_df():
    articles = [
        {
            "title": "Nvidia reports record earnings",
            "text": "Nvidia announced record quarterly earnings driven by AI chip demand. The company's revenue surged past analyst expectations as data center growth accelerated.",
            "source": "reuters",
            "link": "https://example.com/nvidia-earnings",
            "published": "2026-05-28",
            "category": "technology",
            "entities": json.dumps({"persons": ["jensen huang"], "orgs": ["nvidia"], "locations": ["santa clara"]}),
        },
        {
            "title": "Federal Reserve holds interest rates steady",
            "text": "The Federal Reserve decided to maintain current interest rates, citing mixed economic signals. Chair Jerome Powell emphasized a data-dependent approach.",
            "source": "bloomberg",
            "link": "https://example.com/fed-rates",
            "published": "2026-05-28",
            "category": "finance",
            "entities": json.dumps({"persons": ["jerome powell"], "orgs": ["federal reserve"], "locations": ["washington"]}),
        },
        {
            "title": "Nvidia chips used in Fed economic models",
            "text": "The Federal Reserve is adopting Nvidia-powered supercomputers for economic forecasting, creating an unexpected link between semiconductor and monetary policy.",
            "source": "reuters",
            "link": "https://example.com/nvidia-fed",
            "published": "2026-05-27",
            "category": "technology",
            "entities": json.dumps({"persons": ["jensen huang", "jerome powell"], "orgs": ["nvidia", "federal reserve"], "locations": []}),
        },
        {
            "title": "AI regulation debate heats up",
            "text": "Lawmakers in Washington DC are debating new AI regulations that could impact both tech companies and financial markets.",
            "source": "ap",
            "link": "https://example.com/ai-regulation",
            "published": "2026-05-26",
            "category": "politics",
            "entities": json.dumps({"persons": [], "orgs": ["congress"], "locations": ["washington"]}),
        },
        {
            "title": "Stock market mixed on rate decision",
            "text": "Wall Street showed mixed reactions to the Fed rate decision, with technology stocks outperforming financials.",
            "source": "bloomberg",
            "link": "https://example.com/market-mixed",
            "published": "2026-05-25",
            "category": "finance",
            "entities": json.dumps({"persons": [], "orgs": ["wall street"], "locations": ["new york"]}),
        },
    ]
    df = pd.DataFrame(articles)
    df["_parsed_entities"] = df["entities"].apply(json.loads)
    df["full_text"] = df["text"]
    return df


@pytest.fixture
def sample_links():
    return [
        {
            "source_entity": "nvidia",
            "target_entity": "federal reserve",
            "source_sector": "technology",
            "target_sector": "finance",
            "cooccurrence_count": 5,
            "source_diversity": 3,
            "strength": 0.75,
            "semantic_similarity": 0.6,
            "explanation": None,
            "confidence": None,
        },
        {
            "source_entity": "jensen huang",
            "target_entity": "jerome powell",
            "source_sector": "technology",
            "target_sector": "finance",
            "cooccurrence_count": 3,
            "source_diversity": 2,
            "strength": 0.5,
            "semantic_similarity": 0.4,
            "explanation": None,
            "confidence": None,
        },
    ]


@pytest.fixture
def sample_sector_map():
    return {
        "nvidia": {"entity": "nvidia", "type": "org", "sector": "technology", "confidence": 0.9, "mention_count": 2},
        "federal reserve": {"entity": "federal reserve", "type": "org", "sector": "finance", "confidence": 0.85, "mention_count": 2},
        "jensen huang": {"entity": "jensen huang", "type": "person", "sector": "technology", "confidence": 0.7, "mention_count": 2},
        "jerome powell": {"entity": "jerome powell", "type": "person", "sector": "finance", "confidence": 0.8, "mention_count": 2},
        "congress": {"entity": "congress", "type": "org", "sector": "politics", "confidence": 0.75, "mention_count": 1},
        "wall street": {"entity": "wall street", "type": "org", "sector": "finance", "confidence": 0.7, "mention_count": 1},
    }


@pytest.fixture
def tmp_data_dir(tmp_path):
    data_dir = tmp_path / "test_data"
    data_dir.mkdir()
    output_dir = data_dir / "output"
    output_dir.mkdir()
    return data_dir
