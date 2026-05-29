import json
import logging
import re
from typing import List, Dict

logger = logging.getLogger(__name__)

_gliner = None
_hf_ner = None

LABELS = ["person", "organization", "location", "political entity", "technology", "financial entity", "energy company", "military"]

# Simple regex fallback for common named entities
_RE_PERSON = re.compile(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b')
_RE_ORG = re.compile(r'\b([A-Z][A-Za-z]*(?:\s+[A-Z][A-Za-z]*){1,4})\b')
_SKIP_WORDS = {"The", "This", "That", "These", "Those", "What", "When", "Where", "Why", "How", "After", "Before", "During", "While", "With", "From", "Into", "About", "Until", "Since"}


def _get_gliner():
    global _gliner
    if _gliner is None:
        try:
            from gliner import GLiNER
            logger.info("Loading GLiNER model: urchade/gliner_large-v2")
            _gliner = GLiNER.from_pretrained("urchade/gliner_large-v2")
            return _gliner
        except ImportError:
            logger.info("GLiNER not installed — using HuggingFace NER fallback")
            return None
        except Exception as e:
            logger.warning("GLiNER load failed: %s — using fallback NER", e)
            return None
    return _gliner


def _get_hf_ner():
    global _hf_ner
    if _hf_ner is None:
        try:
            from transformers import pipeline
            logger.info("Loading HuggingFace NER pipeline (dslim/bert-base-NER)")
            _hf_ner = pipeline("token-classification", model="dslim/bert-base-NER", aggregation_strategy="simple")
        except Exception as e:
            logger.warning("HF NER pipeline failed: %s", e)
    return _hf_ner


def _extract_regex(text: str) -> Dict[str, List[str]]:
    persons = []
    orgs = []
    locations = []
    words = text.split()
    for m in _RE_PERSON.finditer(text):
        name = m.group(1).strip()
        first = name.split()[0]
        if first not in _SKIP_WORDS and len(name) > 4:
            persons.append(name)
    known_orgs = [
        "White House", "Federal Reserve", "European Union", "United Nations",
        "World Bank", "IMF", "NATO", "Pentagon", "Congress", "Senate",
        "Supreme Court", "House of Representatives", "State Department",
        "Department of Defense", "Treasury Department", "Wall Street",
        "Silicon Valley", "OpenAI", "Google", "Microsoft", "Apple",
        "Amazon", "Meta", "Tesla", "NVIDIA", "Intel", "TSMC", "Samsung",
    ]
    for org in known_orgs:
        if org.lower() in text.lower():
            orgs.append(org)

    known_locations = [
        "United States", "China", "Russia", "Ukraine", "Iran", "Israel",
        "Europe", "Middle East", "Washington", "Moscow", "Beijing",
        "London", "Tokyo", "New York", "California", "Texas",
    ]
    for loc in known_locations:
        if loc.lower() in text.lower():
            locations.append(loc)

    return {
        "persons": list(set(persons))[:10],
        "orgs": list(set(orgs))[:10],
        "locations": list(set(locations))[:10],
    }


def _extract_hf(text: str) -> Dict[str, List[str]]:
    ner = _get_hf_ner()
    if ner is None:
        return _extract_regex(text)
    try:
        results = ner(text[:2000])
        persons = []
        orgs = []
        locations = []
        seen = set()
        for r in results:
            word = r.get("word", "").strip()
            entity_group = r.get("entity_group", r.get("label", ""))
            if not word or word.lower() in seen:
                continue
            seen.add(word.lower())
            if entity_group in ("PER", "person"):
                persons.append(word)
            elif entity_group in ("ORG", "organization"):
                orgs.append(word)
            elif entity_group in ("LOC", "location", "GPE"):
                locations.append(word)
        return {
            "persons": persons[:10],
            "orgs": orgs[:10],
            "locations": locations[:10],
        }
    except Exception as e:
        logger.debug("HF NER error: %s", e)
        return _extract_regex(text)


def extract_entities(text: str, threshold: float = 0.5) -> Dict[str, List[str]]:
    model = _get_gliner()
    if model is not None:
        try:
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
                elif label in ("organization", "political entity", "technology", "financial entity", "energy company"):
                    result["orgs"].append(text_val)
                elif label in ("location",):
                    result["locations"].append(text_val)
            return result
        except Exception as e:
            logger.debug("GLiNER inference error: %s", e)
    return _extract_hf(text)


def get_entity_dict(row) -> Dict[str, List[str]]:
    """Get parsed entities from a DataFrame row (itertuples or dict-like).

    Checks _parsed_entities column first (pre-parsed), falls back to parsing
    the entities JSON string.
    """
    entities = getattr(row, "_parsed_entities", None)
    if isinstance(entities, dict):
        return entities
    raw = getattr(row, "entities", "{}")
    if isinstance(raw, str) and raw:
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            pass
    return {"persons": [], "orgs": [], "locations": []}


def extract_entities_batch(texts: List[str]) -> List[str]:
    results = []
    for text in texts:
        entities = extract_entities(str(text)[:2000])
        results.append(json.dumps(entities))
    return results
