import json
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

_gliner = None

LABELS = ["person", "organization", "location", "political entity", "technology", "financial entity", "energy company", "military"]


def _get_gliner():
    global _gliner
    if _gliner is None:
        try:
            from gliner import GLiNER
            logger.info("Loading GLiNER model: urchade/gliner_large-v2")
            _gliner = GLiNER.from_pretrained("urchade/gliner_large-v2")
        except Exception as e:
            logger.error("Failed to load GLiNER: %s", e)
    return _gliner


def extract_entities(text: str, threshold: float = 0.5) -> Dict[str, List[str]]:
    model = _get_gliner()
    if model is None:
        return {"persons": [], "orgs": [], "locations": []}
    entities = model.predict_entities(text, LABELS, threshold=threshold)
    result = {"persons": [], "orgs": [], "locations": []}
    seen = set()
    for e in entities:
        label = e.get("label", "")
        text_val = e.get("text", "").strip()
        if not text_val or text_val.lower() in seen:
            continue
        seen.add(text_val.lower())
        if label in ("person",):
            result["persons"].append(text_val)
        elif label in ("organization", "political entity"):
            result["orgs"].append(text_val)
        elif label in ("location",):
            result["locations"].append(text_val)
        elif label in ("technology", "financial entity", "energy company"):
            result["orgs"].append(text_val)
    return result


def extract_entities_batch(texts: List[str]) -> List[str]:
    results = []
    for text in texts:
        entities = extract_entities(str(text)[:2000])
        results.append(json.dumps(entities))
    return results
