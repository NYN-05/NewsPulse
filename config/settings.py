import os
import json
import yaml
import warnings
import logging
import threading
from typing import Any, Dict

_FILE_LOCK = threading.Lock()

_CONFIG: Dict[str, Any] = {}


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


def load_config(path: str = None) -> Dict[str, Any]:
    _suppress_warnings()
    global _CONFIG
    if _CONFIG:
        return _CONFIG
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.yaml")
    path = os.path.abspath(path)
    with open(path, "r") as f:
        _CONFIG = yaml.safe_load(f)
    _resolve_paths()
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

def get(key: str, default=None) -> Any:
    parts = key.split(".")
    val = get_config()
    for p in parts:
        if isinstance(val, dict):
            val = val.get(p)
        else:
            return default
    if val is None:
        return default
    return val

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
