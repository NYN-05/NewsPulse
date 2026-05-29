NewsPulse — AI-Powered Cross-Domain Intelligence Discovery Engine.
1. PROJECT PURPOSE & BUSINESS OBJECTIVES
NewsPulse is an autonomous intelligence platform that continuously:
Monitors 111+ RSS/news sources across 8 sectors (Politics, Finance, Technology, Energy, Military, Startups, Social, Global Events)
Extracts entities using state-of-the-art NER (GLiNER → HuggingFace → regex cascade)
Discovers hidden cross-domain relationships (e.g., "How does a Fed rate hike affect AI chip stocks?")
Tracks narrative evolution via BERTopic clustering with lifecycle phases (emerging → accelerating → peaking → declining → fading → resurging)
Detects emerging signals (spillover, anomalies, bursts, phase transitions)
Runs multi-agent LLM analysis (Analyst → Critic → Summarizer via Ollama)
Serves everything through a polished React intelligence dashboard with real-time WebSocket updates
Primary use case: Intelligence analysts, journalists, investors, or policy researchers who need to connect dots across domains automatically.
2. HIGH-LEVEL ARCHITECTURE
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React 19 SPA)                         │
│                                                                         │
│  Port 5173  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐   │
│  (Vite)     │ Zustand  │  │ 7 Pages  │  │    API Client (api.ts)   │   │
│             │ (state)  │  │ (state-  │  │    - 16 REST endpoints   │   │
│             └──────────┘  │ based    │  │    - WebSocket /ws       │   │
│                           │ router)  │  └──────────┬───────────────┘   │
│                           └──────────┘             │                    │
└────────────────────────────────────────────────────┼────────────────────┘
                                                     │
                          HTTP (poll 30s) + WebSocket │ Vite proxy /api → :8765
                                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI on port 8765)                       │
│                                                                          │
│  ┌──────────────────────────────────────────┐  ┌──────────────────────┐ │
│  │  dashboard/backend/main.py               │  │  dashboard/backend/  │ │
│  │  ├─ FastAPI lifespan: start_scheduler()  │  │  ├─ auth.py (JWT)    │ │
│  │  ├─ 19 API endpoints                     │  │  ├─ ws.py (WS bcast) │ │
│  │  ├─ Background scheduler (15 min loop)   │  │  └─ exporter.py      │ │
│  │  └─ Thread-safe _PIPELINE_STATE          │  └──────────────────────┘ │
│  └────────────────────┬─────────────────────┘                           │
│                       │                                                │
└───────────────────────┼────────────────────────────────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                     INTELLIGENCE PIPELINE (pipeline.py)                     │
│                       17-step orchestrator                                  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  PHASE 1: DATA COLLECTION                                            │  │
│  │  step_scrape() → step_scrape_rss() → step_dedup() → step_fetch()     │  │
│  │                                                                       │  │
│  │  PHASE 2: NLP ANALYSIS                                               │  │
│  │  step_analyze() [clean, NER, lang detect] → step_entity_graph()      │  │
│  │                                                                       │  │
│  │  PHASE 3: INTELLIGENCE DISCOVERY                                     │  │
│  │  step_cross_domain() [sector map, LLM verify, impact chains]         │  │
│  │  → step_causal() [lag analysis] → step_narratives() [BERTopic]       │  │
│  │  → step_signals() [spillover, anomalies]                              │  │
│  │                                                                       │  │
│  │  PHASE 4: ADVANCED ANALYSIS                                           │  │
│  │  step_multi_agent() [Analyst→Critic→Summarizer via Ollama]           │  │
│  │  → step_temporal() [velocity, burst, phase transition]               │  │
│  │  → step_briefings() [exec briefing + predictions]                     │  │
│  │                                                                       │  │
│  │  PHASE 5: OUTPUT & SERVING                                            │  │
│  │  step_alerts() → step_export() → step_neo4j() → step_vector_index()  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────┘
3. MODULE MAP & RESPONSIBILITIES
3.1 Configuration Layer
Responsibility
YAML config loader, atomic JSON read/write with threading lock, path resolution
3.2 Data Collection (Phase 1)
Responsibility
HTTP session with retry, connection pooling, backoff
118 RSS feed definitions across 8 sectors
Multi-threaded RSS parsing via feedparser (8 workers)
4 web scrapers with CSS selectors (TOI, HT, IE, NDTV)
Exact dedup + semantic TF-IDF dedup (threshold 0.85)
43 patterns for boilerplate removal
DataManager: Parquet/CSV persistence, merge, dedup keys
3.3 NLP Analysis (Phase 2)
Responsibility
Text cleaning, category extraction, sensationalism detection
GLiNER Large v2 → HuggingFace BERT NER → regex (cascading fallback)
VADER (CPU) / HuggingFace (GPU) sentiment analysis
Language detection (fastText → langdetect fallback)
CUDA detection singleton, automatic fallback to CPU
BGE-M3 sentence transformer encoding
3.4 Intelligence Discovery (Phase 3) — The Core
Responsibility
NetworkX entity co-occurrence graph, degree centrality
★ Central module: sector mapping, cross-domain link scoring (semantic_similarity * 0.4 + cooccurrence * 0.35 + diversity * 0.25), LLM verification via Ollama (qwen3:14b), impact chain construction, confidence calibration
BERTopic clustering (BGE embeddings), 6-phase lifecycle detection, narrative mutation tracking (keyword drift)
4 signal types: emerging relationship, cross-domain spillover, entity anomaly, narrative acceleration
Temporal causal reasoning with lag analysis (Granger-style)
3.5 Advanced Analysis (Phase 4)
Responsibility
3-agent pipeline: Analyst → extracts findings; Critic → challenges assumptions; Summarizer → produces briefing. All via Ollama (qwen3:14b). Falls back to statistical heuristics if LLM unavailable
Entity velocity tracking, z-score anomaly detection (threshold 2.0), burst detection (z>2.5), phase transition prediction
Executive briefing generation with sector situations, watch items, predictions
Multi-signal confidence calibration (statistical 35% + source reliability 10% + semantic 15% + LLM 20% + causal 10%)
Human-readable natural language explanations
3.6 Alerting & Export (Phase 5)
Responsibility
Alert triggers: relationship velocity, acceleration, bursts, phase transitions
ChromaDB + BGE-M3 embeddings + BM25 hybrid search + optional cross-encoder reranker
Neo4j graph adapter (optional, graceful degradation)
JSON/CSV/Markdown export with timestamps
3.7 API Layer
Responsibility
FastAPI app, lifespan scheduler, 19 endpoints, WebSocket, CORS, NaN sanitizer
JWT RBAC (viewer/analyst/admin), disabled by default
WebSocket connection manager, pipeline-complete broadcast
3.8 Frontend
Responsibility
Root: health polling (30s), Ctrl+K search shortcut, state-based page routing
MainLayout (wrapper), Sidebar (7-tab nav), Header (pipeline status)
Intelligence briefing + Leaflet dark map + discoveries feed
3-panel: entity list → ReactFlow graph → explanation
Narrative lifecycle + impact chain visualization
Structured executive briefing display
Ranked signal cards with severity coloring
Severity-sorted alert list
Natural language hybrid search with example queries
ReactFlow interactive graph with cluster/stress layouts
Typed fetch-based API client (16 methods)
Zustand store: sidebar toggle, pipeline status
309 lines of TypeScript interfaces (24 types)
4. DATA FLOW
 RSS Feeds (111+)         Web Sources (4)
       │                       │
       ▼                       ▼
  rss_scraper.py          sources.py
   (8 threads)            (requests+BS4)
       │                       │
       └───────┬───────────────┘
               ▼
         pipeline.py
     step_dedup()  ────►  quality/dedup.py
     step_fetch()  ────►  quality/boilerplate.py
               │
               ▼
     step_analyze()
       ├── nlp/preprocess.py (clean text)
       ├── nlp/entities.py (GLiNER NER)
       ├── nlp/sentiment.py (VADER/HF)
       └── multilingual/detect.py
               │
               ▼
     storage/manager.py ────► output/data/news_analyzed.parquet
               │
               ├──► step_entity_graph() ────► output/entity_graph.json
               │
               ├──► step_cross_domain()
               │      ├── build_sector_map() [keyword + org lexicons]
               │      ├── find_cross_domain_links() [co-occurrence + embedding]
               │      ├── apply_llm_verification() [Ollama qwen3:14b]
               │      ├── predict_cross_domain_impact() [sector templates]
               │      └── build_impact_chains() [NetworkX shortest path]
               │      ├──► output/sector_map.json
               │      ├──► output/cross_domain_links.json
               │      └──► output/impact_chains.json
               │
               ├──► step_causal() ────► output/causal_analysis.json
               │
               ├──► step_narratives()
               │      ├── BERTopic clustering
               │      ├── Phase detection (6 lifecycles)
               │      ├── Mutation tracking
               │      └──► output/narrative_evolution.json
               │
               ├──► step_signals() ────► output/breaking_events.json
               │
               ├──► step_multi_agent()
               │      ├── Analyst Agent (Ollama)
               │      ├── Critic Agent (Ollama)
               │      ├── Summarizer Agent (Ollama)
               │      └──► output/multi_agent_analysis.json
               │
               ├──► step_temporal() ────► output/temporal_patterns.json
               │
               ├──► step_briefings() ────► output/intelligence_briefing.json
               │
               ├──► step_alerts() ────► output/alerts.json
               │
               ├──► step_vector_index() ────► output/chroma_db/
               │
               └──► step_neo4j() ────► Neo4j graph (optional)
5. TECHNOLOGY STACK
Layer	Technology
Backend	Python
Web Framework	FastAPI
ASGI Server	Uvicorn
Frontend	React
Frontend Build	Vite
TypeScript	TypeScript
CSS	Tailwind CSS
State	Zustand
Graph Viz	ReactFlow (@xyflow/react)
Map	Leaflet
NER	GLiNER
Embeddings	Sentence-Transformers (BGE-M3)
Topic Modeling	BERTopic
Vector DB	ChromaDB
Graph DB	Neo4j (optional)
LLM	Ollama (Qwen3:14b)
NLP	HuggingFace Transformers
Sentiment	NLTK (VADER)
GPU	PyTorch + CUDA
Data	Pandas, NumPy, scikit-learn
Storage	Parquet (via PyArrow)
6. ENTRY POINTS & EXECUTION FLOW
Primary entry: python dashboard/backend/main.py
main.py  (port 8765)
│
├── 1. Load config.yaml
├── 2. Create FastAPI app
├── 3. lifespan():
│       ├── start_scheduler()
│       │       └── _scheduler_loop()  [daemon thread]
│       │               ├── initial_delay (10s)
│       │               └── loop:
│       │                       ├── _run_pipeline()
│       │                       ├── update state + broadcast WS
│       │                       └── sleep(interval_minutes * 60s)
│       └── yield  (app serves requests)
│
├── 4. REST endpoints serve from output/*.json (atomic reads)
├── 5. WebSocket endpoint broadcasts pipeline completions
│
└── Shutdown: stop_scheduler() via threading.Event
Alternative entry: python pipeline.py (standalone, one-shot execution)
Frontend: npm run dev (Vite on port 5173, proxies /api to :8765)
7. EXTERNAL DEPENDENCIES & INTEGRATIONS
Dependency	Integration Type
Ollama	HTTP (localhost:11434)
Neo4j	Bolt (localhost:7687)
GLiNER	Python library (HuggingFace)
ChromaDB	Python library
BERTopic	Python library
4 Web Sources	HTTP (requests)
111 RSS Feeds	HTTP (feedparser)
Key architectural principle: Everything degrades gracefully. If a dependency is missing, NewsPulse continues with a less sophisticated alternative. This is the single most important architectural decision in the codebase.
8. CROSS-DOMAIN SCORING FORMULA
strength = cooccurrence_count * 0.35 + source_diversity * 0.25 + semantic_similarity * 0.40
Confidence calibration (when LLM available):
final_confidence = base_confidence * 0.4 + llm_confidence * 0.6
Confidence labels: high (>0.7), medium (0.4–0.7), low (<0.4)
9. STRENGTHS
Resilient architecture — Every component has multiple fallback tiers. The system degrades gracefully from GPU GLiNER down to regex NER, from BERTopic to keyword clustering, from LLM verification to statistical-only.
Clean separation of concerns — Each pipeline step is an independent function with clear inputs/outputs, making it modular and testable.
Excellent design for intelligence — The 3-agent paradigm (Analyst → Critic → Summarizer) mirrors real intelligence analysis workflow. The sector-classified cross-domain engine addresses a genuinely hard problem.
Atomic I/O throughout — All JSON writes use temp-file + rename with threading locks, so the API never serves partial/corrupted output.
Real-time capable — WebSocket broadcast + 30s frontend polling provides near-real-time intelligence updates.
Configuration-driven — All tunable parameters (thresholds, models, intervals, timeouts) in a single config.yaml.
Minimal frontend dependencies — Only 9 packages (React, ReactFlow, Leaflet, Zustand, Tailwind, Vite). No heavy router, no complex state management.
10. WEAKNESSES & RISKS
State-based routing (no React Router) — App.tsx uses a simple Record<string, ReactNode> for page switching. This means no URL-based deep linking, no browser history, and no lazy loading. Users cannot bookmark or share a specific page URL.
Single-threaded pipeline — The entire pipeline runs sequentially in a single daemon thread. If one step crashes, the whole pipeline fails. For 111+ RSS feeds, this could take significant time without parallelization within phases.
No database for article storage — Uses Parquet/CSV files through a custom DataManager. As data grows, this will become a bottleneck. No incremental updates — the pipeline re-processes the entire dataset each cycle.
Limited authentication — JWT auth is implemented but disabled by default. Credentials are stored in-memory with no persistent user database. No API key management for programmatic access.
Ollama single point of failure — LLM verification and multi-agent pipeline depend on a local Ollama instance. If Ollama is down or the model is slow, the pipeline may timeout or produce degraded output. The 60s timeout is generous but the whole pipeline blocks on it.
No formal testing infrastructure — No test files (unit, integration, or E2E) exist in the repository. The entire system relies on runtime logging for verification.
Hardcoded sector templates — Impact prediction uses a hardcoded impact_patterns dictionary (sector pairs mapped to effects). This is brittle and doesn't learn from new patterns.
Memory pressure — BERTopic clustering and BGE-M3 embeddings are memory-intensive. No batching or memory management for large article volumes.
Vite proxy assumption — The frontend assumes /api is proxied to :8765. In production, a reverse proxy (nginx/Caddy) would be needed. No Docker or deployment configuration exists.
No data retention policy — Articles accumulate indefinitely in Parquet files. No archival, compression, or cleanup mechanism.
11. DESIGN PATTERNS USED
Pattern	Where
Pipeline	pipeline.py
Strategy	nlp/entities.py
Singleton	compute/gpu_manager.py
Observer	dashboard/backend/ws.py
Scheduler	dashboard/backend/main.py
Facade	services/api.ts
Atomic I/O	config/settings.py
Multi-Agent	intelligence/agents.py
State-based Routing	App.tsx
Configuration Object	config/settings.py
12. DIRECTORY RUNTIME LAYOUT
C:\Users\JHASHANK\Downloads\NEWS\
├── config.yaml                          ← Central configuration
├── pipeline.py                          ← 17-step orchestrator
├── dashboard/backend/main.py            ← FastAPI server (port 8765)
├── dashboard/frontend/src/              ← React SPA (port 5173 via Vite)
│
├── output/
│   ├── data/news_analyzed.parquet       ← Persistent article store
│   ├── chroma_db/                       ← Vector search index
│   ├── models/kmeans_model.joblib      ← Cached ML models
│   ├── logs/                            ← metrics, alerts, updates
│   ├── sector_map.json                  ← Entity → sector mapping
│   ├── cross_domain_links.json          ← Weighted relationships
│   ├── impact_chains.json               ← Multi-hop propagation
│   ├── entity_graph.json                ← NetworkX graph
│   ├── narrative_evolution.json         ← BERTopic + lifecycle
│   ├── breaking_events.json             ← Signals
│   ├── causal_analysis.json             ← Temporal causation
│   ├── multi_agent_analysis.json        ← Agent pipeline output
│   ├── temporal_patterns.json           ← Velocity/burst/phase
│   ├── intelligence_briefing.json       ← Executive briefing
│   └── alerts.json                      ← Ranked alerts
13. ONBOARDING CHECKLIST FOR NEW DEVELOPERS
Run the pipeline: python pipeline.py (expects config.yaml in CWD)
Start the API + scheduler: python dashboard/backend/main.py
Start the frontend: cd dashboard/frontend && npm install && npm run dev
Key config change: Set intelligence.llm_verification: false in config.yaml if no Ollama
To understand the data model: Read types/index.ts (309 lines, fully typed)
To trace a single cross-domain link: intelligence/relationships.py:483 → cross_domain_pipeline()
To modify the pipeline: pipeline.py:332 → run_pipeline()
To add an API endpoint: dashboard/backend/main.py + services/api.ts + typed response in types/index.ts
To add a frontend page: Create component in pages/, add to pages record in App.tsx, add nav button in sidebar.tsx

NewsPulse — Complete Dependency Map
1. DIRECTORY STRUCTURE MAP
├── pipeline.py                          ★ ORCHESTRATOR (consumes everything)
├── config.yaml                          ★ CONFIG (consumed by everyone)
│
├── config/
│   ├── __init__.py
│   └── settings.py                      ★ lib: yaml, json, os, threading
│
├── compute/
│   ├── __init__.py                      re-exports: GPUManager, device, is_cuda, DEVICE
│   ├── gpu_manager.py                   singleton class GPUManager  [stdlib only]
│   └── embeddings.py                    → compute.gpu_manager (device)
│                                        lib: sentence_transformers
│
├── scraper/
│   ├── __init__.py
│   ├── client.py                        → config.settings (get)
│                                        lib: requests, urllib3
│   ├── rss_feeds.py                     DATA-ONLY (118 feeds, no imports)
│   ├── rss_scraper.py                   → scraper.client (get_session)
│                                        → scraper.rss_feeds (RSS_FEEDS)
│                                        → config.settings (get)
│                                        lib: feedparser
│   └── sources.py                       → scraper.client (fetch)
│                                        → config.settings (get)
│                                        lib: bs4 (BeautifulSoup), pandas
│
├── nlp/
│   ├── __init__.py
│   ├── preprocess.py                    → config.settings (get)
│                                        lib: re, hashlib, html, unicodedata
│   ├── entities.py                      [stdlib only: json, re]
│                                        lib: gliner, transformers (optional)
│   ├── sentiment.py                     [stdlib only]
│                                        lib: transformers (optional)
│   └── summarization.py                 [stdlib only]
│
├── quality/
│   ├── __init__.py
│   ├── dedup.py                         lib: sklearn (TfidfVectorizer)
│   └── boilerplate.py                   [stdlib only: re]
│
├── storage/
│   ├── __init__.py
│   └── manager.py                       → config.settings (path_for, get)
│     class DataManager                  lib: pandas (parquet, csv)
│
├── intelligence/
│   ├── __init__.py
│   ├── entity_graph.py                  → config.settings (atomic_write_json)
│                                        lib: networkx, pandas
│   ├── relationships.py   ★ CORE        → config.settings (get, atomic_write_json)
│                                        → compute.embeddings (encode_texts)
│                                        lib: pandas, numpy, networkx
│                                        ⚡ HTTP: localhost:11434 (Ollama)
│   ├── narratives.py                    → config.settings (atomic_write_json)
│                                        → compute.embeddings (encode_texts)
│                                        lib: bertopic, numpy, pandas
│   ├── signals.py                       → config.settings (atomic_write_json)
│                                        lib: pandas, numpy
│   ├── causal.py                        → config.settings (get)
│                                        lib: networkx, numpy, pandas
│   ├── agents.py                        → config.settings (get, atomic_write_json, path_for)
│                                        lib: numpy
│                                        ⚡ HTTP: localhost:11434 (Ollama)
│   ├── temporal.py                      → config.settings (get, atomic_write_json, path_for)
│                                        lib: pandas, numpy
│   ├── briefings.py                     → config.settings (get, atomic_write_json, path_for)
│                                        lib: numpy
│   ├── alerting.py                      → config.settings (get, atomic_write_json, atomic_read_json, path_for)
│                                        lib: numpy
│   ├── confidence.py                    → config.settings (get)
│   ├── explanation.py                   → intelligence.confidence (calibrate_relationship_confidence)
│   └── event_detection.py               [LEGACY, lib: pandas, numpy]
│
├── multilingual/
│   ├── __init__.py
│   └── detect.py                        lib: langdetect, fastText (optional)
│
├── vector_store/
│   ├── __init__.py
│   ├── chroma_store.py                  → config.settings (path_for)
│                                        → compute.embeddings (encode_texts)
│                                        lib: chromadb, rank_bm25, sentence_transformers (reranker)
│   └── neo4j_store.py                   class Neo4jStore
│                                        lib: neo4j (optional, stdlib otherwise)
│
└── dashboard/
    ├── __init__.py
    └── backend/
        ├── main.py      ★ SERVER        → config.settings (ALL)
                                        → pipeline (run_pipeline, step_*)
                                        → storage.manager (DataManager)
                                        → dashboard.backend.ws (connect, disconnect, broadcast)
                                        → dashboard.backend.exporter (export_*)
                                        → dashboard.backend.auth (authenticate, create_user)
                                        → vector_store.chroma_store (semantic_search)
                                        → vector_store.neo4j_store (Neo4jStore)
                                        → intelligence.explanation (explain_relationship)
                                        lib: fastapi, uvicorn
        ├── auth.py                       → config.settings (get, atomic_write_json, atomic_read_json)
                                        lib: fastapi
        ├── exporter.py                   → config.settings (get, atomic_read_json, path_for)
        └── ws.py                         [stdlib only: asyncio, json]
                                        lib: fastapi (WebSocket)
2. INTERNAL MODULE DEPENDENCY GRAPH
  ┌───────────────┐
  │  config.yaml  │
  └───────┬───────┘
          │ read by
          ▼
  ┌──────────────────┐
  │  config/settings │←─── ALL MODULES read config via get(), path_for()
  └──────────────────┘
          │
          │ exports: load_config, get, path_for, atomic_write_json, atomic_read_json
          │
          ▼
  ┌────────────────────────────────────────────────────────────────┐
  │                       pipeline.py                               │
  │  Imports:                                                       │
  │   ├── compute.gpu_manager        → GPUManager                   │
  │   ├── storage.manager            → DataManager                  │
  │   ├── scraper.sources            → scrape_all_sources, fetch_all│
  │   ├── scraper.rss_scraper        → scrape_all_rss               │
  │   ├── nlp.preprocess             → clean_text, extract_category │
  │   ├── nlp.entities               → extract_entities_batch       │
  │   ├── quality.dedup              → deduplicate_*                │
  │   ├── quality.boilerplate        → remove_boilerplate           │
  │   ├── intelligence.entity_graph  → build_entity_graph           │
  │   ├── intelligence.relationships → cross_domain_pipeline        │
  │   ├── intelligence.narratives    → narrative_pipeline           │
  │   ├── intelligence.signals       → signals_pipeline             │
  │   ├── intelligence.causal        → causal_pipeline              │
  │   ├── intelligence.agents        → multi_agent_pipeline         │
  │   ├── intelligence.temporal      → temporal_pipeline            │
  │   ├── intelligence.briefings     → generate_briefing            │
  │   ├── intelligence.alerting      → alerting_pipeline            │
  │   └── multilingual.detect        → detect_language              │
  └──────────┬─────────────────────────────────────────────────────┘
             │ feeds data to
             ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                      output/*.json files                         │
  │  (read/written atomically, served by API)                        │
  └─────────────────────────────────────────────────────────────────┘
             │ read by
             ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                   dashboard/backend/main.py                       │
  │  Imports:                                                        │
  │   ├── pipeline                   → run_pipeline (lazy)           │
  │   ├── storage.manager            → DataManager (lazy)            │
  │   ├── dashboard.backend.ws       → connect, disconnect           │
  │   ├── dashboard.backend.exporter → export_json/csv/markdown      │
  │   ├── dashboard.backend.auth     → authenticate, create_user     │
  │   ├── vector_store.chroma_store  → semantic_search (lazy)       │
  │   ├── vector_store.neo4j_store   → Neo4jStore (lazy)             │
  │   ├── intelligence.explanation   → explain_relationship (lazy)  │
  │   └── config.settings            → ALL config accessors           │
  └──────────┬──────────────────────────────────────────────────────┘
             │ serves to
             ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                  React Frontend (port 5173)                       │
  │  ┌──────────────────────────────────────────────────────────┐   │
  │  │  App.tsx                                                  │   │
  │  │   ├── components/layout/main-layout                       │   │
  │  │   ├── components/layout/sidebar     ← Zustand useStore    │   │
  │  │   ├── components/layout/header      ← Zustand useStore    │   │
  │  │   ├── pages/home     → api.ts → /api/health              │   │
  │  │   ├── pages/explore  → api.ts → /api/entity-graph        │   │
  │  │   ├── pages/timeline → api.ts → /api/narratives          │   │
  │  │   ├── pages/search   → api.ts → /api/search?q=           │   │
  │  │   ├── pages/signals  → api.ts → /api/signals             │   │
  │  │   ├── pages/briefing → api.ts → /api/briefing            │   │
  │  │   ├── pages/alerts   → api.ts → /api/alerts              │   │
  │  │   ├── services/api.ts   → fetch() to /api/*              │   │
  │  │   ├── store/dashboard.ts ← zustand (sidebar, pipeline)   │   │
  │  │   └── types/index.ts ← all TS interfaces                 │   │
  │  └──────────────────────────────────────────────────────────┘   │
  └─────────────────────────────────────────────────────────────────┘
3. CRITICAL DEPENDENCY CHAIN (THE PIPELINE)
This is the data flow through every layer — a single run of run_pipeline():
┌─ Step 1:  scrape()          ──→ scraper/sources.py
│   depends on: config.settings (get), scraper/client (fetch)
│   writes to: storage/manager (DataManager.merge_new_articles)
│   output: pd.DataFrame (raw articles)
│
├─ Step 2:  scrape_rss()      ──→ scraper/rss_scraper.py
│   depends on: config.settings (get), scraper/client (get_session), scraper/rss_feeds (RSS_FEEDS)
│   writes to: DataManager.merge_new_articles
│   output: pd.DataFrame (raw articles, appended)
│
├─ Step 3:  dedup()           ──→ quality/dedup.py
│   depends on: sklearn (TfidfVectorizer)
│   writes to: DataManager.save_raw
│   output: pd.DataFrame (deduplicated)
│
├─ Step 4:  fetch()           ──→ scraper/sources.py (fetch_all_details)
│   depends on: quality/boilerplate.py
│   writes to: DataManager.save_raw
│   output: pd.DataFrame (with full_text)
│
├─ Step 5:  analyze()         ──→ nlp/preprocess.py, nlp/entities.py, multilingual/detect.py
│   depends on: config.settings (get)
│   writes to: DataManager.save_analyzed
│   output: pd.DataFrame (with entities, language, category, sentiment)
│
├─ Step 6:  entity_graph()    ──→ intelligence/entity_graph.py
│   depends on: config.settings (atomic_write_json), networkx
│   writes to: output/entity_graph.json
│
├─ Step 7:  cross_domain()    ★──→ intelligence/relationships.py
│   depends on: → compute/embeddings.py (encode_texts)
│                → config.settings (get, atomic_write_json)
│                → networkx (impact chains)
│                ⚡ → Ollama (localhost:11434) LLM verification
│   writes to: output/sector_map.json, cross_domain_links.json, impact_chains.json
│   output: dict (links, chains, sector_map)
│
├─ Step 8:  causal()          ──→ intelligence/causal.py
│   depends on: → config.settings (get), networkx, pandas
│   writes to: output/causal_analysis.json
│   input: cross_domain_result (sector_map + entity_pairs)
│
├─ Step 9:  narratives()      ──→ intelligence/narratives.py
│   depends on: → compute/embeddings.py (encode_texts)
│                → config.settings (atomic_write_json)
│                → bertopic (optional), networkx, pandas
│   writes to: output/narrative_evolution.json
│
├─ Step 10: signals()          ──→ intelligence/signals.py
│    depends on: → config.settings (atomic_write_json)
│    reads: output/cross_domain_links.json (for new vs. previous)
│    writes to: output/breaking_events.json
│
├─ Step 11: multi_agent()      ──→ intelligence/agents.py
│    depends on: → config.settings (get, atomic_write_json)
│                ⚡ → Ollama (localhost:11434) — Analyst, Critic, Summarizer
│    writes to: output/multi_agent_analysis.json
│    input: cross_domain_links + impact_chains
│
├─ Step 12: temporal()         ──→ intelligence/temporal.py
│    depends on: → config.settings (get, atomic_write_json)
│    input: narrative_data (for phase_map)
│    writes to: output/temporal_patterns.json
│
├─ Step 13: briefings()        ──→ intelligence/briefings.py
│    depends on: → config.settings (get, atomic_write_json)
│    input: cross_domain_links, sector_map, impact_chains, agent_result, temporal_result, narrative_data
│    writes to: output/intelligence_briefing.json
│
├─ Step 14: alerts()           ──→ intelligence/alerting.py
│    depends on: → config.settings (get, atomic_write_json)
│    input: cross_domain_links + temporal_result (velocities, bursts, transitions)
│    writes to: output/alerts.json
│
├─ Step 15: export()           ──→ dashboard/backend/exporter.py (lazy import)
│    depends on: → config.settings (get, atomic_read_json, path_for)
│    writes to: output/exports/*.json, *.csv, *.md
│
├─ Step 16: neo4j()            ──→ vector_store/neo4j_store.py (optional)
│    depends on: → config.settings (get), neo4j driver
│    writes to: Neo4j graph database
│
└─ Step 17: vector_index()     ──→ vector_store/chroma_store.py
     depends on: → compute/embeddings.py (encode_texts)
                  → config.settings (path_for)
                  → chromadb, rank_bm25
     writes to: output/chroma_db/
4. THIRD-PARTY LIBRARY DEPENDENCY MAP
4.1 Python Packages (requirements.txt)
Package               Used By                                        Purpose
───────               ───────                                        ───────
requests              scraper/client.py                               HTTP client with retry
                      intelligence/agents.py                          Ollama API calls
                      intelligence/relationships.py                   Ollama API calls
beautifulsoup4        scraper/sources.py                              HTML parsing
pandas                pipeline.py, scraper/sources.py                 DataFrame persistence
                      quality/dedup.py, storage/manager.py            and transformation
                      intelligence/*.py, vector_store/chroma_store.py
                      nlp/sentiment.py
numpy                 pipeline.py, intelligence/*.py                  Array ops, statistics
                      quality/dedup.py, compute/embeddings.py
                      vector_store/chroma_store.py
scikit-learn          quality/dedup.py                                TF-IDF vectorization
nltk                  nlp/sentiment.py                                VADER lexicon
pyyaml                config/settings.py                              YAML config parser
joblib                (model serialization, referenced in output/)
lxml                  (XML parser, transitive via bs4)
pyarrow               storage/manager.py                              Parquet file I/O
networkx              intelligence/entity_graph.py                    Graph construction,
                      intelligence/relationships.py                    centrality, shortest
                      intelligence/causal.py                           path, impact chains
feedparser            scraper/rss_scraper.py                           RSS feed parsing
sentence-transformers compute/embeddings.py                           BGE-M3 embeddings
                      vector_store/chroma_store.py                    Reranker model
transformers          nlp/entities.py (fallback)                      HuggingFace NER
                      nlp/sentiment.py (optional)                     GPU sentiment
torch                 compute/gpu_manager.py                          GPU detection, backend
langdetect            multilingual/detect.py                          Language detection
gliner                nlp/entities.py                                 Primary NER (large-v2)
chromadb              vector_store/chroma_store.py                    Vector database
rank-bm25             vector_store/chroma_store.py                    BM25 full-text search
bertopic              intelligence/narratives.py                      Topic clustering
4.2 Frontend Packages (package.json)
Package               Version    Used By                              Purpose
───────               ───────    ───────                              ───────
react                  ^19.2.6   All components                       UI framework
react-dom             ^19.2.6   main.tsx                              DOM rendering
@xyflow/react         ^12.10.2  components/charts/relationship-graph  Interactive graph viz
leaflet               ^1.9.4    pages/home.tsx                        Geo map visualization
tailwindcss           ^4.3.0    All components                        Utility CSS
zustand               ^5.0.14   store/dashboard.ts,                   State management
                                components/layout/*.tsx
@tailwindcss/vite     ^4.3.0    vite.config.ts                        Tailwind Vite plugin
@vitejs/plugin-react  ^6.0.2    vite.config.ts                        Vite React plugin
typescript             ~6.0.2   All .ts/.tsx files                    Type checking
vite                  ^8.0.12   vite.config.ts, dev server            Build tool + HMR
5. API ENDPOINTS ↔ DATA SOURCE MAPPING
Endpoint                    Reads From                           Serves To
────────                    ─────────                            ─────────
GET  /api/health            _PIPELINE_STATE (in-memory)         App.tsx (30s poll)
GET  /api/pipeline-status   _PIPELINE_STATE                     header.tsx
POST /api/trigger-pipeline  (triggers _run_pipeline thread)     header.tsx button
GET  /api/cross-domain      cross_domain_links.json             explore.tsx, home.tsx
                             impact_chains.json
                             sector_map.json
GET  /api/entity-graph      entity_graph.json                   explore.tsx (ReactFlow)
GET  /api/narratives        narrative_evolution.json            timeline.tsx
GET  /api/signals           breaking_events.json                signals.tsx
GET  /api/search?q=         chroma_store.semantic_search()      search.tsx
GET  /api/explain?source=   cross_domain_links.json + explanation.py  explore.tsx (panel)
GET  /api/causal-analysis   causal_analysis.json                (not used in frontend)
GET  /api/multi-agent-analysis multi_agent_analysis.json        (not used in frontend)
GET  /api/temporal-patterns temporal_patterns.json              (not used in frontend)
GET  /api/briefing          intelligence_briefing.json          briefing.tsx
GET  /api/alerts            alerts.json                         alerts.tsx
POST /api/export?fmt=       (generates export files)            (not used in frontend)
GET  /api/neo4j-status      Neo4jStore.get_statistics()         (not used in frontend)
POST /api/auth/login        auth.py (in-memory JSON)            (not used)
POST /api/auth/register     auth.py                             (not used)
WS   /ws                    ws.py (broadcast)                   App.tsx (WebSocket)
6. CONFIGURATION MANAGEMENT
config.yaml  (99 lines)
       │
       ▼
config/settings.py  (loaded at module import time)
       │
       ├── load_config()        → yaml.safe_load → global _CONFIG dict
       ├── get(key, default)    → traverses _CONFIG with dot notation
       ├── path_for(key)        → resolves path from _CONFIG["paths"]
       ├── atomic_write_json()  → temp file + shutil.move + threading.Lock
       └── atomic_read_json()   → json.load with error handling
       
       All 35+ non-init modules call get() and path_for() directly at import or runtime.
       No dependency injection — global singleton pattern.
Config keys used by each module:
- scraper.* — client.py, rss_scraper.py, sources.py
- nlp.* — preprocess.py
- quality.* — dedup.py (via pipeline.py)
- intelligence.* — relationships.py, agents.py, temporal.py, causal.py, briefings.py, alerting.py, confidence.py
- vector_store.* — chroma_store.py (via path_for)
- alerts.* — alerting.py
- auth.* — auth.py
- scheduler.* — main.py
- logging.* — pipeline.py (setup_logging)
- paths.* — ALL modules via path_for()
7. CLASS HIERARCHY
GPUManager  (compute/gpu_manager.py)
   ├── __init__() → detect CUDA, set self.device
   ├── device() → property
   ├── is_cuda() → bool
   └── __new__ → singleton pattern

DataManager  (storage/manager.py)
   ├── __init__() → resolve paths from config
   ├── load_raw() → pd.read_csv
   ├── save_raw() → df.to_csv
   ├── load_analyzed() → pd.read_parquet / pd.read_csv (fallback)
   ├── save_analyzed() → df.to_parquet / df.to_csv (fallback)
   ├── merge_new_articles() → dedup + concat
   ├── drop_redundant_columns() → cleanup
   └── get_existing_keys() → set of (title, link, source) tuples

Neo4jStore  (vector_store/neo4j_store.py)
   ├── __init__() → connect or graceful disable
   ├── store_sector_map()
   ├── store_cross_domain_links()
   ├── store_impact_chains()
   ├── get_statistics()
   └── close()
8. EXTERNAL SERVICE INTEGRATION HEAT MAP
Service              Protocol        Port    Module               Mandatory?  Fallback
───────              ────────        ────    ──────               ──────────  ────────
Ollama (LLM)         HTTP/REST       11434   intelligence/        No          Statistical-only
                                             relationships.py                heuristics
                                             agents.py
Web Sources (4)      HTTP/HTML       443     scraper/sources.py   Yes         None
(TOI, HT, IE, NDTV)
RSS Feeds (111+)     HTTP/RSS        443     scraper/rss_scraper  Yes         None
Neo4j Graph DB       Bolt            7687    vector_store/        No          Disabled (config)
                                             neo4j_store.py                  degrades to JSON
ChromaDB             Local file I/O  N/A     vector_store/        No          No search index
                                             chroma_store.py
HuggingFace Hub      HTTPS           443     nlp/entities.py      No          Regex NER
(transformers)
GLiNER Hub           HTTPS           443     nlp/entities.py      No          HF NER → Regex
(PyPI, HF)
9. DEPENDENCY CHAIN CRITICALITY ANALYSIS
Red (hard failures — pipeline stops)
pipeline.py
  └── config/settings.py          ← EVERYTHING depends on this
  └── scraper/sources.py          ← step_scrape() fail → no data
  └── scraper/rss_scraper.py      ← step_rss() fail → reduced data
  └── storage/manager.py          ← step_dedup/fetch fail → data loss
  └── nlp/entities.py             ← step_analyze() fail → no entities
Yellow (degraded but functional)
intelligence/relationships.py     ← No LLM = statistical only, no causal
intelligence/narratives.py        ← No BERTopic = keyword fallback
intelligence/agents.py            ← No Ollama = template fallback
vector_store/chroma_store.py      ← No ChromaDB = no semantic search
compute/embeddings.py             ← No BGE = no semantic scoring, no vector index
Green (optional enhancements)
vector_store/neo4j_store.py       ← Disabled by default
nlp/sentiment.py (GPU path)       ← Falls back to VADER CPU
multilingual/detect.py            ← Falls back to langdetect
dashboard/backend/auth.py         ← Disabled by default
nlp/entities.py (HF NER path)     ← Falls back to regex
10. DATA FLOW ACROSS MODULE BOUNDARIES
Inter-module data structure:
┌──────────────────────────────────────────────────────────────┐
│  pd.DataFrame (columns: title, description, link,           │
│    source, published, full_text, entities [JSON str],        │
│    language, category, sentiment, analyzed_at)               │
│                                                              │
│  Shared across: pipeline.py, scraper/*, quality/*,          │
│    nlp/*, storage/manager.py, intelligence/*                │
└──────────────────────────────────────────────────────────────┘

Intelligence data structures (all passed as dicts/lists):
├── sector_map: Dict[str, Dict]     ← entity → {sector, confidence, type}
├── cross_domain_links: List[Dict]  ← {source, target, strength, score, ...}
├── impact_chains: List[Dict]       ← {chain, sectors, hops, weight}
├── narrative_data: Dict            ← {mutations, entity_narratives, cluster_narratives}
├── temporal_result: Dict           ← {velocities, anomalies, bursts, transitions}
├── agent_result: Dict              ← {analyst, critic, summarizer}
├── briefing_result: Dict           ← {exec_summary, sector_situations, watch_items}
└── alert_result: Dict              ← {alerts, summary}

All cross-pipeline communication via output/*.json files (atomic I/O).
Pipeline steps pass in-memory results as function return values,
but the API layer reads only from the JSON files — NOT from memory.
11. KEY DESIGN METRICS
Metric	Count
Total Python files	46 (11 empty __init__.py, 35 with code)
Total TypeScript/TSX files	13
Total lines Python	~4,800 (estimated)
Total lines TypeScript/TSX	~3,500 (estimated)
Pipeline steps	17
API endpoints	19
Frontend pages	7
RSS feeds configured	118
Web scrapers	4
External services integrated	7 (Ollama, Neo4j, ChromaDB, HF, GLiNER, 4 websites, 111 RSS)
Classes	3 (GPUManager, DataManager, Neo4jStore)
Configuration keys	~50 (in config.yaml)
Atomic I/O operations	all JSON writes use temp+rename+lock
Cascading fallback chains	NER: 3-level, Sentiment: 2-level, Clustering: 2-level, Language: 2-level

Now I have complete coverage of all runtime paths. Here is the detailed runtime behavior analysis.
NewsPulse — Runtime Behavior Analysis
1. APPLICATION STARTUP SEQUENCE
1.1 Backend Server Startup (python dashboard/backend/main.py)
Step 1: Module import
   │
   ├── config/settings.py executes at import time:
   │     ├── Sets _CONFIG = None (global)
   │     ├── Defines threading.Lock for atomic I/O
   │     └── load_config() NOT yet called — lazy
   │
   ├── dashboard/backend/ws.py executes:
   │     └── Creates empty _clients: Set[WebSocket]
   │
   └── dashboard/backend/auth.py executes:
         └── Defines USERS_FILE path (output/data/users.json)

Step 2: load_config() called at module level (line 24)
   │
   ├── Reads config.yaml using yaml.safe_load
   ├── Populates global _CONFIG dict
   └── All subsequent get() calls now resolve from this dict

Step 3: FastAPI app construction (line 172)
   │
   ├── app = FastAPI(title="NewsPulse Intelligence API", version="3.0")
   ├── CORS middleware added (allow all origins)
   ├── 19 route handlers registered (via decorators)
   ├── WebSocket endpoint registered (/ws)
   └── lifespan handler registered

Step 4: Lifespan context manager enters (asynccontextmanager)
   │
   ├── start_scheduler() called
   │     ├── Checks scheduler.enabled config (default: true)
   │     ├── Creates daemon thread with target=_scheduler_loop
   │     ├── Thread sets _SCHEDULER_STOP = threading.Event()
   │     ├── Thread starts: _scheduler_loop()
   │     │     ├── sleep(initial_delay_seconds=10)
   │     │     ├── _run_pipeline()  ← FIRST PIPELINE RUN
   │     │     ├── Update _PIPELINE_STATE
   │     │     ├── _broadcast_pipeline_complete() via new event loop
   │     │     ├── _update_state(next_run_at=now + interval)
   │     │     └── _SCHEDULER_STOP.wait(interval * 60s)  ← BLOCK
   │     │
   │     └── Returns immediately (daemon thread)
   │
   └── yield — FastAPI begins serving requests
         on port 8765 (or $PORT env var)

Step 5: uvicorn.run(app, host="0.0.0.0", port=8765)
   │
   ├── ASGI server starts
   └── Requests now accepted

Step 6: On shutdown
   └── stop_scheduler() sets _SCHEDULER_STOP Event
         → scheduler loop exits on next iteration
1.2 Frontend Startup (npm run dev)
vite.config.ts:
   ├── react() plugin
   ├── tailwindcss() plugin
   ├── resolve alias: @ → ./src
   └── proxy: /api → http://localhost:8765

Browser loads index.html:
   └── <script type="module" src="/src/main.tsx">

main.tsx:
   ├── import "./index.css"  ← Tailwind + CSS variables
   ├── import App from "./App"
   └── createRoot(document.getElementById("root")!).render(
         <StrictMode><App /></StrictMode>
       )

App.tsx initial render:
   ├── Sets healthy = null (unknown)
   ├── Returns loading spinner: "Connecting..."
   ├── useEffect fires on mount:
   │     ├── api.health() → fetch("/api/health")
   │     ├── On success: healthy=true, update Zustand pipeline state
   │     ├── On failure: healthy=false
   │     ├── Starts 30s polling interval (setInterval)
   │     └── Returns cleanup: clearInterval
   │
   ├── Ctrl+K listener registered via useEffect
   │
   └── After health check resolves:
         ├── healthy=true  → <MainLayout> with {pages[activeTab]}
         └── healthy=false → "Backend unavailable" with retry button
2. REQUEST/RESPONSE LIFECYCLE
2.1 Typical REST Request (e.g., GET /api/cross-domain)
USER ACTION: User navigates to Explore page → API call triggered
   │
   ▼
BRWSR → fetch("http://localhost:5173/api/cross-domain")
   │
   ▼
VITE DEV SERVER (port 5173)
   ├── Matches /api/* → proxy rule in vite.config.ts
   └── Forwards to http://localhost:8765/api/cross-domain
   │
   ▼
UVICORN (port 8765)
   ├── Receives HTTP request
   ├── FastAPI matches route: @app.get("/api/cross-domain")
   ├── CORS middleware checks origin (allowed: *)
   ├── No auth middleware applied (auth.enabled=false by default)
   │
   ▼
cross_domain() → dashboard/backend/main.py:243
   ├── _load_intel("cross_domain_links.json")
   │     ├── path = path_for("output_dir") + "/cross_domain_links.json"
   │     ├── atomic_read_json(path)
   │     │     ├── Opens file, reads, json.load
   │     │     ├── On error: returns None
   │     │     └── Thread-safe: no lock (read-only)
   │     └── _clean() → recursively removes NaN/Inf from floats
   │
   ├── _load_intel("impact_chains.json") — same pattern
   ├── _load_intel("sector_map.json") — same pattern
   │
   └── Returns dict { links, chains, sector_map }
         │
         ▼
   FastAPI serializes to JSON (auto via jsonable_encoder)
         │
         ▼
   uvicorn sends HTTP 200 response
         │
         ▼
   Vite proxy relays to browser
         │
         ▼
   api.ts fetchJSON<T>() receives Response
         ├── r.ok? (status 200-299)
         ├── r.json() → typed as CrossDomainData
         └── Returns to calling page component
2.2 WebSocket Lifecycle
CONNECTION:
   ── Browser: new WebSocket("ws://localhost:5173/ws")
   ── Vite proxy forwards to :8765/ws
   ── FastAPI: @app.websocket("/ws") → websocket_endpoint()
   ── ws.connect(ws):
         ├── await ws.accept()
         └── _clients.add(ws)
   ── Server enters while True:
         ├── await ws.receive_text()  ← HANGS until client sends
         └── (server ignores client-side messages — just keeps alive)

RECEPTION:
   ── Backend triggers _broadcast_pipeline_complete():
         ├── Creates new asyncio event loop (synchronous bridge)
         ├── ws.broadcast_pipeline_complete(state)
         │     └── broadcast("pipeline_complete", data)
         │           └── For each client in _clients:
         │                 ├── ws.send_text(json.dumps({
         │                 │     event, data, timestamp
         │                 │   }))
         │                 └── On error: mark client dead → discard
         └── Loop closed

DISCONNECT:
   ── Browser closes tab → WebSocketDisconnect raised
   ── ws_disconnect(ws): _clients.discard(ws)
3. DATA PROCESSING PIPELINE (Full Trace)
3.1 Pipeline Execution Thread
Thread: pipeline-scheduler (daemon)
   │
   └── _scheduler_loop()
         └── while not _SCHEDULER_STOP.is_set():
               │
               ├── _run_pipeline()
               │     │
               │     ├── _update_state(status="running")
               │     │     ├── Acquires _STATE_LOCK
               │     │     └── Updates _PIPELINE_STATE dict
               │     │
               │     ├── start = time.time()
               │     │
               │     ├── run_pipeline()  ← BLOCKING (15-300s)
               │     │     ├── DataManager() [creates path resolvers]
               │     │     │
               │     │     ├── step_scrape(data_mgr)  [Phase 1]
               │     │     │     ├── scrape_all_sources() → list of dicts
               │     │     │     │     ├── ThreadPoolExecutor(max_workers=8?)
               │     │     │     │     ├── 4 web scrapers (TOI, HT, IE, NDTV)
               │     │     │     │     ├── Each: fetch() + BeautifulSoup
               │     │     │     │     └── Returns articles with {title, link, source, description, published}
               │     │     │     └── data_mgr.merge_new_articles(new)
               │     │     │           ├── Loads existing CSV via load_raw()
               │     │     │           ├── Compares (title, source, link) against existing
               │     │     │           ├── Only appends truly new articles
               │     │     │           └── save_raw() → output/data/news_data.csv
               │     │     │
               │     │     ├── step_scrape_rss(data_mgr)  [Phase 1]
               │     │     │     ├── scrape_all_rss()
               │     │     │     │     ├── ThreadPoolExecutor(max_workers=8)
               │     │     │     │     ├── Iterates 118 RSS_FEEDS
               │     │     │     │     ├── Each: feedparser.parse(url)
               │     │     │     │     └── Returns articles
               │     │     │     └── data_mgr.merge_new_articles(new)
               │     │     │
               │     │     ├── step_dedup(df, data_mgr)  [Phase 1]
               │     │     │     ├── deduplicate_exact(df): exact title match
               │     │     │     ├── deduplicate_semantic(df, 0.85):
               │     │     │     │     ├── TfidfVectorizer on titles
               │     │     │     │     └── cosine_similarity → drop if >0.85
               │     │     │     └── data_mgr.save_raw(df)
               │     │     │
               │     │     ├── step_fetch_details(df, data_mgr)  [Phase 1]
               │     │     │     ├── Remove boilerplate (43 regex patterns)
               │     │     │     ├── Extract clean title
               │     │     │     └── fetch_all_details(df): HTTP GET each article URL
               │     │     │           └── ThreadPoolExecutor for parallel fetching
               │     │     │
               │     │     ├── step_analyze(df, data_mgr)  [Phase 2]
               │     │     │     ├── Load existing analyzed data (parquet)
               │     │     │     ├── Filter: only new articles (by title+link+source)
               │     │     │     ├── clean_text(title + description)
               │     │     │     ├── extract_category() → (category, clean_title)
               │     │     │     ├── extract_entities_batch(texts):
               │     │     │     │     ├── For each text: extract_entities(text)
               │     │     │     │     │     ├── GLiNER.predict_entities (if available)
               │     │     │     │     │     ├── ELSE: HF pipeline("token-classification")
               │     │     │     │     │     └── ELSE: regex fallback
               │     │     │     │     └── Returns JSON string
               │     │     │     ├── detect_language(text) → en/hi/ur/...
               │     │     │     └── data_mgr.save_analyzed(df) → parquet
               │     │     │
               │     │     ├── step_entity_graph(df)  [Phase 3]
               │     │     │     ├── build_entity_graph(df, max_age=90d)
               │     │     │     │     ├── NetworkX graph from entity co-occurrence
               │     │     │     │     └── Degree centrality computation
               │     │     │     └── atomic_write → output/entity_graph.json
               │     │     │
               │     │     ├── step_cross_domain(df)  ★ [Phase 3 — THE CORE]
               │     │     │     ├── cross_domain_pipeline(df):
               │     │     │     │     ├── build_sector_map(df):
               │     │     │     │     │     ├── Extract all entities from all articles
               │     │     │     │     │     ├── classify_entity_sector(name, type, context):
               │     │     │     │     │     │     ├── Score against SECTOR_KEYWORDS (keyword → +1.0)
               │     │     │     │     │     │     ├── Score against SECTOR_ORGS (org match → +1.5)
               │     │     │     │     │     │     ├── Score against context text (→ +0.3 each)
               │     │     │     │     │     │     └── Best sector wins, confidence = score/5.0
               │     │     │     │     │     └── Returns Dict[entity → {sector, confidence, type, mention_count}]
               │     │     │     │     │
               │     │     │     │     ├── find_cross_domain_links(df, sector_map):
               │     │     │     │     │     ├── Find article entity pairs from different sectors
               │     │     │     │     │     ├── Score = cooccurrence*0.35 + diversity*0.25 + semantic*0.40
               │     │     │     │     │     ├── Semantic similarity via BGE-M3 embeddings
               │     │     │     │     │     └── Return top 200 links
               │     │     │     │     │
               │     │     │     │     ├── apply_llm_verification(links):
               │     │     │     │     │     ├── For links with strength >= 2.0:
               │     │     │     │     │     │     ├── POST to http://localhost:11434/api/generate
               │     │     │     │     │     │     │     ├── model: qwen3:14b (or configured)
               │     │     │     │     │     │     │     ├── prompt: entity1/entity2/sectors/context
               │     │     │     │     │     │     │     ├── timeout: 45s
               │     │     │     │     │     │     │     └── max tokens: 384
               │     │     │     │     │     │     └── Parse JSON response → causal direction, mechanism, impact
               │     │     │     │     │     └── _calibrate_confidence(link, llm_result):
               │     │     │     │     │           ├── base = stat_score*0.5 + sem_score*0.5
               │     │     │     │     │           └── if llm: final = base*0.4 + llm_conf*0.6
               │     │     │     │     │
               │     │     │     │     ├── predict_cross_domain_impact(links):
               │     │     │     │     │     └── Sector pair → lookup impact_patterns dict
               │     │     │     │     │           (e.g., politics→finance = "Market volatility")
               │     │     │     │     │
               │     │     │     │     ├── build_impact_chains(df, sector_map):
               │     │     │     │     │     ├── Build NetworkX graph of entity co-occurrences
               │     │     │     │     │     ├── For each unique sector pair → nx.shortest_path
               │     │     │     │     │     └── Return top 50 chains by cross-domain hops
               │     │     │     │     │
               │     │     │     │     └── generate_relationship_explanations(links):
               │     │     │     │           └── Template-based fallback if LLM didn't provide one
               │     │     │     │
               │     │     │     └── atomic_write 3 files:
               │     │     │           ├── output/sector_map.json
               │     │     │           ├── output/cross_domain_links.json
               │     │     │           └── output/impact_chains.json
               │     │     │
               │     │     ├── step_causal(df, sector_map, entity_pairs)  [Phase 3]
               │     │     │     ├── causal_pipeline(df, sector_map, entity_pairs)
               │     │     │     │     ├── For each entity pair: detect temporal lag (6h-14d)
               │     │     │     │     ├── build_causal_graph() → NetworkX with causal edges
               │     │     │     │     └── find_causal_chains() → multi-hop chains
               │     │     │     └── atomic_write → output/causal_analysis.json
               │     │     │
               │     │     ├── step_narratives(df)  [Phase 3]
               │     │     │     ├── narrative_pipeline(df):
               │     │     │     │     ├── cluster_articles_bertopic(df):
               │     │     │     │     │     ├── BERTopic(embedding_model=None, min_topic_size=3)
               │     │     │     │     │     ├── Uses BGE-M3 embeddings passed directly
               │     │     │     │     │     └── Returns cluster assignments
               │     │     │     │     ├── compute_entity_narratives(df):
               │     │     │     │     │     ├── Per-entity daily mention counts
               │     │     │     │     │     └── detect_narrative_phases(trajectory):
               │     │     │     │     │           ├── emerging / accelerating / growing
               │     │     │     │     │           ├── peaked / declining / fading
               │     │     │     │     │           └── dormant / resurging / stable
               │     │     │     │     ├── compute_cluster_narratives(df, cluster_data)
               │     │     │     │     ├── compute_narrative_mutation(df):
               │     │     │     │     │     └── Keyword drift across 7-day windows
               │     │     │     │     └── find_emerging/disappearing_topics()
               │     │     │     └── atomic_write → output/narrative_evolution.json
               │     │     │
               │     │     ├── step_signals(df)  [Phase 3]
               │     │     │     ├── signals_pipeline(df):
               │     │     │     │     ├── detect_cross_domain_spillover():
               │     │     │     │     │     ├── Compare word freq in last 48h vs older
               │     │     │     │     │     └── burst = recent_freq / older_freq; flag if >5x
               │     │     │     │     ├── signal_new_relationships():
               │     │     │     │     │     └── Compare entity pairs against previous cycle
               │     │     │     │     └── Deduplicate + sort by score
               │     │     │     └── atomic_write → output/breaking_events.json
               │     │     │
               │     │     ├── step_multi_agent(cross_domain_links, impact_chains)  [Phase 4]
               │     │     │     ├── multi_agent_pipeline():
               │     │     │     │     ├── analyst_agent():
               │     │     │     │     │     ├── Take top 10 links + top 5 chains
               │     │     │     │     │     ├── POST to Ollama → structured JSON findings
               │     │     │     │     │     └── Fallback: template-graded findings
               │     │     │     │     ├── critic_agent(findings, links):
               │     │     │     │     │     ├── POST to Ollama → critiques + confidence gaps
               │     │     │     │     │     └── Fallback: statistical quality assessment
               │     │     │     │     └── summarizer_agent(findings, critiques):
               │     │     │     │           ├── POST to Ollama → briefing + key developments
               │     │     │     │           └── Fallback: template summary
               │     │     │     └── atomic_write → output/multi_agent_analysis.json
               │     │     │
               │     │     ├── step_temporal(df, narrative_data)  [Phase 4]
               │     │     │     ├── temporal_pipeline(df, phase_map):
               │     │     │     │     ├── _extract_daily_entity_counts(df)
               │     │     │     │     ├── compute_entity_velocity():
               │     │     │     │     │     ├── recent_rate (last 7d) / prior_rate
               │     │     │     │     │     └── velocity = recent - prior, acceleration = vel/prior
               │     │     │     │     ├── detect_velocity_anomalies():
               │     │     │     │     │     └── Z-score ≥ 2.0 → anomaly (spike/drop)
               │     │     │     │     ├── detect_bursts():
               │     │     │     │     │     └── Per-day z-score ≥ 2.5 and count ≥ 2
               │     │     │     │     └── predict_phase_transitions():
               │     │     │     │           └── Rule-based: accel/velocity → next phase prediction
               │     │     │     └── atomic_write → output/temporal_patterns.json
               │     │     │
               │     │     ├── step_briefings(links, map, chains, agents, temporal, narratives)  [Phase 4]
               │     │     │     ├── generate_briefing():
               │     │     │     │     ├── Build sector_situations from sector_map + links
               │     │     │     │     ├── Build key_connections from top links
               │     │     │     │     ├── Build watch_items from agent_result + anomalies
               │     │     │     │     └── Build predictions (template: sector pairs)
               │     │     │     └── atomic_write → output/intelligence_briefing.json
               │     │     │
               │     │     ├── step_alerts(links, temporal_result)  [Phase 5]
               │     │     │     ├── alerting_pipeline():
               │     │     │     │     ├── Load previous cross_domain_links
               │     │     │     │     ├── eval_relationship_alerts():
               │     │     │     │     │     └── New link with confidence ≥0.8 → HIGH
               │     │     │     │     │     └── New LLM-verified link≥0.7 → MEDIUM
               │     │     │     │     ├── eval_velocity_alerts():
               │     │     │     │     │     └── accel>3.0 AND vel>2.0 → HIGH
               │     │     │     │     ├── eval_burst_alerts():
               │     │     │     │     │     └── burst_factor ≥ 3.0 → HIGH
               │     │     │     │     └── eval_phase_alerts():
               │     │     │     │           └── transition confidence ≥ 0.7 → MEDIUM
               │     │     │     └── atomic_write → output/alerts.json
               │     │     │
               │     │     ├── step_export()  [Phase 5]
               │     │     │     ├── Lazy-import exporter module
               │     │     │     ├── export_json, export_csv, export_markdown
               │     │     │     └── Write to output/exports/ with timestamp
               │     │     │
               │     │     ├── step_neo4j(sector_map, links, chains)  [Phase 5 — optional]
               │     │     │     ├── If neo4j.enabled:
               │     │     │     │     ├── Neo4jStore(uri, user, password)
               │     │     │     │     ├── store_sector_map() → CREATE nodes
               │     │     │     │     ├── store_cross_domain_links() → CREATE edges
               │     │     │     │     ├── store_impact_chains() → CREATE paths
               │     │     │     │     └── get_statistics() → {entities, relationships}
               │     │     │     └── Graceful: catch all exceptions, log warning
               │     │     │
               │     │     └── step_vector_index(df)  [Phase 5]
               │     │           ├── index_articles(df):
               │     │           │     ├── Build text from title+description
               │     │           │     ├── BGE-M3 embeddings via encode_texts()
               │     │           │     ├── ChromaDB collection.add() in batches of 128
               │     │           │     └── Also builds BM25 index for hybrid search
               │     │           └── Returns count of indexed articles
               │     │
               │     └── Returns cross_domain_result, narrative_result, temporal_result,
               │           agent_result, briefing_result, causal_result
               │
               ├── duration = round(time.time() - start, 1)
               │
               ├── _update_state(status="idle", last_run=now, duration, success=true, ...)
               │     └── _broadcast_pipeline_complete()
               │           ├── New asyncio event loop
               │           └── ws.broadcast("pipeline_complete", {duration, success, ...})
               │
               └── _SCHEDULER_STOP.wait(interval * 60)
4. AUTHENTICATION & AUTHORIZATION FLOW
CONFIG: auth.enabled = false (default)
   │
   ├── When DISABLED (default):
   │     ├── No middleware on any endpoint
   │     ├── /api/auth/login returns {"status": "auth_disabled"}
   │     └── All endpoints accessible without credentials
   │
   └── When ENABLED:
         ├── USERS_FILE = output/data/users.json
         ├── Default user: admin/admin (SHA-256)
         ├── Roles: viewer(1) < analyst(2) < admin(3)
         │
         ├── REGISTER:
         │     POST /api/auth/register?username=X&password=Y&role=Z
         │     ├── validate role
         │     ├── check duplicate
         │     ├── hash password (SHA-256)
         │     └── atomic_write_json to users.json
         │
         ├── LOGIN:
         │     POST /api/auth/login?username=X&password=Y
         │     ├── _load_users()
         │     ├── hash + compare
         │     └── Return { user, token: "placeholder-jwt" }
         │
         └── AUTHORIZATION (per-request):
               require_role("analyst"):
                 ├── Read X-User-Role header
                 ├── Compare against required role level
                 └── 403 if insufficient

               require_auth():
                 ├── Check X-User header exists
                 └── 401 if missing

      NOTE: Auth is skeleton-level. JWT tokens are placeholder-only.
            Role checking uses HTTP headers (should come from proxy).
5. ERROR HANDLING MECHANISMS
Layer 1 — Pipeline step errors (pipeline.py):
   ├── Each step is a top-level try/except in _run_pipeline():
   │     ├── Except Exception → error = f"{type}: {msg}"
   │     ├── _update_state(status="error", last_error=error)
   │     ├── Logged with stack trace
   │     └── Pipeline continues to next interval (fail_safe=true)
   │
   └── step_export() / step_neo4j() / step_vector_index():
         └── Each wraps in try/except → log warning → continue

Layer 2 — Graceful degradation (cross-module):
   ├── NER: GLiNER → HF → regex (3-level)
   ├── Sentiment: HF GPU → VADER CPU (2-level)
   ├── Language: fastText → langdetect (2-level)
   ├── Clustering: BERTopic → keyword-based (2-level)
   ├── LLM verification: Ollama → statistical-only (2-level)
   ├── Multi-agent: Ollama → template (2-level)
   ├── Vector search: ChromaDB → no search (graceful)
   ├── Neo4j: disabled by default → degrades to JSON (graceful)
   └── Parquet: → CSV fallback (2-level storage)

Layer 3 — API error handling (main.py):
   ├── _clean(): removes NaN/Inf from JSON responses
   │     └── Prevents JSON serialization crashes
   ├── _load_intel(): returns {} if file missing or corrupt
   ├── /api/search: returns {"error": msg, "results": []}
   ├── /api/explain: returns {"error": "relationship not found"}
   └── /api/export: returns {"error": str(e)}

Layer 4 — Frontend error handling:
   ├── App.tsx:
   │     ├── health check fails → "Backend unavailable" + retry button
   │     └── Empty state for each page when no data
   ├── All api.ts calls chain .catch(() => [])
   ├── home.tsx: Promise.all with .catch for each API
   ├── explore.tsx: loading=true/false state, spinner
   └── search.tsx: try/catch → empty results

Layer 5 — Thread safety:
   ├── _PIPELINE_STATE: threading.Lock for all R/W
   ├── atomic_write_json: threading.Lock + temp-file + rename
   └── DataManager: file-based persistence (no cross-thread issues)
6. EVENT-DRIVEN WORKFLOWS
EVENT: Pipeline Completes
   │
   ├── _broadcast_pipeline_complete() called from _run_pipeline()
   │
   ├── Creates new asyncio event loop (bridge from sync→async)
   │
   ├── ws.broadcast("pipeline_complete", {
   │     duration, success, articles_analyzed, run_count
   │   })
   │
   ├── Each connected WebSocket client receives JSON:
   │     {
   │       "event": "pipeline_complete",
   │       "data": { duration, success, ... },
   │       "timestamp": "2026-05-29T..."
   │     }
   │
   └── Frontend (if WebSocket connected) can update UI reactively
         (Currently: frontend relies on 30s polling, not WebSocket events)

EVENT: Pipeline errors
   │
   ├── _update_state(status="error", last_error=...)
   ├── No WebSocket broadcast on error
   └── Frontend detects on next 30s poll → amber/red dot in header

EVENT: Alert detected
   ├── alerting_pipeline() writes to output/alerts.json
   └── Frontend reads on next refresh (no push notification)

EVENT: Signal detected
   ├── signals_pipeline() writes to output/breaking_events.json
   └── Frontend reads on next refresh

NOTE: WS broadcast for alerts and signals is defined (ws.py lines 55-60)
      but currently NOT called from the pipeline — the functions exist
      but are dead code / not wired.
7. BACKGROUND JOBS & SCHEDULED TASKS
SCHEDULER (dashboard/backend/main.py):
   Type: threading.Thread (daemon)
   Interval: configurable via scheduler.interval_minutes (default: 15)
   Start: on FastAPI lifespan entry
   Stop: threading.Event signal
   Behavior: Blocking — waits for pipeline to complete before sleeping
   State: Exposed via /api/health and /api/pipeline-status

┌─────────────────────────────────────────────────────────────────┐
│  Timeline:                                                       │
│                                                                   │
│  T=0     Server starts                                           │
│  T=10s   First pipeline run (initial_delay_seconds)              │
│  T=10+N  Pipeline completes (N = time for all 17 steps)          │
│  T=10+N  WebSocket broadcast                                     │
│  T=10+N  _update_state, log next run at T=10+N+15min            │
│  T=10+N  _SCHEDULER_STOP.wait(15*60) ← blocks thread            │
│  T=10+N+15m  Second pipeline run                                 │
│  ...     Repeats indefinitely                                    │
│                                                                   │
│  KEY WEAKNESS: Pipeline is SINGLE-THREADED, BLOCKING. If one    │
│  run takes 14 minutes and the interval is 15 minutes, there is   │
│  only 1 minute of downtime between runs. If it exceeds 15 min,   │
│  the next run is delayed.                                        │
└─────────────────────────────────────────────────────────────────┘

MANUAL TRIGGER:
   POST /api/trigger-pipeline
   ├── Creates new daemon thread → _run_pipeline()
   └── Returns immediately: {"status": "triggered"}
8. STATE MANAGEMENT APPROACH
8.1 Backend State
State	Location	Thread Safety
Pipeline status	_PIPELINE_STATE (in-memory dict)	threading.Lock
WebSocket clients	_clients: Set[WebSocket]	No concurrent writes (only lifespan thread)
Article data	DataManager (Parquet/CSV files)	File-based, no concurrent writers
Intelligence outputs	output/*.json	atomic_write_json (temp+rename+lock)
User accounts	output/data/users.json	atomic_write_json
GPU manager	GPUManager singleton	Single initialization
Embedding model	_encoder (module-level cache)	Lazy init, no lock
NER models	_gliner, _hf_ner (module-level cache)	Lazy init, no lock
ChromaDB collection	_collection (module-level cache)	Lazy init, no lock
8.2 Frontend State
State	Store	Location	Source of Truth
Active page tab	useState	App.tsx	User action
Backend health	useState	App.tsx	Polled from /api/health (30s)
Pipeline status	Zustand	store/dashboard.ts	Written by App.tsx polling
Sidebar open/closed	Zustand	store/dashboard.ts	User toggle
Page data (links, signals, etc.)	useState	Each page component	API calls on mount
Search query + results	useState	pages/search.tsx	User action
Selected entity/link	useState	pages/explore.tsx	User interaction
Expanded items	useState	pages/home.tsx	User click
Key observation: There is no global data cache on the frontend. Each page independently fetches and owns its data. If a user navigates from Home to Explore and back, all API calls are re-fired. The Zustand store only holds sidebar toggle and pipeline status (read from health checks). No React Query, no SWR, no Redux — just raw useEffect fetches.
8.3 Data Freshness Model
Pipeline runs
    │
    ▼
atomic_write_json to output/*.json
    │
    ▼ (async, poll-based)
Frontend polls /api/health every 30s
    │
    ├── Updates pipeline status in Zustand
    └── No automatic page data refresh
    │
Page components fetch on MOUNT only
    │
    ├── home.tsx: 3 parallel fetches on mount
    ├── explore.tsx: 1 fetch on mount
    ├── timeline.tsx: 1 fetch on mount
    └── etc.
    │
User must navigate away and back to see fresh data
OR manually trigger pipeline via header
9. FULL USER ACTION TRACE
Scenario: User opens app → navigates to Explore → selects entity → views explanation
STEP 1: USER OPENS http://localhost:5173
   │
   Browser → index.html → main.tsx → App.tsx
   │
   ├── healthy = null → Renders "Connecting..." spinner
   ├── useEffect fires:
   │     └── fetch("/api/health")
   │           → FastAPI: returns { status: "ok", pipeline: {...} }
   │           → healthy = true
   │           → useStore.getState().setPipeline(pipeline)
   │           → Header re-renders with green dot
   │
   ├── App re-renders healthy=true:
   │     └── <MainLayout activeTab="home">
   │           ├── Sidebar → active: "home", label: "Discoveries"
   │           ├── Header → green dot, "Live", "Updated Xm ago"
   │           └── {pages["home"]} = <HomePage />
   │
   └── HomePage renders:
         ├── loading = true → skeleton UI
         ├── useEffect fires:
         │     └── Promise.all([
         │           fetch("/api/cross-domain")     → links, chains
         │           fetch("/api/signals")           → signals
         │           fetch("/api/narratives")        → narratives
         │         ])
         │         → buildFeed() → sorted discoveries
         │         → loading = false
         └── Renders: IntelligenceMap + DiscoveriesList (30 items)

STEP 2: USER CLICKS "Relationships" IN SIDEBAR
   │
   ├── onTabChange("explore") → setActiveTab("explore")
   ├── App re-renders: {pages["explore"]} = <ExplorePage />
   │
   └── ExplorePage renders:
         ├── loading = true → spinner
         ├── useEffect fires:
         │     └── fetch("/api/cross-domain")
         │           → FastAPI: reads atomic_read_json("cross_domain_links.json")
         │           → Returns sorted links + sector_map
         │           → setLinks(sorted links)
         │           → loading = false
         │
         └── Three-column layout renders:
               ├── Left (Entity Discovery):
               │     └── Sectors: politics, finance, technology...
               │     └── Per-sector entity lists with strength
               │
               ├── Center (Graph):
               │     └── ReactFlow graph of all links
               │     └── Nodes colored by sector
               │
               └── Right (Intelligence Panel):
                     └── SampleIntelligence:
                           ├── Stats cards (connections, entities, domains)
                           └── Top 5 relationships by strength

STEP 3: USER CLICKS ON ENTITY "nvidia" IN LEFT PANEL
   │
   ├── handleEntitySelect("nvidia")
   │     ├── setSelectedEntity("nvidia")
   │     └── setSelectedLink(null)
   │
   ├── Memoized recomputation:
   │     ├── connectedLinks = filteredLinks where source or target == "nvidia"
   │     └── (synced from previous full link set, no API call)
   │
   ├── Center panel → FocusedGraph re-renders:
   │     └── ReactFlow graph zooms to nvidia + neighbor nodes only
   │
   └── Right panel re-renders:
         └── "Connections for nvidia":
               ├── List of connected entities with strength
               └── Each button calls setSelectedLink(link)

STEP 4: USER CLICKS A CONNECTED ENTITY IN RIGHT PANEL
   │
   ├── Example: clicks "nvidia ↔ fed" link
   ├── setSelectedLink(link) where link = {
   │     source_entity: "nvidia", target_entity: "fed",
   │     source_sector: "technology", target_sector: "finance",
   │     confidence: 0.82, strength: 12.4, verified: true,
   │     causal_mechanism: "Fed rate decisions affect AI infrastructure investment",
   │     impact_prediction: "Capital reallocation from growth to value",
   │     explanation: "..."
   │   }
   │
   └── Right panel re-renders:
         └── <IntelligencePanel link={link} />
               ├── Relationship details card
               ├── Confidence score with color
               ├── Causal mechanism text
               ├── Impact prediction
               └── Explanation text

   At this point, 4 HTTP requests have been made total:
     1. GET /api/health (App.tsx mount)
     2. GET /api/cross-domain (home.tsx mount)
     3. GET /api/signals (home.tsx mount)
     4. GET /api/narratives (home.tsx mount)
     5. GET /api/cross-domain (explore.tsx mount)

   All subsequent interactions are pure client-side memoized data.

STEP 5: 30 SECONDS LATER
   ├── App.tsx pollInterval fires:
   │     └── fetch("/api/health") → check pipeline status
   │           ├── pipeline.status === "idle" → green dot unchanged
   │           └── pipeline.status === "running" → amber dot, "Processing"
   └── If pipeline just completed:
         ├── pipeline.run_count incremented
         ├── pipeline.last_run_duration updated
         └── Header re-renders (Zustand subscription)
10. CRITICAL RACE CONDITIONS & TIMING ISSUES
RACE 1: Atomic write during API read
   ├── Pipeline writes output/cross_domain_links.json via atomic_write_json
   │     └── temp file → rename (atomic on same filesystem)
   ├── API reads same file via atomic_read_json
   │     └── Opens and reads in one call
   └── RISK: Very low — rename is atomic, read sees complete file or old file

RACE 2: Pipeline thread + manual trigger
   ├── Scheduler loop calls _run_pipeline() (blocking)
   ├── User calls POST /api/trigger-pipeline → new thread
   │     └── Both threads write to same output/*.json files
   └── RESULT: Corrupted output, overlapping writes
         MITIGATION: atomic_write_json uses threading.Lock
                     But it's a MODULE-LEVEL lock — both threads share it
                     So writes are serialized. However, order is unpredictable.

RACE 3: WebSocket broadcast from sync context
   ├── _run_pipeline() is synchronous (runs in daemon thread)
   ├── _broadcast_pipeline_complete() creates new asyncio event loop
   │     └── loop.run_until_complete(broadcast_pipeline_complete())
   ├── If multiple pipeline completions overlap (manual trigger):
   │     └── Multiple event loops created → undefined behavior
   └── RISK: Low (single scheduler, but manual trigger adds second thread)

RACE 4: ChromaDB concurrent index
   ├── step_vector_index() calls collection.add() in batches
   ├── If two pipeline threads run simultaneously:
   │     └── ChromaDB has file-level locks → one will fail
   └── RISK: Medium (manual trigger while scheduler running)
11. MEMORY & RESOURCE LIFECYCLE
┌─────────────────────────────────────────────────────────────────┐
│  MEMORY ALLOCATION PER PIPELINE RUN                              │
│                                                                   │
│  pd.DataFrame (raw)            ~ 10-100 MB (for 1000s articles)  │
│  pd.DataFrame (analyzed)       ~ 10-100 MB                      │
│  BGE-M3 embeddings             ~ 2-4 GB VRAM (GPU)              │
│  BERTopic clustering           ~ 500 MB-1 GB (CPU)              │
│  NetworkX graph                ~ 10-100 MB                      │
│  ChromaDB cache                ~ 100-500 MB (on disk)           │
│  Ollama inference              ~ 8-14 GB VRAM (Qwen3:14b)       │
│                                                                   │
│  PERSISTENT (loaded once at first use, never freed):             │
│    GPUManager          → singleton, lifetime of process          │
│    _encoder (BGE-M3)   → module-level cache, never GC'd         │
│    _gliner (GLiNER)    → module-level cache, never GC'd         │
│    _collection (ChromaDB) → module-level cache, never GC'd      │
│    _reranker (BGE++)   → module-level cache, never GC'd         │
│                                                                   │
│  WARNING: No explicit memory management. Models stay in VRAM    │
│  forever. BERTopic creates new model each run (no .save).       │
└─────────────────────────────────────────────────────────────────┘

NewsPulse — Senior Engineering Code Review
SEVERITY SCALE
CRITICAL — Will cause production incidents or data corruption. Fix immediately.
HIGH — Significantly impacts maintainability, scalability, or correctness. Fix this sprint.
MEDIUM — Violates best practices, creates friction for development. Fix this quarter.
LOW — Cosmetic or nice-to-have improvements.
CRITICAL FINDINGS
C1. No Test Infrastructure (Zero Tests)
Files: 46 Python + 13 TypeScript/TSX = 59 source files
Tests: 0
Test directory: does not exist
Evidence: There is no test/, tests/, __tests__/ directory anywhere. No pytest, unittest, vitest, or jest configuration. No test files exist.
Impact: Every change is a blind deployment. There is no safety net for regression. The pipeline's 17-step orchestration, the NER cascade, the cross-domain scoring formula, the temporal burst detection — none of it is verified. This is the single biggest risk to the project.
Fix: Add pytest and vitest. Start with integration tests for pipeline.py::run_pipeline() (mock the scraper layer, verify the output JSON files contain the correct structure).
C2. Duplicate Pipeline Execution on Startup — No Locking
File: dashboard/backend/main.py:136-153
_time.sleep(initial_delay)  # 10s
while not _SCHEDULER_STOP.is_set():
    _run_pipeline()
    _SCHEDULER_STOP.wait(interval * 60)
File: dashboard/backend/main.py:236-240
@app.post("/api/trigger-pipeline")
def trigger_pipeline():
    t = threading.Thread(target=_run_pipeline, daemon=True)
    t.start()
Problem: POST /api/trigger-pipeline creates a second thread calling _run_pipeline() while the scheduler may already be executing one. Both threads write to the same output/*.json files. The atomic_write_json lock serializes file writes, but the order is unpredictable — data from the two runs interleaves. Furthermore, both threads call _broadcast_pipeline_complete() which creates competing asyncio event loops.
Impact: Corrupted intelligence outputs, conflicting WebSocket broadcasts, undefined behavior. This is a data integrity issue.
Fix: Add a _pipeline_running flag (protected by _STATE_LOCK). Reject trigger-pipeline if already running. Or use a queue. Also: prevent the scheduler from starting a new run if the previous one hasn't finished.
C3. import json and import os Inside Function Bodies
intelligence/causal.py:55     import json  (inside detect_causal_candidates)
intelligence/temporal.py:35   import json  (inside _extract_daily_entity_counts)
intelligence/narratives.py:386 import os   (inside narrative_pipeline)
intelligence/relationships.py:537 import os (inside cross_domain_pipeline)
intelligence/briefings.py:202 import os    (inside generate_briefing)
intelligence/agents.py:210    import os    (inside multi_agent_pipeline)
intelligence/signals.py:226   import os    (inside signals_pipeline)
intelligence/temporal.py:221  import os    (inside temporal_pipeline)
intelligence/alerting.py:172  import os    (inside alerting_pipeline)
Problem: 9 modules have import os or import json inside function bodies rather than at the top of the file. This means:
- The import is re-executed on every function call (minor perf hit)
- It hides the module's true dependencies from tooling (IDE, linters, dependency analyzers)
- It creates inconsistency — pipeline.py has imports at the top
Impact: Technical debt that compounds. Every new contributor will copy this pattern.
Fix: Move all imports to module scope. Run isort or ruff to enforce a single standard.
C4. Atomic Write Paths Hardcoded in Intelligence Modules Instead of Pipeline
Each intelligence module writes its own output files:
intelligence/relationships.py:540-542  → writes 3 files
intelligence/narratives.py:389         → writes 1 file
intelligence/signals.py:226            → writes 1 file
intelligence/causal.py:214             → writes 1 file
intelligence/agents.py:211             → writes 1 file
intelligence/temporal.py:222           → writes 1 file
intelligence/briefings.py:203          → writes 1 file
intelligence/alerting.py:173           → writes 1 file
Problem: The pipeline orchestrator (pipeline.py) calls step functions, but the side effects (file writes) happen deep inside each module. This means:
- You cannot call cross_domain_pipeline() programmatically without it writing to disk
- The pipeline orchestrator has no control over I/O — it cannot skip writes, redirect output, or batch writes
- Testing requires file system mocks
Fix: Have each step function return its data. Have pipeline.py (or a dedicated output manager) own ALL file writes.
HIGH SEVERITY
H1. Duplicated Entity Extraction Logic (7 Copies of the Same Code)
The exact same pattern for loading entities from a DataFrame row and iterating over persons/orgs/locations appears in:
intelligence/relationships.py:111-125    (build_sector_map)
intelligence/relationships.py:286-297   (find_cross_domain_links)
intelligence/relationships.py:396-406   (build_impact_chains)
intelligence/entity_graph.py:40-61      (build_entity_graph)
intelligence/narratives.py:255-269      (compute_entity_narratives)
intelligence/signals.py:53-66           (signal_new_relationships)
intelligence/signals.py:140-155         (_detect_entity_spikes)
intelligence/causal.py:50-64            (detect_causal_candidates)
intelligence/temporal.py:22-43          (_extract_daily_entity_counts)
Example duplicated block (appears 7+ times):  
ents_str = row.get("entities", "{}")
if not isinstance(ents_str, str):
    continue
try:
    entities = json.loads(ents_str)
except (json.JSONDecodeError, TypeError):
    continue
all_ents = []
for key in ("persons", "orgs", "locations"):
    for ent in entities.get(key, []):
        ek = ent.strip().lower()
        if ek and len(ek) > 1:
            all_ents.append(ek)
Impact: If the entity JSON format changes (e.g., adding a "organizations" key alongside "orgs"), all 7+ locations must be updated. This already happened — notice that "technology", "financial entity", and "energy company" labels from GLiNER (defined in nlp/entities.py:11) are silently dropped because the iteration only checks "persons", "orgs", and "locations".
Fix: Extract a shared utility function like _extract_entities_from_row(row) in a common module (e.g., nlp/entities.py or intelligence/common.py).
H2. Two Different Confidence Calibration Functions for Relationships
File: intelligence/relationships.py:195-224 — _calibrate_confidence()
def _calibrate_confidence(link, llm_result=None):
    stat_score = min(link["cooccurrence_count"] * 0.3 + link["source_diversity"] * 0.2, 5.0) / 5.0
    sem_score = link.get("semantic_similarity", 0.0)
    base_confidence = stat_score * 0.5 + sem_score * 0.5
    # ...
    if llm_result:
        link["confidence"] = round(base_confidence * 0.4 + llm_conf * 0.6, 3)
File: intelligence/confidence.py:31-86 — calibrate_relationship_confidence()
def calibrate_relationship_confidence(link, llm_result=None):
    # statistical * 0.35 + source_reliability * 0.10 + semantic * 0.15 
    # + sector_baseline * 0.10 + llm * 0.20 + causal * 0.10
Problem: These two functions do the same job with different formulas and different weights. The relationships.py version uses a simpler formula (stat*0.5 + sem*0.5, then base*0.4 + llm*0.6). The confidence.py version uses 6 weighted signals. Both are called from different code paths:
- relationships.py:381 calls _calibrate_confidence() (local version)
- explanation.py:64 calls calibrate_relationship_confidence() (from confidence module)
Impact: A relationship will have a different confidence value depending on which code path computed it. Users see inconsistent numbers.
Fix: Delete _calibrate_confidence() in relationships.py. Use only confidence.calibrate_relationship_confidence(). The relationships.py pipeline already aggregates all the signals needed.
H3. Dead Code — broadcast_alert and broadcast_signal Never Called
File: dashboard/backend/ws.py:55-60
async def broadcast_alert(alert: Dict):
    await broadcast("alert", alert)

async def broadcast_signal(signal: Dict):
    await broadcast("signal", signal)
Grep confirms: broadcast_alert and broadcast_signal are defined but never imported or called anywhere in the codebase. The alerting pipeline (alerting.py) and signals pipeline (signals.py) write to JSON files but never push to WebSocket. Users must poll to see alerts.
Impact: The WebSocket infrastructure is wired and tested only for pipeline completion. Real-time alert/signal push doesn't work despite being architected for it. This is false advertising of the Phase 5 real-time capability.
Fix: Wire broadcast_alert() into alerting_pipeline(), and broadcast_signal() into signals_pipeline(). Since those run in a sync thread, use the same event-loop bridge pattern as _broadcast_pipeline_complete().
H4. event_detection.py Is Orphaned Legacy Code
File: intelligence/event_detection.py
def detect_breaking_events(df):
File: intelligence/__init__.py — empty
Grep: event_detection — imported nowhere
Impact: Dead code that will rot. A developer reading the codebase will wonder if breaking event detection is running. It's not. It was replaced by signals.py but never deleted.
Fix: Delete event_detection.py.
H5. No URL-Based Routing — State-Based Navigation
File: dashboard/frontend/src/App.tsx:13-21
const pages: Record<string, React.ReactNode> = {
  home: <HomePage />,
  explore: <ExplorePage />,
  // ...
}
Problem: No React Router. Pages are rendered via {pages[activeTab]}. This means:
- No deep linking: localhost:5173/explore doesn't work
- No browser back/forward buttons
- No lazy loading — all pages mount eagerly in memory
- Search engines cannot index individual pages
Impact: This becomes a blocker as soon as the project needs to share links or support multi-tab browsing. Adding React Router later will require rewriting all page mounting logic.
Fix: Add react-router-dom. Convert <App> to use <Routes>. Keep the sidebar as <NavLink> components.
H6. Hardcoded Ollama URL in Two Places
File: intelligence/relationships.py:173
resp = requests.post(
    "http://localhost:11434/api/generate",
    ...
)
File: intelligence/agents.py:28
resp = requests.post(
    "http://localhost:11434/api/generate",
    ...
)
Problem: The Ollama endpoint URL is hardcoded. If Ollama runs on a different host, port, or via a unix socket (common in Docker), changes must be made in two places.
Fix: Add ollama.base_url: "http://localhost:11434" to config.yaml. Read via get("ollama.base_url") in both modules. Even better: extract a shared _ollama_call() utility.
H7. Near-Identical Ollama HTTP Calling Code Duplicated
File: intelligence/relationships.py:147-192 — _llm_verify_relationship()
File: intelligence/agents.py:21-44 — _ollama_generate()
Both functions:
- Build a POST request to http://localhost:11434/api/generate
- Set stream: False
- Parse response.json()["response"]
- Handle requests.exceptions with logger.debug fallback
- Return Optional[str] / Optional[Dict]
Impact: A change to Ollama API (e.g., adding API key header, changing JSON format) requires edits in two files. The timeout values differ (45s vs 60s) with no explanation why.
Fix: Extract a shared intelligence/ollama.py module with ollama_generate(prompt, model, timeout).
H8. No Response Validation — FastAPI Relies on Raw dict
File: dashboard/backend/main.py:243-252
@app.get("/api/cross-domain")
def cross_domain():
    links = _load_intel("cross_domain_links.json")
    chains = _load_intel("impact_chains.json")
    sector_map = _load_intel("sector_map.json")
    return {
        "links": links if isinstance(links, list) else [],
        "chains": chains if isinstance(chains, list) else [],
        "sector_map": sector_map if isinstance(sector_map, dict) else {},
    }
Problem: No Pydantic models for request or response validation. The API returns raw dicts. If cross_domain_links.json has corrupted data, the API silently serves it. The frontend TypeScript types (types/index.ts) are the only contract — and they are not enforced at runtime.
Impact: Field name mismatches between backend and frontend (e.g., causal_direction vs direction) are not caught until runtime. Backend changes can silently break the frontend.
Fix: Define Pydantic models for all API responses. Use response_model=CrossDomainResponse in endpoint decorators.
MEDIUM SEVERITY
M1. Frontend Renders All Pages in Memory at All Times
File: dashboard/frontend/src/App.tsx:13-21
const pages: Record<string, React.ReactNode> = {
  home: <HomePage />,
  explore: <ExplorePage />,
  // ... all 7 pages created on every render
}
Problem: Every navigation press creates a new React element for ALL pages, React diffs them, and keeps unused ones in the virtual DOM. With 7 pages each fetching 1-3 API calls, this means:
- 10+ HTTP requests fire on mount (for the initial home page, all other pages are also constructed but their useEffect hasn't fired yet — actually they haven't been rendered yet)
- Actually, since only {pages[activeTab]} is rendered, this is only a minor issue. But the Record is recreated every render.
Actual fix: Use React.lazy() for page components:
const HomePage = React.lazy(() => import("@/pages/home"));
const ExplorePage = React.lazy(() => import("@/pages/explore"));
M2. Global Mutable Caches Are Not Thread-Safe
# compute/embeddings.py:7
_encoder = None

# nlp/entities.py:8-9
_gliner = None
_hf_ner = None

# vector_store/chroma_store.py:32-35
_collection = None
_bm25_index = None
Problem: Module-level mutable caches are initialized lazily without locks. If two pipeline threads somehow call _get_encoder() simultaneously (e.g., from relationships.py and chroma_store.py), the SentenceTransformer could be loaded twice. While Python's GIL prevents truly concurrent execution, the daemon thread + manual trigger creates unpredictable timing.
Impact: Double model loading wastes VRAM. Very unlikely to crash, but shows lack of thread-safety discipline.
Fix: Add threading.Lock() guards to all lazy-init patterns. Or better, initialize all models in init_gpu() or a dedicated init_models() call.
M3. Template-Based Sector Explanations Are Hardcoded
File: intelligence/explanation.py:91-112 — 12 hardcoded sector pair templates
File: intelligence/relationships.py:233-246 — 12 hardcoded impact patterns
File: intelligence/confidence.py:17-28 — 8 hardcoded sector baselines
File: intelligence/causal.py:20-31 — 10 hardcoded causal patterns
Problem: There are 4 different hardcoded sector-pair dictionaries across 4 modules. They all cover roughly the same pairs but with different keys and values. Adding a new sector requires updating all 4 dictionaries. There is no single source of truth for sector interaction models.
Impact: The system cannot discover novel cross-domain patterns — it can only surface what's been pre-programmed. This undermines the "discovery engine" value proposition.
Fix: Consolidate all sector interaction data into config.yaml. Better yet, derive interaction templates from the actual co-occurrence data rather than hardcoding them.
M4. remove_boilerplate() Discards Lines Without Testing Context
File: quality/boilerplate.py:55-56
if len(stripped) < 15:
    continue
Problem: Any line shorter than 15 characters is unconditionally removed. This discards legitimate content like headlines, dates, bylines, and short factual sentences. The extract_clean_title() function also strips everything after |, -, –, :, « — which may remove meaningful context.
Impact: The pipeline permanently loses article content due to over-aggressive cleaning. This is a silent data loss issue.
Fix: Use position-aware heuristics (boilerplate is more likely at the bottom; short lines at the start may be legitimate). Add word-count thresholds instead of character thresholds.
M5. dangerouslySetInnerHTML for SVG Icons
File: dashboard/frontend/src/components/layout/sidebar.tsx:52-54
<span
  className="shrink-0"
  dangerouslySetInnerHTML={{ __html: NAV_ICONS[item.id] }}
/>
Problem: The 7 SVG icons are stored as raw HTML strings and injected with dangerouslySetInnerHTML. This is a React anti-pattern that bypasses React's XSS protection. While the SVGs are static, this sets a bad precedent.
Impact: If a future developer adds dynamic content to NAV_ICONS, they open an XSS vulnerability.
Fix: Import SVGs as React components or use inline JSX for the icons.
M6. Frontend Data is Never Refreshed After Initial Load
All pages fetch data on mount but never re-fetch:
// explore.tsx:177
useEffect(() => {
    api.crossDomain().then(...)
}, [])
// home.tsx:266
useEffect(() => {
    Promise.all([...]).then(...)
}, [])
Problem: The useEffect dependency arrays are empty ([]), so data is fetched once when the component mounts. If the user is on the Explore page and the pipeline completes in the background, they see stale data until they navigate away and back.
Impact: Users see outdated intelligence. The header shows "Live" but the data may be 15+ minutes old. This undermines the "real-time" UX.
Fix: Add a re-fetch interval or a refetch-on-focus mechanism. Or use the WebSocket to trigger re-fetch when pipeline completes.
M7. Pipeline State Check on Every Header Render
File: dashboard/frontend/src/components/layout/header.tsx:15
const { toggleSidebar, pipeline } = useStore()
Zustand store selection: This subscribes the header to all Zustand state changes. Every time ANY part of the store changes (e.g., sidebar toggle), the header re-renders.
Impact: Trivially small for this app, but shows lack of Zustand selector optimization.
Fix: Use selector functions: useStore((s) => s.pipeline) and useStore((s) => s.toggleSidebar) separately.
M8. Config Singleton Cannot Be Overridden for Testing
File: config/settings.py
_CONFIG = None

def get(key, default=None):
    # reads from _CONFIG
Problem: load_config() is called once at module import time. There is no API to inject a test configuration. Any test that needs different config values must either mock config.settings.get or set environment variables.
Impact: Writing isolated unit tests that change config values (e.g., test with llm_verification=True vs False) requires monkey-patching.
Fix: Make get() accept an optional override dict, or use a config class that can be instantiated per test.
M9. No .gitignore for Output Data
File: .gitignore — exists but let me verify content
Let me check:
→ Read .gitignore 
Thought: 1.7s
Good — the .gitignore does cover output data directories. But there are some issues I noticed:

- output/logs/ is ignored but the pipeline writes logs there
- output/chroma_db/ is ignored (correct)
- But output/exports/ is NOT ignored — exports could be committed
- The JSON output files (cross_domain_links.json, etc.) in output/ are NOT covered by any .gitignore pattern

Actually wait, output/data/ is ignored, but output/logs/ is ignored too. But the actual intelligence JSON files like output/cross_domain_links.json are in output/ directly — they would be tracked by git. That's actually intentional to have example output in the repo? No, that seems like they'd be committed unintentionally.

Let me continue with the review. I have enough now to compile the full report.
Good — .gitignore exists and covers sensitive directories. Noted for the review.
LOW SEVERITY
L1. Pipeline Thread Blocks the Scheduler (No Parallelism)
while not _SCHEDULER_STOP.is_set():
    _run_pipeline()          # BLOCKS for 2-10+ minutes
    _SCHEDULER_STOP.wait(interval * 60)  # THEN sleeps
If the pipeline takes 14 minutes and the interval is 15 minutes, the system is idle only 1 minute per cycle. The pipeline is entirely single-threaded — scraping, NER, topic modeling, LLM calls all run sequentially. With 111 RSS feeds + 3 LLM calls per link + BERTopic, this is the primary performance bottleneck.
Fix: Scrape in parallel (already done via ThreadPoolExecutor). Run LLM verification in parallel batches. Move vector indexing to a separate process.
L2. get_existing_keys() Duplicates merge_new_articles() Logic
File: storage/manager.py:119-125 and 68-102
The key-generation logic (title.lower(), source.strip(), link.strip()) is duplicated between get_existing_keys() and merge_new_articles(). Any change to how dedup keys work requires updating both methods.
L3. nltk VADER Download Not Handled
File: nlp/sentiment.py uses NLTK's VADER, which requires nltk.download('vader_lexicon'). The code does not handle the LookupError that occurs on first run.
L4. No __main__ Guard in dashboard/backend/main.py
Line 415: if __name__ == "__main__": — correctly guarded. But the module-level load_config() call on line 24 executes at import time. Importing main.py as a module (e.g., for testing) triggers config loading and begins side effects.
L5. Frontend: All Pages Use useEffect Without AbortController
useEffect(() => {
    api.crossDomain().then(setLinks)
}, [])
If the user navigates away before the API call completes, React logs a Can't perform a React state update on an unmounted component warning. The fetch should have an AbortController.
L6. compute/__init__.py Re-exports DEVICE That Doesn't Exist
File: compute/__init__.py:1
from compute.gpu_manager import GPUManager, device, is_cuda, DEVICE
But gpu_manager.py defines device as a function and is_cuda as a function — there is no DEVICE constant. This will raise an ImportError on from compute import *.
SUMMARY TABLE
ID	Severity	Category	File(s)	Issue
C1	CRITICAL	Testing	Entire repo	Zero tests — no safety net
C2	CRITICAL	Concurrency	main.py	No lock on manual+scheduler pipeline trigger
C3	CRITICAL	Code quality	9 files	import inside function bodies
C4	CRITICAL	Architecture	8 intelligence modules	Side-effect file writes bypass orchestrator
H1	HIGH	Duplication	7+ files	Entity extraction logic copy-pasted 7 times
H2	HIGH	Correctness	relationships.py, confidence.py	Two different confidence formulas
H3	HIGH	Dead code	ws.py	broadcast_alert/signal defined but never wired
H4	HIGH	Dead code	event_detection.py	Orphaned legacy module
H5	HIGH	Architecture	App.tsx	No URL routing — state-based only
H6	HIGH	Config	relationships.py, agents.py	Ollama URL hardcoded in 2 places
H7	HIGH	Duplication	relationships.py, agents.py	Duplicate Ollama HTTP caller
H8	HIGH	Robustness	main.py	No Pydantic response validation
M1	MED	Performance	App.tsx	No lazy loading for pages
M2	MED	Concurrency	embeddings.py, entities.py, chroma_store.py	Global caches not thread-safe
M3	MED	Duplication	4 modules	4 different hardcoded sector-pair dicts
M4	MED	Data loss	boilerplate.py	Removes lines <15 chars unconditionally
M5	MED	Security	sidebar.tsx	dangerouslySetInnerHTML for SVGs
M6	MED	UX	All pages	No data refresh after mount
M7	MED	Performance	header.tsx	Oversubscribed Zustand selector
M8	MED	Testability	config/settings.py	Singleton cannot be overridden
L1	LOW	Performance	main.py	Pipeline blocks scheduler thread
L2	LOW	Duplication	storage/manager.py	Dedup key logic duplicated
L3	LOW	Robustness	nlp/sentiment.py	VADER download not handled
L4	LOW	Design	main.py	Module-level side effects on import
L5	LOW	UX	All pages	No AbortController on fetch
L6	LOW	Bug	compute/__init__.py	Imports non-existent DEVICE
KEY THEMES
1. Copy-paste is the dominant engineering pattern — entity extraction, Ollama calls, sector dictionaries, confidence calibration. 7+ copies of the same entity loop. This is the single strongest signal of insufficient abstraction.
2. Intelligence modules have too many responsibilities — they extract, compute, calibrate, explain, AND persist to disk. The pipeline orchestrator is a thin coordinator with no control over side effects.
3. The project is pre-quality — zero tests, no CI, no linting rules (ruff, mypy, eslint, prettier). The .gitignore is incomplete for the output directory. The code compiles and runs, but there is no quality gate.
4. Frontend is fragile — state-based routing, no caching, no error boundaries, no loading skeletons per data point, dangerouslySetInnerHTML. It works for a demo but will not scale to real users.
5. The architecture has good bones — graceful degradation everywhere, atomic I/O, modular pipeline steps, WebSocket infrastructure, config-driven design. The raw materials are solid; the execution shortcuts (copy-paste, no tests, no models) are what need attention.
