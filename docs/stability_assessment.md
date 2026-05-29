# Production Stability Assessment

**Date:** 2026-05-29  
**Inspected:** 32 Python files, 1 TypeScript, config, requirements  
**Method:** Manual code audit + static analysis + integration smoke tests + benchmark validation

---

## 1. Critical Bugs Found & Fixed During Review

| # | Bug | Severity | Introduced By | Fix |
|---|---|---|---|---|
| 1 | `predict_cross_domain_impact` crashes because `link["confidence"]` is `None` after confidence consolidation refactor | **CRITICAL** | Phase 5 confidence consolidation | Added `calibrate_relationship_confidence` loop in `cross_domain_pipeline()` |
| 2 | `chroma_store.py:99-102` — `row.get()` on namedtuple crashes `index_articles()` | **CRITICAL** | Phase 1 itertuples migration | Replaced with `getattr()` |
| 3 | NPMI formula divides by zero when `p_ab = 1.0` (all articles contain a pair) | **HIGH** | Pre-existing | Added `denom > 1e-10` guard |
| 4 | `alerting.py:141` — `path_for()` returns `""` for nonexistent config keys, history tracking broken | **HIGH** | Pre-existing | `os.path.join(path_for("output_dir"), ...)` |
| 5 | `hash(link)` generates different ChromaDB IDs across runs → duplicate accumulation | **HIGH** | Pre-existing | `hashlib.md5` |

**All 5 bugs have been fixed and verified.**

---

## 2. Regression Risk by Change Area

### 2.1 `itertuples()` migration (25+ call sites across 10 files)

| File | Risk | Pattern Used | Status |
|---|---|---|---|
| `chroma_store.py` | Was CRITICAL | `row.get()` → now `getattr()` | ✅ Fixed |
| `storage/manager.py` | None | `getattr(a, ...)`, `str(getattr(...))` | ✅ |
| `entity_graph.py` | None | `get_entity_dict(row)`, `getattr(row,...)` | ✅ |
| `relationships.py` | None | `get_entity_dict(row)`, `getattr(row,...)` | ✅ |
| `narratives.py` | None | `get_entity_dict(row)`, `getattr(row,...)` | ✅ |
| `signals.py` | None | `get_entity_dict(row)`, `getattr(row,...)` | ✅ |
| `causal.py` | None | `get_entity_dict(row)`, `getattr(row,...)` | ✅ |
| `temporal.py` | None | `get_entity_dict(row)`, `getattr(row,...)` | ✅ |
| `pipeline.py` | None | `getattr(row,...)`, `df.set_index(...).to_dict()` | ✅ |

**Regression verdict: SAFE** — remaining 25+ call sites all use namedtuple-safe access patterns.

### 2.2 Confidence consolidation (`_calibrate_confidence` → `calibrate_relationship_confidence`)

| Concern | Detail | Verdict |
|---|---|---|
| `_calibrate_confidence` no longer sets `link["confidence"]` | Was CRITICAL — broke `predict_cross_domain_impact` | ✅ Fixed with calibration loop |
| `calibrate_relationship_confidence` pops `_llm_result` | Single pop, second call returns `None` → fallback | ✅ |
| LLM signal weight | Previously discarded (double-calculation bug), now 20%/10% | ✅ Fixed |
| Multiple calibration calls on same link | `pop()` returns `None` on second call, graceful | ✅ Safe |

**Regression verdict: SAFE** after the calibration loop fix.

### 2.3 List comprehension json.loads (pipeline.py:190)

- `[json.loads(e) for e in to_analyze["entities"]]`
- **NaN risk**: If `entities` column has NaN from CSV corruption → `json.loads(NaN)` raises `TypeError`
- **Mitigation**: `get_entity_dict()` catches `json.JSONDecodeError` and `TypeError` downstream
- **Verdict**: LOW risk, protected downstream

### 2.4 Settings dataclass activation

- `main.py:27` now calls `load_config(as_settings=True)`, populating `_SETTINGS`
- `get()` returns Settings values before `_CONFIG` dict values
- Settings paths are relative strings (e.g., `"output"`), `_CONFIG` has resolved absolute paths
- **Mitigation**: All path access goes through `path_for()` which independently resolves
- **Code audit**: No code directly uses `get("paths.*")` as a file path — all use `path_for()`
- **Verdict**: SAFE — path resolution is self-healing

---

## 3. Integration Points

### 3.1 Frontend ↔ Backend Contract

| API Endpoint | Returns | Consumed By | Type Drift Risk |
|---|---|---|---|
| `/api/cross-domain` | `{links, chains, sector_map}` | `ExplorePage` | Low — stable schema |
| `/api/entity-graph` | `{nodes, edges, stats}` | `ExplorePage` | Low — ignores `stats` |
| `/api/narratives` | `{mutations, entity_narratives, ...}` | `TimelinePage` | Medium — complex nested types |
| `/api/signals` | `{signals, summary}` | `SignalsPage` | Low |
| `/api/alerts` | `{alerts, summary}` | `AlertsPage` | Low |
| `/api/briefing` | Full briefing object | `BriefingPage` | Medium |
| `/api/causal-analysis` | `{causal_candidates, ...}` | unused in frontend | Low |
| `/api/multi-agent-analysis` | Multi-agent result | unused in frontend | Low |
| `/api/temporal-patterns` | Temporal result | unused in frontend | Low |

**Risk**: Frontend types (`types/index.ts`) are manually maintained — no shared schema. Pydantic models exist (`models/models.py`) but are not used as a type source for the frontend. Type drift is possible but low-probability for stable fields.

### 3.2 WebSocket

| Flow | Reliability |
|---|---|
| Pipeline complete broadcast | Creates new event loop per broadcast; exception in one client doesn't block others |
| Signal/alert broadcasts | Same pattern; dead clients removed lazily |
| Standalone pipeline mode | All broadcast calls wrapped in `try/except` — silent failure if WebSocket server not running |

**Risk**: LOW — broadcasts are fire-and-forget with proper error isolation.

### 3.3 APScheduler ↔ Pipeline

| Timing Parameter | Value | Risk |
|---|---|---|
| Interval | 15 min | If pipeline takes >15 min, scheduler skips the missed run |
| `misfire_grace_time` | 120 sec | Misses beyond 2 min are permanently skipped |
| `_PIPELINE_RUN_LOCK` | Non-blocking | Concurrent runs rejected with warning |
| Daemon thread pipeline | Yes | Thread killed on shutdown — mid-run data loss possible |

**Risk**: LOW for normal operation. MEDIUM on shutdown — daemon thread terminates abruptly.

### 3.4 Neo4j / ChromaDB

| Store | Risk | Mitigation |
|---|---|---|
| Neo4j | Connection credentials in config | Fully optional, entire block in try/except |
| ChromaDB | Duplicate documents (now fixed) | `hashlib.md5` provides stable IDs |

---

## 4. Edge-Case & Exception Analysis

### 4.1 Empty DataFrame propagation (ALL paths verified)

```
scrape → empty df → dedup: loads from disk
                  → fetch: loads from disk
                  → analyze: loads from disk
                  → entity_graph: returns error dict
                  → cross_domain: empty lists
                  → narratives: empty lists
                  → signals: empty list
                  → temporal: empty lists
                  → vector_index: returns 0
```

**No crash path found for empty DataFrames across any module.**

### 4.2 NaN/Inf protection audit

| Location | Guard | Safe? |
|---|---|---|
| `np.mean(links)` in summary | `if cross_links else 0` | ✅ |
| `np.mean(src_rels)` in confidence | `if src_rels else 0.5` | ✅ |
| `np.mean(sims)` in relationships | `if sims else 0.0` | ✅ |
| `np.mean(...)` in briefings | `if relevant_links` / `if links` | ✅ |
| `_clean()` in main.py read path | Recursive NaN→None | ✅ |
| `json.dump` write path | Never receives NaN (all values rounded) | ✅ |

### 4.3 Missing dependency audit

| Dependency | Import Pattern | Graceful Fallback |
|---|---|---|
| `networkx` | `try/except ImportError` | ✅ Return error dict / `[]` |
| `chromadb` | `try/except` | ✅ Return 0, search returns error |
| `datasketch` | `try/except` | ✅ Falls back to TF-IDF |
| `bertopic` | `try/except` | ✅ Keyword-based clustering |
| `neo4j` | `try/except` | ✅ `NEO4J_AVAILABLE = False` |
| `gliner` | `try/except` in `_get_gliner()` | ✅ → HF NER → regex |
| `transformers` | Multiple try/except sites | ✅ CPU fallbacks |
| `torch` | `try/except` in `detect_cuda()` | ✅ CPU mode |
| `fasttext` | `try/except` in `_get_detector()` | ✅ Langdetect fallback |
| `rank_bm25` | `try/except` | ✅ Skips hybrid search |
| `requests` | `try/except` in `relationships.py` | ✅ `_HAS_REQUESTS = False` |
| `sentence_transformers` | `try/except` in various | ✅ Embeddings return None |

**Every optional dependency has a graceful degradation path.**

---

## 5. Race Conditions & Concurrency

| Resource | Protection | Risk |
|---|---|---|
| `_PIPELINE_RUN_LOCK` (threading.Lock) | Non-blocking acquire | ✅ No concurrent pipelines |
| `_STATE_LOCK` (threading.Lock) | `_update_state` / `_get_state` | ✅ Protected |
| `_STATE_LOCK` TOCTOU on `run_count` | `run_count=_PIPELINE_STATE["run_count"]+1` evaluated outside lock | ✅ Practically unreachable — serialized by pipeline lock |
| `_INTEL_CACHE` (plain dict) | No lock | ⚠️ LOW — clear during read returns stale data (not crash) |
| `_FILE_LOCK` (threading.Lock) | `atomic_write_json` | ✅ Writes serialized |
| `atomic_read_json` | No lock (relies on `os.replace` atomicity) | ✅ Correct |
| `GPUManager` singleton `__new__` | No lock on `_instance` | ⚠️ LOW — initialized once, accessed read-only thereafter |
| WebSocket `_clients` (Set) | Modified by `connect/disconnect`, iterated by `broadcast` | ⚠️ LOW — `list(_clients)` copy in broadcast prevents mid-iteration modification |

**Concurrency verdict**: All critical paths are protected. Remaining unprotected resources are low-risk.

---

## 6. Security Assessment

| Concern | Detail | Verdict |
|---|---|---|
| Password hashing | bcrypt with `gensalt()` | ✅ Strong |
| JWT auth | Placeholder — `"token": "placeholder-jwt"` | ⚠️ No real token |
| Role enforcement | `X-User-Role` header (no signature) | ⚠️ Trivially bypassable |
| Neo4j credentials | Hardcoded in config.yaml (`password`) | ⚠️ Documented as non-production |
| JWT secret | Hardcoded default: `"change-me-in-production"` | ⚠️ Documented |
| Input validation | FastAPI `Query()` with type hints | ✅ Basic |
| CORS | `allow_origins=["*"]` | ⚠️ Documented as dev default |
| `_clean()` NaN removal | Handles only JSON-safe types | ✅ |
| File path traversal | `path_for()` uses `os.path.abspath`, no user input | ✅ |

**Security verdict**: Acceptable for internal/development use. **Not ready for internet-facing deployment** without real JWT, credential management, and CORS restrictions.

---

## 7. Environment-Specific Risks

### Windows (current platform)
| Risk | Detail |
|---|---|
| `os.path.join(absolute, absolute)` behavior | Ignores first arg on Windows — matches second absolute path | ✅ Correct |
| `os.replace()` | Available since Python 3.3 | ✅ |
| Signal handling | No graceful shutdown handler installed | ⚠️ Daemon thread killed |
| Line endings | CSV/Parquet are binary-safe, JSON uses platform encoding | ✅ |

### Linux
| Risk | Detail |
|---|---|
| `os.path.join("/a", "/b")` | Returns `"/b"` (second absolute path) — same as Windows for this case | ✅ Correct |

### GPU memory
| Risk | Detail |
|---|---|
| GLiNER (~1.5GB) + BGE-M3 (~2GB) | Stays loaded across pipeline runs | ⚠️ OOM on <8GB VRAM |
| `pipeline_cleanup()` | Clears only HF pipelines, NOT GLiNER or BGE-M3 embeddings | ⚠️ Memory accumulates |
| Mitigation | Set `CUDA_VISIBLE_DEVICES=""` for CPU-only | Documented |

### Ollama availability
| Risk | Degradation |
|---|---|
| All LLM calls | Return `None` → pipeline continues with statistical analysis | ✅ Graceful |

### Internet connectivity
| Risk | Degradation |
|---|---|
| Scraping | Returns `[]` → pipeline runs on existing data | ✅ Graceful |

---

## 8. Production Confidence Score

### Scoring (1-5 each)

| Criterion | Score | Rationale |
|---|---|---|
| **Pipeline reliability** | **4.5** | No crash paths found; all errors caught; graceful degradation for every dependency |
| **Data integrity** | **4.0** | Atomic writes, parquet fallback, `_clean()` NaN handling; ChromaDB duplicate risk eliminated |
| **Integration quality** | **3.5** | All API contracts matched; WebSocket fire-and-forget; frontend types manually maintained |
| **Concurrency safety** | **4.0** | Critical paths locked; GPU singleton and cache unprotected but usage-safe |
| **Error handling** | **4.5** | Every optional dependency has fallback; empty DF handled globally; NaN guarded |
| **Security** | **2.5** | bcrypt good; JWT, CORS, credentials all placeholder/documentation-level |
| **Operational readiness** | **2.0** | No Docker, no health check, no metrics, no graceful shutdown, no CI/CD, no tests |

### Overall: 3.6 / 5 → **65% confidence for production deployment**

### Blocker checklist for production go-live

| Required | Status | Notes |
|---|---|---|
| Critical bugs resolved | ✅ All 5 found are fixed |
| High bugs resolved | ✅ One high (NPMI div/zero) fixed |
| Graceful degradation for all dependencies | ✅ Every optional import has fallback |
| Data consistency across runs | ✅ Parquet + CSV + JSON all consistent |
| **Not ready until:** | | |
| Real JWT auth | ❌ | Placeholder only |
| Docker containerization | ❌ | Dependency management on bare metal is fragile |
| Graceful shutdown | ❌ | Pipeline thread is daemon — killed on exit |
| Monitoring / health check endpoint | ❌ | `/api/health` is basic; no pipeline-specific health |
| CI/CD pipeline | ❌ | Manual deploy only |
| Frontend-backend schema sync | ❌ | Types manually maintained, no shared schema file |
| GLiNER/BGE-M3 memory management | ⚠️ | Pipeline cleanup doesn't unload these; accumulates GPU memory |
### Recommended next steps for production

1. **Test suite**: `pytest` with mocked models — catch integration gaps like the confidence calibration bug
2. **Docker**: Containerize API + frontend + Ollama for reproducible deployment
3. **Real JWT**: Implement actual token generation/verification in `auth.py`
4. **GPU memory**: Add `del _gliner` / `del _encoder` calls in `pipeline_cleanup()`
5. **Graceful shutdown**: `atexit.register` or APScheduler `shutdown(wait=True)` with pipeline abort signal
6. **Shared schema**: Generate TypeScript types from pydantic models (or use `datamodel-code-generator`)
7. **Health endpoint**: `/api/health` should report pipeline status + disk space + GPU memory + last error trace
