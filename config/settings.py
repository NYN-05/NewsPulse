import os
import json
import yaml
import warnings
import logging
import threading
from dataclasses import dataclass, field, fields
from typing import Any, Dict, Optional

_FILE_LOCK = threading.Lock()

_CONFIG: Dict[str, Any] = {}
_SETTINGS: Optional["Settings"] = None

_ENV_PREFIX = "NEWSPULSE_"


@dataclass
class Settings:
    paths: Dict[str, str] = field(default_factory=lambda: {
        "data_dir": ".", "output_dir": "output",
        "news_csv": "output/data/news_data.csv",
        "analyzed_parquet": "output/data/news_analyzed.parquet",
        "analyzed_csv": "output/data/news_analyzed.csv",
        "update_log": "output/logs/update_log.json",
    })
    scraper: Dict[str, Any] = field(default_factory=lambda: {
        "user_agent": "Mozilla/5.0", "timeout": 15,
        "max_articles_per_source": 50, "global_article_cap": 500,
        "max_workers": 8,
        "retry_attempts": 3, "retry_backoff": 1.0, "request_delay": 0.0,
    })
    nlp: Dict[str, Any] = field(default_factory=lambda: {
        "batch_size": 64, "cache_size": 2048, "entity_threshold": 0.5,
    })
    quality: Dict[str, Any] = field(default_factory=lambda: {
        "dedup_threshold": 0.85, "enable_semantic_dedup": True,
        "enable_boilerplate_removal": True,
    })
    intelligence: Dict[str, Any] = field(default_factory=lambda: {
        "min_entity_mentions": 2, "min_link_cooccurrence": 2,
        "max_cross_domain_links": 200, "max_impact_chains": 50,
        "llm_verification": True, "llm_max_links": 20, "llm_model": "qwen3:14b",
        "multi_agent": {"enabled": True, "analyst_model": "qwen3:14b",
                        "critic_model": "qwen3:14b", "summarizer_model": "qwen3:14b"},
        "temporal": {"enabled": True, "anomaly_std_threshold": 2.0,
                     "burst_z_threshold": 2.5, "min_burst_count": 2},
        "briefings": {"enabled": True, "include_predictions": True, "max_watch_items": 20},
    })
    causal: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True, "min_lag_hours": 6, "max_lag_days": 14,
        "lookback_days": 30, "max_candidates": 100, "max_chains": 30,
    })
    vector_store: Dict[str, Any] = field(default_factory=lambda: {
        "collection_name": "newspulse", "embedding_model": "BAAI/bge-m3",
        "reranker_model": "BAAI/bge-reranker-v2-m3",
        "use_hybrid_search": True, "use_reranker": False,
    })
    neo4j: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": False, "uri": "bolt://localhost:7687",
        "user": "neo4j", "password": "",
    })
    alerts: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True, "velocity_acceleration_threshold": 3.0,
        "velocity_magnitude_threshold": 2.0, "burst_threshold": 3.0,
        "phase_transition_threshold": 0.7, "relationship_confidence_threshold": 0.8,
    })
    auth: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True, "jwt_secret": "",
        "jwt_expiry_hours": 24,
    })
    export: Dict[str, Any] = field(default_factory=lambda: {
        "json_dir": "output/exports", "csv_dir": "output/exports",
        "markdown_dir": "output/exports",
    })
    scheduler: Dict[str, Any] = field(default_factory=lambda: {
        "enabled": True, "interval_minutes": 15,
        "initial_delay_seconds": 10, "fail_safe": True,
    })
    logging: Dict[str, Any] = field(default_factory=lambda: {
        "level": "INFO", "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    })

    @classmethod
    def from_yaml(cls, path: str) -> "Settings":
        path = os.path.abspath(path)
        with open(path, "r") as f:
            raw = yaml.safe_load(f) or {}
        return cls(**{k: v for k, v in raw.items() if hasattr(cls, k)})

    @classmethod
    def from_env(cls, base: Optional["Settings"] = None) -> "Settings":
        raw = {}
        if base is not None:
            for f in fields(cls):
                val = getattr(base, f.name)
                raw[f.name] = dict(val) if isinstance(val, dict) else val
        s = cls(**raw)
        for key, val in os.environ.items():
            if not key.startswith(_ENV_PREFIX):
                continue
            parts = key[len(_ENV_PREFIX):].lower().split("_", 1)
            if len(parts) != 2:
                continue
            section, setting = parts
            if not hasattr(s, section):
                continue
            sec = getattr(s, section)
            if not isinstance(sec, dict):
                continue
            sec[setting] = _coerce_env(val, sec.get(setting))
        return s

    def as_dict(self) -> Dict[str, Any]:
        return {f.name: dict(getattr(self, f.name)) for f in fields(self)}


def _coerce_env(raw: str, default: Any) -> Any:
    if isinstance(default, bool):
        return raw.lower() in ("1", "true", "yes")
    if isinstance(default, int):
        return int(raw)
    if isinstance(default, float):
        return float(raw)
    return raw


def _suppress_warnings():
    warnings.filterwarnings("ignore")
    for lib in ["transformers", "tokenizers", "huggingface_hub", "urllib3", "PIL"]:
        try:
            mod = __import__(lib)
            if hasattr(mod, "logging"):
                mod.logging.set_verbosity_error()
            logger = getattr(mod, "logger", None)
            if logger is not None:
                logger.setLevel(logging.ERROR)
        except (ImportError, AttributeError):
            pass
    try:
        import logging
        logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
        logging.getLogger("torch").setLevel(logging.ERROR)
    except Exception:
        pass


def _validate_secrets():
    jwt_secret = get("auth.jwt_secret", "")
    if not jwt_secret:
        env_val = os.environ.get("NEWSPULSE_AUTH_JWT_SECRET")
        if env_val:
            _CONFIG["auth"]["jwt_secret"] = env_val
            return
        if get("auth.enabled", True):
            warnings.warn(
                "CRITICAL: JWT secret is not configured! "
                "Set NEWSPULSE_AUTH_JWT_SECRET environment variable. "
                "Falling back to disabled auth for safety."
            )
            _CONFIG["auth"]["enabled"] = False


def load_config(path: str = None, as_settings: bool = False) -> Any:
    _suppress_warnings()
    global _CONFIG, _SETTINGS
    if _CONFIG and not as_settings:
        return _CONFIG
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.yaml")
    path = os.path.abspath(path)
    with open(path, "r") as f:
        _CONFIG = yaml.safe_load(f)
    _resolve_paths()
    if as_settings:
        _SETTINGS = Settings.from_env(base=Settings.from_yaml(path))
        _validate_secrets()
        auth_enabled = get("auth.enabled", True)
        if not auth_enabled:
            logging.getLogger("api").warning(
                "SECURITY: Authentication is DISABLED. All API endpoints are publicly accessible. "
                "Set auth.enabled: true in config or NEWSPULSE_AUTH_ENABLED=true env var in production."
            )
        return _SETTINGS
    return _CONFIG

def _resolve_paths():
    data_dir = _CONFIG.get("paths", {}).get("data_dir", ".")
    output_dir = _CONFIG.get("paths", {}).get("output_dir", "output")
    for key in list(_CONFIG.get("paths", {}).keys()):
        if key.endswith("_dir"):
            raw = _CONFIG["paths"][key]
            _CONFIG["paths"][key] = os.path.abspath(os.path.join(data_dir, raw))
            _ensure_dir(_CONFIG["paths"][key])


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def get_config() -> Dict[str, Any]:
    if not _CONFIG:
        load_config()
    return _CONFIG

def _get_nested(cfg: Dict[str, Any], key: str, default=None) -> Any:
    parts = key.split(".")
    val = cfg
    for p in parts:
        if isinstance(val, dict):
            val = val.get(p)
        else:
            return default
    return val if val is not None else default


def get(key: str, default=None) -> Any:
    global _SETTINGS
    # 1. Try env var override first (highest priority)
    env_key = _ENV_PREFIX + key.replace(".", "_").upper()
    env_val = os.environ.get(env_key)
    if env_val is not None:
        cfg = get_config()
        dft = _get_nested(cfg, key, default)
        return _coerce_env(env_val, dft)

    # 2. Try Settings dataclass (if loaded via load_config(as_settings=True))
    if _SETTINGS is not None:
        parts = key.split(".")
        if len(parts) == 2:
            section, setting = parts
            if hasattr(_SETTINGS, section):
                sec = getattr(_SETTINGS, section)
                if isinstance(sec, dict) and setting in sec:
                    return sec[setting]

    # 3. Fall back to dict config
    return _get_nested(get_config(), key, default)

def path_for(key: str) -> str:
    raw = get(f"paths.{key}", "")
    if not raw:
        return ""
    data_dir = get("paths.data_dir", ".")
    return os.path.abspath(os.path.join(data_dir, raw))


def atomic_write_json(path: str, data):
    """Thread-safe atomic JSON write — never exposes partial output."""
    with _FILE_LOCK:
        tmp = path + ".tmp"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)


def atomic_read_json(path: str):
    """Atomic JSON read — no lock needed because os.replace in atomic_write_json provides atomicity."""
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)
