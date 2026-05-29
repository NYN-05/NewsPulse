# Production Stability Assessment

**Date:** 2026-05-29  
**Scope:** Full-stack — pipeline, API, frontend, vector stores, scrapers  
**Coverage:** 31 Python files, 1 TypeScript file, 1 config file, 1 requirements file  
**Method:** Manual code audit + static analysis + benchmark validation

---

## 1. Architecture & Data Flow

```
┌─────────────┐    ┌──────────────┐    ┌───────────────┐    ┌──────────────────┐
│  Scrapers   │───▶│  DataFrame   │───▶│  NLP/Analysis │───▶│  Intelligence    │
│  (4 web +   │    │  Storage     │    │  (entities,   │    │  Engine          │
│   118 RSS)  │    │  (Parquet/   │    │   dedup,      │    │  (graph, agents, │
│             │    │   CSV)       │    │   sentiment)  │    │   temporal, etc) │
└─────────────┘    └──────────────┘    └───────────────┘    └────────┬─────────┘
                                                                    │
                    ┌───────────────────────────────────────────────┘
                    ▼
┌─────────────┐    ┌──────────────┐    ┌──────────────────────────┐
│  Frontend   │◀───│  FastAPI     │◀───│  JSON output files       │
│  (React 19) │    │  (port 8765) │    │  (atomic writes)         │
│             │    │  + WebSocket │    │                          │
│             │    │  + APSched.  │    │  ChromaDB  ─── optional  │
│             │    │              │    │  Neo4j     ─── optional  │
└─────────────┘    └──────────────┘    └──────────────────────────┘
```

**Critical path dependencies (degradation if absent):**
| Component | Degradation behavior |
|---|---|
| Ollama (qwen3:14b) | Statistical-only analysis, no LLM verification |
| GLiNER | HF NER fallback → regex fallback |
| BERTopic | Keyword-based clustering |
| GPU | CPU fallback (slower, same results) |
| ChromaDB | Search returns error message, pipeline runs normally |
| Neo4j | Skipped, pipeline continues |
| Internet | Empty scrape results → no data to analyze |

---

## 2. Regression Risk Analysis

### 2.1 `itertuples()` migration (10 files, 25+ call sites)

| File | Risk | Status |
|---|---|---|
| `vector_store/chroma_store.py` | **CRITICAL** — was using `row.get()` on namedtuple | ✅ FIXED |
| `storage/manager.py` | Low — uses `getattr(a, ...)` | ✅ Clean |
| `intelligence/entity_graph.py` | Low — uses `get_entity_dict()` | ✅ Clean |
| `intelligence/relationships.py` | Low — uses `get_entity_dict()` + `getattr` | ✅ Clean |
| `intelligence/narratives.py` | Low — uses `getattr(row, ...)` | ✅ Clean |
| `intelligence/signals.py` | Low — uses `get_entity_dict()` + `getattr` | ✅ Clean |
| `intelligence/causal.py` | Low — uses `get_entity_dict()` | ✅ Clean |
| `intelligence/temporal.py` | Low — uses `get_entity_dict()` + `getattr` | ✅ Clean |
| `pipeline.py` | Low — uses `getattr(row, ...)` | ✅ Clean |

**Regression verdict: SAFE** — all 25+ call sites use namedtuple-safe attribute access.

### 2.2 List comprehension json.loads (pipeline.py:190)

```python
to_analyze["_parsed_entities"] = [json.loads(e) for e in to_analyze["entities"]]
```
- **Edge case**: `entities` column contains NaN from CSV reload → `json.loads(float("nan"))` raises `TypeError`.
- **Reality**: `extract_entities_batch` always returns JSON strings. CSV round-trip preserves strings. Only risk is manual corruption.
- **Downstream protection**: `get_entity_dict()` catches `json.JSONDecodeError` and `TypeError`.
- **Verdict**: LOW risk, protected downstream.

### 2.3 Confidence consolidation (relationships.py + confidence.py)

| Concern | Detail | Verdict |
|---|---|---|
| `_calibrate_confidence` sets `_llm_result` | Only called when LLM succeeds | ✅ Correct |
| `calibrate_relationship_confidence` pops `_llm_result` | Single pop — first call consumes it | ✅ Correct |
| Multiple calibration calls on same link | `pop()` returns None on second call, graceful fallback | ✅ Safe |
| LLM signal weight | 20% if verified, 10% if not (was previously discarded) | ✅ Bug fixed |

**Verdict: SAFE** — verified via benchmark functional tests.

### 2.4 Settings dataclass activation

- Previously: `_SETTINGS` never populated, `get()` always fell through to `_CONFIG`.
- Now: `load_config(as_settings=True)` populates `_SETTINGS` in `main.py`.
- **Key concern**: Settings paths are relative strings (e.g., `"output"`) while `_CONFIG` has resolved absolute paths. `get()` returns Settings values first.
- **Mitigation**: `path_for()` independently resolves paths via `os.path.abspath(os.path.join(data_dir, raw))`.
- **Code audit**: No direct `get("paths.*")` path value usage — all path access goes through `path_for()`.
- **Verdict**: SAFE — path resolution is self-healing.

---

## 3. Broken Functionality

### 3.1 Previously broken and FIXED
| Issue | File | Fix |
|---|---|---|
| `row.get()` on namedtuple | `chroma_store.py:99-102` | `getattr()` |
| `hash(link)` unstable IDs | `chroma_store.py:94` | `hashlib.md5` |
| `path_for()` wrong key | `alerting.py:141` | `os.path.join(path_for("output_dir"), ...)` |
| Dead `import json` | `temporal.py`, `causal.py`, `narratives.py` | Removed |
| Dead `_IS_CUDA` / `callable` guard | `gpu_manager.py` | Removed |
| `df.copy()` in `signals.py` | `signals.py:83` | Converted to `df.assign()` |
| Settings dataclass inert | `main.py:27` | `as_settings=True` |

### 3.2 Still broken (minor)
| Issue | Impact | Workaround |
|---|---|---|
| `alerting.py:141` — no history file exists yet | All relationships appear "new" on first run | ✅ Resolves after first pipeline run creates the file |
| Frontend types manually maintained | Type drift over time | Manual sync needed |

### 3.3 Not broken (verified functional)
- Entity parsing: old vs new data ✅
- Confidence calibration: all 6 signals ✅
- Pipeline cleanup: all phases ✅
- APScheduler: start/stop ✅
- bcrypt auth: hash/verify ✅
- Pydantic models: serialization ✅

---

## 4. Edge-Case Failure Analysis

### 4.1 Empty DataFrame propagation

```
scrape → empty df → dedup loads from disk → fetch loads from disk → analyze loads from disk
```

Every step handles empty DataFrames:
- `step_dedup`: `df.empty` → fallback to `load_raw()` ✅
- `step_analyze`: `to_analyze.empty` → return old data ✅
- `build_entity_graph`: `df.empty` → return error dict ✅
- `find_cross_domain_links`: empty → return `[]` ✅
- `compute_entity_narratives`: empty → return `[]` ✅

**Verdict**: ROBUST — no empty-df crash path found.

### 4.2 NaN/Inf in JSON output

| Location | Guard | Safe? |
|---|---|---|
| `_clean()` in main.py | Recursive NaN→None conversion | ✅ On read path |
| `np.mean(links)` in relationships.py | `if cross_links else 0` | ✅ |
| `np.mean(src_rels)` in confidence.py | `if src_rels else 0.5` | ✅ |
| `np.mean(sims)` in relationships.py | `if sims else 0.0` | ✅ |
| `np.mean(...)` in briefings.py | `if relevant_links else 0` | ✅ |

**Edge case found**: `predict_cross_domain_impact` does `min(link.get("confidence", 0.5) * 1.2, 1.0)`. If confidence is `None`, `None * 1.2` raises `TypeError`. But looking at the code flow:
- `find_cross_domain_links` sets `"confidence": None` (line 355)
- `apply_llm_verification` calls `_calibrate_confidence` which sets `_llm_result` but NOT `confidence`
- `predict_cross_domain_impact` is called after `apply_llm_verification` but BEFORE `apply_confidence_calibration`

Wait! Let me re-examine the pipeline:
```python
cross_links = apply_llm_verification(cross_links, dict(pair_texts))
cross_links = predict_cross_domain_impact(cross_links, sector_map)
impact_chains = build_impact_chains(df, sector_map)
cross_links = generate_relationship_explanations(cross_links, sector_map)
```

`apply_llm_verification` calls `_calibrate_confidence` which sets `_llm_result` but not `confidence`. Then `predict_cross_domain_impact` reads `link.get("confidence", 0.5)` — which is still `None` (set to None in `find_cross_domain_links`).

Wait — `link.get("confidence", 0.5)` with `"confidence": None`... The default `0.5` is only used if the key is missing. Since the key exists with value `None`, `link.get("confidence", 0.5)` returns `None`. Then `None * 1.2` raises `TypeError`.

**BUG CONFIRMED**: `predict_cross_domain_impact` crashes on all links when confidence is None (which it always is, because `_calibrate_confidence` doesn't set it).

Wait, let me re-check. `_calibrate_confidence`:
```python
def _calibrate_confidence(link: Dict, llm_result: Optional[Dict] = None) -> Dict:
    if llm_result:
        link["verified"] = llm_result.get("verified", True)
        ...
        link["_llm_result"] = llm_result
    return link
```

It does NOT set `link["confidence"]`. So confidence stays None from `find_cross_domain_links`.

Then `predict_cross_domain_impact` line 260:
```python
adjusted_likelihood = pattern["likelihood"] * min(link.get("confidence", 0.5) * 1.2, 1.0)
```

`link.get("confidence", 0.5)` returns `None` (key exists, value is None). `None * 1.2` raises `TypeError`.

**RISK**: MEDIUM-HIGH — this would crash the pipeline during `step_cross_domain` whenever confidence is None (always, since consolidation happens later).

But wait... the benchmark test passed. Let me look at the confidence flow again more carefully.

Actually, looking at the output JSON file, there's no `apply_confidence_calibration` called anywhere in `cross_domain_pipeline`. Let me search...

Looking at `cross_domain_pipeline()` (line 506):
```python
cross_links = apply_llm_verification(cross_links, dict(pair_texts))
cross_links = predict_cross_domain_impact(cross_links, sector_map)
cross_links = generate_relationship_explanations(cross_links, sector_map)
```

No `apply_confidence_calibration` call! The confidence calibration step is MISSING. The links have `confidence: None` when they reach `predict_cross_domain_impact`.

So the question is: does `None * 1.2` crash or not?
- `min(None * 1.2, 1.0)` → `None * 1.2` raises `TypeError: unsupported operand type(s) for *: 'NoneType' and 'float'`

Wait, let me check Line 260 again:
```python
adjusted_likelihood = pattern["likelihood"] * min(link.get("confidence", 0.5) * 1.2, 1.0)
```

Hmm, actually `min(link.get("confidence", 0.5) * 1.2, 1.0)` — `link.get("confidence", 0.5)` would return `None` because "confidence" key exists with value `None`. `None * 1.2` → TypeError.

But actually, let me look at the generated `cross_domain_links.json` to see what's actually in there. The benchmark test might not have exercised this code path.

Actually, the benchmark test (`validate_benchmarks.py`) imports modules but doesn't run `cross_domain_pipeline` with real data. It tests `_calibrate_confidence` directly and `calibrate_relationship_confidence` directly, but NOT `predict_cross_domain_impact`.

So this IS a bug, but I need to verify:
1. Does `link.get("confidence", 0.5)` return `None` when `"confidence": None`?
2. Does the pipeline actually call `predict_cross_domain_impact` with links that have `None` confidence?

Answer to 1: YES — `dict.get()` returns the value if key exists, even if value is None. Default is only used if key is MISSING.

Answer to 2: YES — `_calibrate_confidence` doesn't set `link["confidence"]`, only `link["_llm_result"]`.

So `predict_cross_domain_impact` will crash with `TypeError` on every link.

**This is a NEWLY DISCOVERED CRITICAL BUG** introduced by the confidence consolidation change. Previously, `_calibrate_confidence` would compute confidence inline (via the redundant formula), so confidence was always set. Now it defers to `calibrate_relationship_confidence` which is never called by the cross_domain_pipeline flow.

The fix: either call `calibrate_relationship_confidence` in `cross_domain_pipeline`, or have `_calibrate_confidence` set a default confidence of 0.5.

This is actually a HIGH or CRITICAL issue.

Let me also check line 268 and 272 for the same pattern:
```python
link["impact"] = {
    ...
    "confidence_weighted": round(adjusted_likelihood * link.get("confidence", 0.5), 3),
}
```

Same bug — `link.get("confidence", 0.5)` returns `None`.

OK I need to add this to the report. This is actually the most important finding.

Let me also check line 110:
```python
adjusted_likelihood = pattern["likelihood"] * min(link.get("confidence", 0.5) * 1.2, 1.0)
```

and line 271:
```python
"likelihood": round(0.5 * link.get("confidence", 0.5), 3),
```

And `predict_cross_domain_impact` line 260, 265, 268:
```python
adjusted_likelihood = pattern["likelihood"] * min(link.get("confidence", 0.5) * 1.2, 1.0)
...
"confidence_weighted": round(adjusted_likelihood * link.get("confidence", 0.5), 3),
```

And line 269-272:
```python
"predicted_effect": "Cross-domain propagation",
"likelihood": round(0.5 * link.get("confidence", 0.5), 3),
...
"confidence_weighted": round(0.5 * link.get("confidence", 0.5), 3),
```

All of these would crash with `None * float`.

**CRITICAL BUG**: The pipeline will crash in `predict_cross_domain_impact` at `step_cross_domain` every time.

Now let me also check line 551 — `avg_confidence` in the summary:
```python
"avg_confidence": round(float(np.mean([l.get("confidence", 0) for l in cross_links])), 3) if cross_links else 0,
```
This uses `.get("confidence", 0)` — same pattern but the default 0 is only used if key is MISSING. Since key exists with None, it returns None. `np.mean([None, None])` → this would raise TypeError too, because `None` can't be converted to float by numpy.

Wait, actually `np.mean([None, None])` returns `nan` in newer numpy versions? Let me think... `np.mean` tries to convert to float. `float(None)` → TypeError. So `np.mean([None, 0.5])` would crash.

But actually, the list comprehension is `[l.get("confidence", 0) for l in cross_links]` — if confidence is None (because key exists with None value), the list contains `[None, None, ...]`. `np.mean([None])` → TypeError.

Actually, in numpy >= 1.20, `np.mean([None])` → `nan` with a warning. But in numpy 1.26.4 (pinned in requirements.txt), let me check... `np.mean([None])` converts to `np.array([None])` which has dtype object, and `np.mean` tries to compute mean of objects. This might actually work and return `nan` or it might crash.

Hmm, the benchmark test passed. Let me check what the test does...

Actually, the benchmark test (`validate_benchmarks.py`) tests confidence consolidation by directly testing `_calibrate_confidence` and `calibrate_relationship_confidence`. It doesn't test `predict_cross_domain_impact`. So this path was never exercised.

OK so I have found a CRITICAL bug. Let me include it in the report.

Actually wait, I need to re-read the test more carefully. The validation output says:
```
Consolidated confidence | LLM fields set, confidence deferred | OK
Consolidated confidence | confidence.py picks up _llm_result | OK
Consolidated confidence | no-LLM fallback | OK
```

These test the confidence functions in isolation. They don't test the end-to-end flow through `cross_domain_pipeline`. So the bug would be caught by integration testing but not by unit testing.

This is a classic integration gap bug. The confidence consolidation split `_calibrate_confidence` into two phases (LLM field setting and full calibration), but the second phase call (`calibrate_relationship_confidence`) was never wired into the `cross_domain_pipeline` flow.

Let me update the report with this finding.

Also let me re-examine: is there actually an `apply_confidence_calibration` function anywhere? Let me search.<｜end▁of▁thinking｜>

<｜｜DSML｜｜tool_calls>
<｜｜DSML｜｜invoke name="grep">
<｜｜DSML｜｜parameter name="pattern" string="true">apply_confidence_calibration|calibrate_relationship_confidence