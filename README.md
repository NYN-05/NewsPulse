# NewsPulse — AI-Powered Media Intelligence Platform

GPU-accelerated news aggregation, NLP analysis, cross-domain relationship discovery, narrative evolution tracking, influence mapping, and interactive intelligence dashboard. Scrapes 96+ RSS feeds across 8 sectors (politics, finance, technology, energy, military, startups, social, global events) and surfaces hidden connections between them.

## Intelligence Features

### 🧠 Cross-Domain Relationship Engine
- Automatically maps every entity to one of 8 sectors using keyword + context classification
- Discovers hidden connections between entities **across sectors** (e.g., Iran ↔ Strait of Hormuz = global_events ↔ energy)
- Builds multi-hop **impact chains** (e.g., China export restrictions → semiconductor policy → startup funding)
- Scores relationship strength by co-occurrence count, source diversity, and sentiment variance
- Output: `cross_domain_links.json`, `impact_chains.json`, `sector_map.json`

### 🕸 Interactive Graph Visualization (Frontend)
- **React Flow** interactive entity graph — drag, zoom, pan, click nodes
- Color-coded by entity type (person/organization/location) or sector
- Edge thickness indicates relationship weight
- Dedicated **Cross-Domain Explorer** page with sector-colored relationship map + impact chain view
- Toggle between relationship map and impact chain views

### ⏳ Narrative Evolution Tracker
- Tracks how narratives mutate across consecutive time windows (keyword drift scoring)
- Classifies every entity and cluster into lifecycle phases: **emerging, accelerating, growing, peaked, stable, declining, fading, resurging**
- Detects **emerging topics** (high acceleration + recent appearance) and **disappearing topics** (fading mentions)
- Tracks sentiment trajectory per narrative over time
- Output: `narrative_evolution.json`

### 📡 Influence Mapping
- **Entity Influence Scoring** — combines mention volume, recency, source diversity, cross-domain links, centrality, and sentiment impact
- **Source Amplification Scoring** — measures each source's reach (entities covered), category breadth, article volume, sentiment extremity, and sensationalism
- **Information Propagation** — tracks how fast narratives spread across sources (adoption time, density, spread speed)
- Output: `influence_map.json`

### Core Pipeline
- Scraping (RSS + web), dedup, NLP analysis, clustering, trend detection, historical comparison
- Entity graph (NetworkX, 3000+ nodes), breaking news detection, topic evolution, source reliability
- GPU-accelerated via HuggingFace Transformers on CUDA (RTX 4050):
  - Sentiment (distilbert), summarization (t5-small), NER (dslim/bert-base-NER), embeddings (all-MiniLM-L6-v2), KMeans clustering
- Semantic search via ChromaDB vector index
- Slack alerts for breaking events and virality spikes
- Multilingual detection (891+ non-English articles flagged)

## Pipeline Steps

```
scrape → rss → dedup → fetch → analyze → cluster → trends → compare →
entity_graph → entity_trends → breaking → topics → reliability →
cross_domain → narratives → influence → vector_index → track → alerts
```

(19 steps)

## Dashboard Pages (17)

| Page | Description |
|------|-------------|
| **Overview** | KPIs, trend chart, categories, languages |
| **Sentiment** | Distribution pie + average over time |
| **Categories** | Article counts by category |
| **Topic Clusters** | Cluster cards with sentiment + top sources |
| **Trends** | Rising keywords bar chart |
| **Entity Graph** | Interactive React Flow graph + centrality table + communities |
| **Entity Trends** | Entity momentum + detail cards |
| **Cross-Domain** | Sector-colored relationship map + impact chains + link table |
| **Narratives** | Emerging/disappearing topics, cluster/entity lifecycle phases |
| **Influence Map** | Entity influence scores, source amplification, propagation speed |
| **Breaking News** | Signal cards with burst factors |
| **Virality** | Score distribution + top viral articles |
| **Bias & Reliability** | Political leaning, source reliability scores |
| **Topic Evolution** | Cluster trajectory area charts |
| **Semantic Search** | ChromaDB-powered search with relevance scores |
| **Data Explorer** | Filterable article table |

## Project Structure

```
├── pipeline.py              # 19-step orchestrator
├── config/                  # YAML configuration
├── scraper/                 # RSS and web scraping
├── nlp/                     # Sentiment, summarization, NER, preprocessing
├── intelligence/            # ★ New intelligence modules
│   ├── cross_domain.py      # Cross-domain relationship engine
│   ├── narrative_tracker.py # Narrative evolution lifecycle
│   ├── influence.py         # Entity influence + source amplification
│   ├── entity_graph.py      # Entity co-occurrence graph (NetworkX)
│   ├── bias.py              # Political bias + clickbait detection
│   ├── virality.py          # Virality scoring
│   ├── event_detection.py   # Breaking news
│   └── topics.py            # Topic evolution
├── analytics/               # Trends, comparison, clustering
├── alerts/                  # Slack alert engine
├── multilingual/            # Language detection
├── vector_store/            # ChromaDB semantic search
├── rag/                     # RAG chatbot
├── storage/                 # Parquet/JSON persistence
├── compute/                 # GPU/CPU device management
├── dashboard/
│   ├── backend/main.py      # FastAPI REST server (port 8765) — 17+ endpoints
│   └── frontend/            # React 19 + TypeScript + Vite 6 app (port 5173)
│       ├── src/pages/       # 17 dashboard pages
│       ├── src/charts/      # Recharts + React Flow graph components
│       └── src/components/  # shadcn-style UI components
└── requirements.txt
```

## Requirements

- **Python 3.10+** with CUDA-capable GPU (optional, CPU fallback)
- **Node 20+** and **npm 10+** for the dashboard frontend

```bash
pip install -r requirements.txt
cd dashboard/frontend && npm install
```

## How to Run

### 1. Pipeline (data collection + analysis)

```bash
python pipeline.py
```

~3.5 min for ~4300 new articles. To run specific steps:

```python
# In Python or modify pipeline.py
from pipeline import run_pipeline
run_pipeline(steps=["analyze", "cross_domain", "narratives", "influence"])
```

### 2. Dashboard (two terminals)

**Terminal A — FastAPI backend:**

```bash
python dashboard/backend/main.py
```

17+ REST endpoints on `http://localhost:8765`.

**Terminal B — React frontend:**

```bash
cd dashboard/frontend
npm run dev
```

On `http://localhost:5173` (proxies `/api` to backend).

### 3. Semantic Search

```python
from vector_store.chroma_store import semantic_search
results = semantic_search("defense policy and AI startups", n_results=10)
```

### 4. RAG Chatbot

```python
from rag.chatbot import NewsChatbot
bot = NewsChatbot()
answer = bot.ask("How are semiconductor policies affecting Indian startups?")
```

## GPU Acceleration

- Auto-detects CUDA 12 on RTX 4050 (or any CUDA device)
- Falls back to CPU if no GPU available
- GPU: sentiment, summarization, NER, embeddings, KMeans clustering
- Managed centrally via `compute/gpu_manager.py`

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Pipeline | Python, HuggingFace Transformers, PyTorch, scikit-learn |
| Intelligence | NetworkX, numpy, pandas, sentence-transformers |
| Vector Store | ChromaDB |
| Graph Viz | React Flow (@xyflow/react) |
| Backend API | FastAPI + uvicorn |
| Frontend | React 19, TypeScript, Vite 6, Tailwind CSS v4 |
| Charts | Recharts + React Flow |
| State | Zustand |
| UI | Radix UI, shadcn-style, Framer Motion |
| Alerts | Slack Webhook (Block Kit) |
