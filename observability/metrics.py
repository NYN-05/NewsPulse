import time
import json
import os
import logging
from datetime import datetime
from typing import Dict
from collections import defaultdict

logger = logging.getLogger(__name__)


class PipelineMetrics:
    def __init__(self):
        self._metrics = defaultdict(list)
        self._counters = defaultdict(int)
        self._start_time = None
        self._load()

    def _load(self):
        path = os.path.join("output", "logs", "metrics.json")
        try:
            if os.path.exists(path):
                with open(path) as f:
                    data = json.load(f)
                    self._counters = defaultdict(int, data.get("counters", {}))
        except Exception:
            pass

    def _save(self):
        path = os.path.join("output", "logs", "metrics.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {"counters": dict(self._counters), "last_updated": datetime.now().isoformat()}
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def start_run(self):
        self._start_time = time.time()
        self._metrics = defaultdict(list)
        self._counters["pipeline_runs"] += 1

    def end_run(self):
        if self._start_time:
            elapsed = time.time() - self._start_time
            self._metrics["duration_seconds"].append(elapsed)
            self._counters["total_duration_seconds"] += elapsed
        self._save()

    def record_scrape(self, source: str, count: int):
        self._counters[f"scrape_{source}"] += count
        self._counters["total_scraped"] += count

    def record_rss(self, count: int):
        self._counters["rss_articles"] += count
        self._counters["total_scraped"] += count

    def record_analyzed(self, count: int):
        self._counters["total_analyzed"] += count

    def record_clustered(self, count: int):
        self._counters["total_clustered"] += count

    def record_error(self, error_type: str):
        self._counters[f"error_{error_type}"] += 1

    def get_report(self) -> Dict:
        return {
            "counters": dict(self._counters),
            "pipeline_runs": self._counters.get("pipeline_runs", 0),
            "total_scraped": self._counters.get("total_scraped", 0),
            "total_analyzed": self._counters.get("total_analyzed", 0),
            "avg_duration": round(self._counters.get("total_duration_seconds", 0) / max(self._counters.get("pipeline_runs", 1), 1), 2),
        }


metrics = PipelineMetrics()
