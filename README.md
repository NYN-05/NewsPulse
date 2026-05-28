# NewsPulse — AI-Powered Media Intelligence

GPU-accelerated news aggregation, NLP analysis, and analytics dashboard. Scrapes 96+ RSS feeds, performs multi-stage NLP (sentiment, summarization, NER, clustering, entity extraction), detects breaking news, scores virality, analyzes bias, and visualizes everything through a React dashboard.

## Features

- **Scraping** — RSS feed aggregation (96+ unique feeds), deduplication, article fetch
- **NLP Pipeline** — GPU-accelerated via HuggingFace Transformers on CUDA (RTX 4050):
  - Sentiment analysis (distilbert)
  - Summarization (t5-small)
  - Named entity recognition (dslim/bert-base-NER + NLTK fallback)
  - Topic clustering (sentence-transformers + GPU KMeans)
  - Entity graph construction (NetworkX)
- **Intelligence** — Breaking news detection, virality scoring, bias/clickbait detection, multilingual detection (891+ non-English articles flagged)
- **Semantic Search** — ChromaDB vector index with sentence-transformers embeddings
- **RAG Chatbot** — Retrieval-augmented generation over indexed articles
- **Alerting** — Slack alerts for breaking events and virality spikes
- **Analytics** — Trend detection, historical comparison, entity momentum, topic evolution
- **Dashboard** — React 19 + TypeScript + Vite 6 with 13 interactive pages, dark theme, responsive

## Pipeline Steps

```
scrape → rss → dedup → fetch → analyze → cluster → trends → compare →
entity_graph → entity_trends → breaking → topics → reliability →
vector_index → track → alerts
```

## Project Structure

```
├── pipeline.py              # 17-step orchestrator
├── config/                  # YAML configuration, feed list
├── scraper/                 # RSS and web scraping
├── nlp/                     # Sentiment, summarization, NER, preprocessing
├── intelligence/            # Entity graph, virality, bias, breaking news
├── analytics/               # Trends, comparison, entity trends, clustering
├── alerts/                  # Alert engine (Slack)
├── multilingual/            # Language detection
├── vector_store/            # ChromaDB semantic search index
├── rag/                     # RAG chatbot
├── storage/                 # Parquet/JSON persistence, column management
├── compute/                 # GPU/CPU device management
├── output/                  # Generated data, logs, ChromaDB index
├── dashboard/
│   ├── backend/main.py      # FastAPI REST server (port 8765)
│   └── frontend/            # React 19 + TypeScript + Vite 6 app (port 5173)
│       ├── src/pages/       # 13 dashboard pages
│       ├── src/charts/      # Recharts wrappers (bar, line, area, pie)
│       ├── src/components/  # shadcn-style UI components
│       └── src/services/    # Axios API layer + Zustand store
└── requirements.txt
```

## Requirements

- **Python 3.10+** with CUDA-capable GPU (optional, CPU fallback)
- **Node 20+** and **npm 10+** for the dashboard frontend
- Python packages: `pip install -r requirements.txt`
- Frontend packages: `cd dashboard/frontend && npm install`

## How to Run

### 1. Pipeline (data collection + analysis)

```bash
python pipeline.py
```

Takes ~3.5 minutes for ~4300 new articles. Output saved to `output/data/` as Parquet + JSON.

### 2. Dashboard (two terminals)

**Terminal A — FastAPI backend:**

```bash
python dashboard/backend/main.py
```

Serves REST API on `http://localhost:8765` with 15+ endpoints.

**Terminal B — React frontend:**

```bash
cd dashboard/frontend
npm run dev
```

Serves on `http://localhost:5173` (proxies `/api` to the backend).

### 3. Semantic Search

```python
from vector_store.chroma_store import ArticleVectorStore
store = ArticleVectorStore()
results = store.find_similar("your query", top_k=5)
```

### 4. Chatbot (RAG)

```python
from rag.chatbot import NewsChatbot
bot = NewsChatbot()
answer = bot.ask("What is happening with climate change?")
```

## GPU Acceleration

- Auto-detects CUDA 12 on RTX 4050 (or any CUDA device)
- Falls back to CPU if no GPU available
- GPU used for: sentiment, summarization, NER, embeddings, KMeans clustering
- Device managed centrally via `compute/device.py`

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Pipeline | Python, HuggingFace Transformers, PyTorch, scikit-learn |
| Vector Store | ChromaDB + sentence-transformers |
| Graph Analytics | NetworkX |
| Backend API | FastAPI + uvicorn |
| Frontend | React 19, TypeScript, Vite 6, Tailwind CSS v4 |
| Charts | Recharts |
| State | Zustand |
| UI | Radix UI primitives, shadcn-style, Framer Motion |
| Alerts | Slack Webhook (Block Kit) |
