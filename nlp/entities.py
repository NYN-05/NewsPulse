import json
import logging
from functools import lru_cache
from typing import List

logger = logging.getLogger(__name__)

_gpu_pipeline = None
HAS_SPACY = False


def _try_load_spacy():
    global HAS_SPACY
    try:
        import spacy
        global _nlp
        _nlp = spacy.load("en_core_web_sm", disable=["parser", "lemmatizer"])
        HAS_SPACY = True
        logger.info("Using spaCy for NER")
    except Exception:
        HAS_SPACY = False
        logger.info("spaCy not available, falling back to NLTK for NER")


def _get_gpu_ner():
    global _gpu_pipeline
    if _gpu_pipeline is not None:
        return _gpu_pipeline
    from compute.gpu_manager import GPUManager, is_cuda
    if is_cuda():
        try:
            mgr = GPUManager()
            _gpu_pipeline = mgr.get_pipeline("ner")
        except Exception as e:
            logger.warning("GPU NER init failed: %s", e)
    return _gpu_pipeline


@lru_cache(maxsize=1024)
def _extract_entities_gpu(text: str) -> str:
    pipe = _get_gpu_ner()
    if pipe is None:
        return json.dumps({"persons": [], "orgs": [], "locations": []})
    try:
        results = pipe(text[:10000], aggregation_strategy="simple")
        persons, orgs, locs = [], [], []
        seen = set()
        for r in results:
            ent = r["word"]
            key = (r["entity_group"], ent.lower())
            if key in seen:
                continue
            seen.add(key)
            if r["entity_group"] == "PER":
                persons.append(ent)
            elif r["entity_group"] == "ORG":
                orgs.append(ent)
            elif r["entity_group"] == "LOC":
                locs.append(ent)
        return json.dumps({
            "persons": persons[:5],
            "orgs": orgs[:5],
            "locations": locs[:5],
        })
    except Exception as e:
        logger.warning("GPU NER failed (%s), will use CPU fallback next call", e)
        return json.dumps({"persons": [], "orgs": [], "locations": []})


@lru_cache(maxsize=1024)
def _extract_entities_spacy(text: str) -> str:
    import spacy
    nlp = spacy.load("en_core_web_sm", disable=["parser", "lemmatizer"])
    doc = nlp(text[:10000])
    persons, orgs, locs = [], [], []
    seen = set()
    for ent in doc.ents:
        key = (ent.label_, ent.text.lower())
        if key in seen:
            continue
        seen.add(key)
        if ent.label_ == "PERSON":
            persons.append(ent.text)
        elif ent.label_ in ("ORG", "GPE"):
            orgs.append(ent.text)
        elif ent.label_ == "LOC":
            locs.append(ent.text)
    return json.dumps({
        "persons": list(dict.fromkeys(persons))[:5],
        "orgs": list(dict.fromkeys(orgs))[:5],
        "locations": list(dict.fromkeys(locs))[:5],
    })


@lru_cache(maxsize=1024)
def _extract_entities_nltk(text: str) -> str:
    from nltk import pos_tag, ne_chunk, word_tokenize
    if not isinstance(text, str) or len(text) < 20:
        return json.dumps({"persons": [], "orgs": [], "locations": []})
    tokens = word_tokenize(text)
    tagged = pos_tag(tokens[:200])
    ne_tree = ne_chunk(tagged)
    persons, orgs, locs = set(), set(), set()
    for subtree in ne_tree:
        if hasattr(subtree, "label"):
            entity = " ".join(word for word, tag in subtree.leaves())
            if subtree.label() == "PERSON":
                persons.add(entity)
            elif subtree.label() in ("ORGANIZATION", "GPE"):
                orgs.add(entity)
    return json.dumps({
        "persons": list(persons)[:5],
        "orgs": list(orgs)[:5],
        "locations": list(locs)[:5],
    })


def extract_entities(text: str) -> str:
    if not isinstance(text, str) or len(text) < 20:
        return json.dumps({"persons": [], "orgs": [], "locations": []})
    if _get_gpu_ner() is not None:
        result = _extract_entities_gpu(text)
        if result != json.dumps({"persons": [], "orgs": [], "locations": []}):
            return result
    global HAS_SPACY
    if not HAS_SPACY:
        _try_load_spacy()
    if HAS_SPACY:
        return _extract_entities_spacy(text)
    return _extract_entities_nltk(text)


def extract_entities_batch(texts: List[str]) -> List[str]:
    pipe = _get_gpu_ner()
    if pipe is None:
        return [extract_entities(t) for t in texts]
    valid_indices = [i for i, t in enumerate(texts) if isinstance(t, str) and len(t) >= 20]
    if not valid_indices:
        return [extract_entities(t) for t in texts]
    valid_texts = [texts[i] for i in valid_indices]
    try:
        all_results = pipe(valid_texts, batch_size=32, aggregation_strategy="simple")
        results = [json.dumps({"persons": [], "orgs": [], "locations": []})] * len(texts)
        for batch_idx, idx in enumerate(valid_indices):
            entities = all_results[batch_idx] if batch_idx < len(all_results) else []
            persons, orgs, locs = [], [], []
            seen = set()
            for r in entities:
                ent = r["word"]
                key = (r["entity_group"], ent.lower())
                if key in seen:
                    continue
                seen.add(key)
                if r["entity_group"] == "PER":
                    persons.append(ent)
                elif r["entity_group"] == "ORG":
                    orgs.append(ent)
                elif r["entity_group"] == "LOC":
                    locs.append(ent)
            results[idx] = json.dumps({"persons": persons[:5], "orgs": orgs[:5], "locations": locs[:5]})
        return results
    except Exception as e:
        logger.warning("GPU batch NER failed (%s), falling back to CPU", e)
        return [extract_entities(t) for t in texts]
