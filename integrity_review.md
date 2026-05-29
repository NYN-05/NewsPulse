# NewsPulse — Comprehensive Integrity Review

**Date:** 2026-05-29  
**Scope:** All Phases 1-5 + 5 targeted optimizations  
**Inspected:** 29 files across 11 packages

---

## Summary

| Category | Critical | High | Medium | Low |
|---|---|---|---|---|
| Functional Correctness | 1 | 2 | 0 | 0 |
| Architectural Consistency | 0 | 2 | 1 | 1 |
| Coding Standards | 0 | 0 | 2 | 1 |
| Dependency Integrity | 0 | 0 | 4 | 0 |
| Configuration | 0 | 0 | 0 | 1 |
| Security | 0 | 0 | 1 | 0 |
| Error Handling | 0 | 0 | 1 | 0 |
| Data Consistency | 0 | 0 | 0 | 0 |

**Total: 1 Critical, 4 High, 9 Medium, 3 Low**

---

## CRITICAL

### C1. `chroma_store.py:99` — namedtuple `.get()` raises AttributeError at runtime

**File:** `vector_store/chroma_store.py:99`  
**Introduced by:** `itertuples()` migration in Phase 1

`itertuples()` returns namedtuples, which support attribute access via `getattr(row, "col")` but do **not** have a `.get()` dict method. Four lines in `index_articles()` use `row.get(...)` instead of `getattr(row, ..., "")`:

```python
for row in df.itertuples():
    ...
    metadatas.append({
        "source": str(row.get("source", "") or ""),      # L99 — BUG
        "published": str(row.get("published", "") or ""), # L100 — BUG
        "category": str(row.get("category", "") or ""),   # L101 — BUG
        "sentiment": str(row.get("sentiment", "") or ""), # L102 — BUG
    })
```

**Consequence:** `index_articles()` crashes immediately when called at the end of `run_pipeline()`. Vector indexing is **completely broken**.

**Fix:** Replace with `getattr(row, "source", "")` etc.

---

## HIGH

### H1. `load_config(as_settings=True)` never called — Settings dataclass is dead code

**File:** `config/settings.py:158-160`  
**Introduced by:** Phase 5

The `Settings` dataclass with env var override, DI support, and typed defaults exists but is **never activated**. All calls:

| Caller | Call | `as_settings` |
|---|---|---|
| `pipeline.py:81` | `load_config()` | `False` (default) |
| `dashboard/backend/main.py:27` | `load_config()` | `False` (default) |
| `config/settings.py:150` | `if _CONFIG and not as_settings: return` | — |

`_SETTINGS` remains `None` through every code path. The `get()` function's Settings branch (line 203) is never reached unless `load_config(as_settings=True)` is explicitly called.

**Consequence:** Env var override `NEWSPULSE_*` still works (via the `get()` function's env check at line 194), but typed defaults, structured config loading, and DI support are inert.

**Fix:** Either:
  (a) `dashboard/backend/main.py:27`: Change to `load_config(as_settings=True)`  
  (b) Or remove the `Settings` dataclass entirely if unused

(a) is recommended — the Settings dataclass is well-designed and should be the primary config mechanism.

### H2. `alerting.py:141-142` — missing path config breaks history tracking

**File:** `intelligence/alerting.py:141`  
**Pre-existing** (not introduced by our changes)

```python
previous_links = atomic_read_json(path_for("cross_domain_links_history") or
                                  path_for("cross_domain_links"))
```

Neither `"cross_domain_links_history"` nor `"cross_domain_links"` exists in `config.yaml` under `paths:`. `path_for()` returns `""` for both, so `atomic_read_json("")` returns `None`, and `previous_links` becomes `[]`.

**Consequence:** Every `eval_relationship_alerts` pass sees no previous relationships. All existing relationships appear "new", generating false-positive alerts on every pipeline run.

**Fix:** Add to `config.yaml`:
```yaml
paths:
  cross_domain_links: "output/data/cross_domain_links.json"
  cross_domain_links_history: "output/data/cross_domain_links_history.json"
```
Or derive from `output_dir` directly.

### H3. Two separate Ollama session pools — wasted connections

**File:** `intelligence/relationships.py:27` and `intelligence/agents.py:21`  
**Introduced by:** Phase 1 (relationships) and Phase 4 (agents)

Two independent `requests.Session()` instances manage Ollama connections:
- `relationships.py`: `_LLM_SESSION` — closed by `close_llm_session()`
- `agents.py`: `_OLLAMA_SESSION` — closed by `close_ollama_session()`

Both connect to `localhost:11434/api/generate` with the same model. Each pool maintains a separate TCP connection, doubling connection overhead for no benefit. Both are correctly closed by `pipeline_cleanup()`.

**Fix:** Consolidate into a single shared session, likely in `intelligence/agents.py` (since it has the more general `_ollama_generate` function), and have `relationships.py` import and use it.

**Priority:** Medium — the perf impact is small since both run sequentially in the pipeline.

### H4. `chroma_store.py:94` — `hash(link)` yields unstable cross-run document IDs

**File:** `vector_store/chroma_store.py:94`  
**Pre-existing**

```python
doc_id = f"article_{hash(link) % 10**12}" if link else f"article_{_id_generator()}"
```

Python's `hash()` is salted per interpreter run (`PYTHONHASHSEED`). The same URL produces a different `doc_id` every time the server restarts. This causes ChromaDB to **accumulate duplicate entries** across pipeline runs.

**Consequence:** Vector database grows unboundedly with duplicates. Semantic search returns increasingly polluted results.

**Fix:** Use a deterministic hash:
```python
import hashlib
doc_id = f"article_{hashlib.md5(link.encode()).hexdigest()[:12]}" if link else ...
```

---

## MEDIUM

### M1. Dead imports: `json` in 3 intelligence files

| File | Line | Status |
|---|---|---|
| `intelligence/temporal.py` | 11 | `import json` — never referenced |
| `intelligence/causal.py` | 10 | `import json` — never referenced |
| `intelligence/narratives.py` | 11 | `import json` — never referenced |

Likely leftover from earlier versions that called `json.loads()` or `json.dumps()` directly. No functional impact but violates import hygiene.

### M2. Dead code: `_IS_CUDA` in `gpu_manager.py`

**File:** `compute/gpu_manager.py:115`

```python
_IS_CUDA = is_cuda()  # cache result, use callable check in __init__
```

`_IS_CUDA` is set at module level but **never read** anywhere in the codebase. The `__init__` method uses its own `callable(is_cuda)` check instead. This appears to be leftover from the earlier `is_cuda()` shadowing bug fix.

### M3. `GPUManager.__init__` — `callable(is_cuda)` check is always True

**File:** `compute/gpu_manager.py:69`

```python
self.cuda = is_cuda() if callable(is_cuda) else bool(is_cuda)
```

At `__init__` time, `is_cuda` is the module-level function (not shadowed by a bool). `callable(is_cuda)` is always True, making the `else bool(is_cuda)` branch dead code. This was a safety guard from the earlier bug fix but no longer serves a purpose.

### M4. `path_for()` redundant `os.path.abspath` when path already absolute

**File:** `config/settings.py:219`

`_resolve_paths()` already converts `_dir` paths to absolute. When `path_for()` is called for an already-resolved path, `os.path.abspath(os.path.join(absolute_data_dir, absolute_path))` works on Windows (where `os.path.join` ignores leading components when a later component is absolute) but is conceptually redundant.

No functional bug — just ~20µs of wasted computation per call.

### M5. Remaining `df.copy()` in `signals.py:83`

**File:** `intelligence/signals.py:83`

```python
df = df.copy()
df["_date"] = pd.to_datetime(df[time_col], errors="coerce")
```

This `df.copy()` was intentionally left when the other 4 in `narratives.py` were removed, because `detect_cross_domain_spillover` adds a temporary column and wants to avoid `SettingWithCopyWarning`. Could be converted to `df.assign()` for consistency:

```python
df = df.assign(_date=pd.to_datetime(df[time_col], errors="coerce")).dropna(subset=["_date"])
```

### M6. `_INTEL_CACHE` in `main.py` — no thread safety

**File:** `dashboard/backend/main.py:225-250`

The API cache (`_INTEL_CACHE`) is a plain `dict` read by `_load_intel()` (called from API endpoints via `threading.Thread` pool) and cleared by `_run_pipeline()` (called from APScheduler background thread). No lock protects it.

In practice: a cache clear during a concurrent read could return stale data or cause a transient `KeyError` that is caught. Window is tiny. Consider `threading.Lock` or `copy-on-write` pattern.

### M7. `dashboard/backend/main.py:88` — inline `import pandas pd`

Importing `pandas` inside `_run_pipeline()` at line 88 violates the "module-scope imports" convention. Minor — `pandas` is already imported elsewhere so it's in the import cache by this point.

### M8. `auth.py:94-99` — placeholder JWT auth

**File:** `dashboard/backend/auth.py:90-100`

```python
def require_role(required_role: str):
    min_level = ROLES.get(required_role, 0)
    def checker(request: Request):
        role = request.headers.get("X-User-Role", "viewer")
        if ROLES.get(role, 0) < min_level:
            raise HTTPException(status_code=403, detail=f"Requires {required_role} role")
        return True
    return checker
```

Auth relies entirely on the `X-User-Role` header with no signature verification. A client can impersonate any role. The login endpoint returns `{"token": "placeholder-jwt"}` — no actual JWT is generated or verified. Tagged as security but documented as a known limitation.

### M9. `gpu_manager.py:114-116` — module-level execution at import time

```python
device = get_device()
_IS_CUDA = is_cuda()
DEVICE = device
```

`get_device()` calls `detect_cuda()` which imports `torch`. This runs when any module does `from compute.gpu_manager import GPUManager`. If `torch` is not installed, this crashes at import time. Pre-existing issue.

---

## LOW

### L1. `pipeline.py:269-277` / `pipeline.py:348-358` — new event loop per broadcast

```python
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
from dashboard.backend.ws import broadcast_signal
for sig in signals[:5]:
    loop.run_until_complete(broadcast_signal(sig))
loop.close()
```

Creating and destroying an event loop per broadcast is heavy. The loops are not properly cleaned up if an exception occurs mid-broadcast. Alternative: use `asyncio.run()` or a persistent loop. Pre-existing.

### L2. Dead branch: `elif "dedup" in steps and df.empty:` in pipeline runner

```python
if "dedup" in steps and not df.empty:
    df = step_dedup(df, data_mgr)
elif "dedup" in steps and df.empty:
    df = data_mgr.load_raw()
```

The `elif` branches are defensive fallbacks for empty DataFrames. They're not dead — they handle the edge case where `df` is empty after scraping. But they create a confusing pattern where the DataFrame type toggles between raw and analyzed. Kept for backward compatibility.

### L3. `config.yaml` has no `paths.cross_domain_links` entry

(Related to H2) The path keys `cross_domain_links` and `cross_domain_links_history` are referenced in code but absent from `config.yaml`. Caused by the `paths` config structure being designed for `_dir` suffixes while `alerting.py` uses a file path.

---

## Data Consistency Check

| Check | Status | Details |
|---|---|---|
| Entity parsing backward compat | ✅ | `get_entity_dict()` handles both old (string `entities` column) and new (`_parsed_entities` dict) |
| Confidence LLM signal | ✅ | `_calibrate_confidence` sets `_llm_result`; `calibrate_relationship_confidence` pops it |
| Parquet round-trip | ✅ | `_parsed_entities` column is JSON-serializable; Parquet handles dict columns via JSON encoding |
| Config singleton `_CONFIG` | ✅ | `_CONFIG` loaded once; `_SETTINGS` is parallel (though unused) |
| Scheduler run lock | ✅ | `_PIPELINE_RUN_LOCK.acquire(blocking=False)` prevents concurrent pipeline runs |
| bcrypt password hashing | ✅ | `bcrypt.hashpw` + `bcrypt.checkpw` with `gensalt()` |
| Pipeline cleanup order | ✅ | session close → GPU clear → cache clear → gc → cuda.empty_cache |

**Edge cases verified:**
- Empty DataFrame through all entity extraction functions → returns empty dicts/lists
- Missing `_parsed_entities` column on old analyzed Parquet → falls back to `entities` string column
- No `entities` column → returns `{"persons": [], "orgs": [], "locations": []}`
- LLM unavailable → `_calibrate_confidence` with `llm_result=None` → no LLM signals in confidence
- ChromaDB unavailable → `index_articles()` returns 0 silently
- NetworkX unavailable → `build_entity_graph()` returns error dict; `build_impact_chains()` returns `[]`

---

## Corrective Action Plan

### Must Fix (before next run)
1. **C1** — `chroma_store.py:99-102`: Replace 4× `row.get()` with `getattr(row, ..., "")` 
2. **H2** — `alerting.py:141`: Fix `path_for()` calls or derive from `output_dir`

### Should Fix (next iteration)
3. **H1** — Call `load_config(as_settings=True)` from `main.py` and/or `pipeline.py`
4. **H4** — Replace `hash(link)` with `hashlib.md5` for stable ChromaDB IDs
5. **M1** — Remove `import json` from `temporal.py`, `causal.py`, `narratives.py`
6. **M2** — Remove `_IS_CUDA` from `gpu_manager.py`

### Nice to Fix
7. **H3** — Consolidate Ollama sessions into one shared pool
8. **M5** — Convert remaining `df.copy()` in `signals.py` to `df.assign()`
9. **M6** — Add thread safety to `_INTEL_CACHE`
10. **M9** — Lazy `torch` import in `gpu_manager.py`
11. **L1** — Persistent event loop for WebSocket broadcasts
12. **M8** — Real JWT token generation/verification (documented limitation)

---

*Files inspected: pipeline.py, config/settings.py, config.yaml, requirements.txt, intelligence/*.py (13 files), nlp/entities.py, compute/gpu_manager.py, compute/embeddings.py, storage/manager.py, quality/dedup.py, models/models.py, vector_store/chroma_store.py, vector_store/neo4j_store.py, dashboard/backend/*.py (4 files), dashboard/frontend/src/types/index.ts*
