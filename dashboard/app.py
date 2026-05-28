import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from storage.manager import DataManager
from config.settings import load_config, get
from compute.gpu_manager import GPUManager
from vector_store.chroma_store import semantic_search, get_collection_stats
from rag.chatbot import ask, query_articles
from intelligence.entity_graph import build_entity_graph
from intelligence.event_detection import detect_breaking_events
from intelligence.virality import predict_virality
from intelligence.bias import analyze_bias, compute_source_reliability
from intelligence.topics import track_topic_evolution

load_config()
plt.rcParams["figure.dpi"] = 120

st.set_page_config(page_title="NewsPulse Intelligence", layout="wide")
st.title("NewsPulse Intelligence Dashboard")

data_mgr = DataManager()
df = data_mgr.load_analyzed()

if df.empty:
    st.error("Run the analysis pipeline first!")
    st.stop()

# Sidebar
st.sidebar.header("Filters")
sentiment_filter = st.sidebar.multiselect("Sentiment", ["positive", "negative", "neutral"], default=[])
category_filter = st.sidebar.multiselect("Category", df["category"].dropna().unique() if "category" in df.columns else [], default=[])
source_filter = st.sidebar.multiselect("Source", df["source"].dropna().unique() if "source" in df.columns else [], default=[])
days_back = st.sidebar.slider("Days", 1, 30, 7)

# Filter
filtered = df.copy()
if "published" in filtered.columns and filtered["published"].notna().sum() > 0:
    time_col = "published"
elif "scraped_at" in filtered.columns:
    time_col = "scraped_at"
else:
    time_col = None
if time_col:
    filtered["_ts"] = pd.to_datetime(filtered[time_col], errors="coerce")
    cutoff = datetime.now() - timedelta(days=days_back)
    filtered = filtered[filtered["_ts"] >= cutoff]
if sentiment_filter:
    filtered = filtered[filtered["sentiment"].isin(sentiment_filter)]
if category_filter:
    filtered = filtered[filtered["category"].isin(category_filter)]
if source_filter:
    filtered = filtered[filtered["source"].isin(source_filter)]

# KPIs
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Articles", len(filtered))
if not filtered.empty and "compound" in filtered.columns:
    col2.metric("Avg Sentiment", f"{filtered['compound'].mean():.3f}")
if "sensationalism_score" in filtered.columns:
    col3.metric("Avg Sensationalism", f"{filtered['sensationalism_score'].mean():.3f}")
if "virality_score" in filtered.columns:
    col4.metric("Avg Virality", f"{filtered['virality_score'].mean():.3f}")
vs = get_collection_stats()
col5.metric("Vector Index", vs.get("count", 0))

tabs = st.tabs([
    "Sentiment", "Categories", "Sensationalism", "Clusters", "Virality",
    "Entity Graph", "Breaking News", "Bias & Reliability", "Topic Evolution",
    "Semantic Search", "Ask NewsPulse", "Data"
])

# --- Tab 1: Sentiment ---
with tabs[0]:
    if "sentiment" in filtered.columns:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        filtered["sentiment"].value_counts().plot(kind="pie", ax=ax1, autopct="%1.1f%%", ylabel="")
        ax1.set_title("Sentiment Distribution")
        filtered["compound"].hist(bins=20, ax=ax2, edgecolor="black")
        ax2.set_title("Compound Score Distribution")
        st.pyplot(fig)
        if "sentiment" in filtered.columns and "source" in filtered.columns:
            st.subheader("Sentiment by Source")
            ct = pd.crosstab(filtered["source"], filtered["sentiment"])
            st.dataframe(ct, use_container_width=True)

# --- Tab 2: Categories ---
with tabs[1]:
    if "category" in filtered.columns:
        cats = filtered["category"].fillna("Uncategorized").value_counts().head(20)
        fig, ax = plt.subplots(figsize=(10, 5))
        cats.plot(kind="barh", ax=ax)
        ax.set_title("Top Categories")
        ax.set_xlabel("Count")
        st.pyplot(fig)
    else:
        st.info("No category data")

# --- Tab 3: Sensationalism ---
with tabs[2]:
    if "sensationalism_score" in filtered.columns:
        top = filtered.nlargest(20, "sensationalism_score")
        fig, ax = plt.subplots(figsize=(10, 5))
        titles = [t[:50] for t in (top.get("clean_title") if "clean_title" in top.columns else top["title"])]
        colors = ["red" if s == "negative" else "green" if s == "positive" else "gray" for s in top["sentiment"]]
        ax.barh(range(len(top)), top["sensationalism_score"], color=colors)
        ax.set_yticks(range(len(top)))
        ax.set_yticklabels(titles, fontsize=8)
        ax.set_xlabel("Sensationalism Score")
        ax.set_title("Most Sensational Headlines")
        st.pyplot(fig)

# --- Tab 4: Clusters ---
with tabs[3]:
    if "cluster" in filtered.columns and "cluster_label" in filtered.columns:
        clusters = filtered.groupby("cluster_label").size().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(10, 4))
        clusters.plot(kind="bar", ax=ax)
        ax.set_title("Article Clusters")
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig)
        cl = st.selectbox("Explore cluster", clusters.index.tolist())
        if cl:
            st.dataframe(filtered[filtered["cluster_label"] == cl][["title", "source", "sentiment"]].head(10), use_container_width=True)
    else:
        st.info("Run clustering first")

# --- Tab 5: Virality ---
with tabs[4]:
    if "virality_score" in filtered.columns:
        st.subheader("Virality Distribution")
        fig, ax = plt.subplots(figsize=(10, 4))
        filtered["virality_score"].hist(bins=20, ax=ax, edgecolor="black")
        ax.set_xlabel("Virality Score")
        st.pyplot(fig)
        st.subheader("Most Viral Articles")
        viral = filtered.nlargest(10, "virality_score")
        for _, r in viral.iterrows():
            with st.expander(f"{r.get('title', '')[:80]} — Score: {r['virality_score']:.2f}"):
                st.write(f"**Source:** {r.get('source', '')} | **Sentiment:** {r.get('sentiment', '')} | **Sensationalism:** {r.get('sensationalism_score', 0):.3f}")
                st.write(r.get("summary", "")[:300])
    else:
        st.info("Run NLP analysis with virality scoring")

# --- Tab 6: Entity Graph ---
with tabs[5]:
    st.subheader("Entity Relationship Graph")
    if st.button("Build Entity Graph") or os.path.exists("output/entity_graph.json"):
        if os.path.exists("output/entity_graph.json"):
            with open("output/entity_graph.json") as f:
                graph = json.load(f)
        else:
            graph = build_entity_graph(filtered)
        if "stats" in graph:
            st.json(graph["stats"])
            if graph.get("nodes"):
                st.subheader("Top Entities by Centrality")
                nodes_df = pd.DataFrame(graph["nodes"])
                st.dataframe(nodes_df.sort_values("centrality", ascending=False), use_container_width=True)
            if graph.get("edges"):
                st.subheader("Entity Connections")
                edges_df = pd.DataFrame(graph["edges"])
                st.dataframe(edges_df.head(20), use_container_width=True)
    else:
        st.info("Click 'Build Entity Graph' to generate")

# --- Tab 7: Breaking News ---
with tabs[6]:
    st.subheader("Breaking News Detection")
    if st.button("Detect Breaking Events"):
        events = detect_breaking_events(filtered)
        if events:
            st.success(f"{len(events)} breaking signals detected")
            for e in events[:10]:
                kw = e.get("keyword") or e.get("entity", "?")
                st.metric(kw, f"Score: {e.get('score', 0):.1f}", f"{e.get('recent_count', 0)} mentions")
        else:
            st.info("No breaking events detected")
    else:
        st.info("Click 'Detect Breaking Events' to scan")

# --- Tab 8: Bias & Reliability ---
with tabs[7]:
    st.subheader("Bias Analysis")
    sample = filtered.sample(min(5, len(filtered)))
    if "text" in sample.columns:
        for _, r in sample.iterrows():
            bias = analyze_bias(r.get("text", ""))
            with st.expander(f"{r.get('title', '')[:60]} — {bias['political_leaning']}"):
                st.json(bias)
    st.subheader("Source Reliability")
    if st.button("Score Sources"):
        reliability = compute_source_reliability(filtered)
        if reliability:
            rel_df = pd.DataFrame.from_dict(reliability, orient="index")
            st.dataframe(rel_df.sort_values("reliability_score", ascending=False), use_container_width=True)

# --- Tab 9: Topic Evolution ---
with tabs[8]:
    st.subheader("Topic Evolution Over Time")
    if "cluster" in filtered.columns:
        evolution = track_topic_evolution(filtered)
        if "clusters" in evolution:
            for c in evolution["clusters"][:5]:
                if c.get("trajectory"):
                    traj = pd.DataFrame(c["trajectory"])
                    traj["date"] = pd.to_datetime(traj["date"])
                    fig, ax = plt.subplots(figsize=(8, 2))
                    ax.plot(traj["date"], traj["count"], marker="o")
                    ax.set_title(f"Cluster {c['cluster']}: {c.get('label', '')} ({c['total_articles']} articles)")
                    st.pyplot(fig)
    else:
        st.info("Run clustering first")

# --- Tab 10: Semantic Search ---
with tabs[9]:
    st.subheader("Semantic Article Search")
    query = st.text_input("Search query", placeholder="e.g., 'Karnataka political crisis'")
    if query:
        with st.spinner("Searching..."):
            results = semantic_search(query)
        if results:
            st.success(f"Found {len(results)} results")
            for r in results:
                with st.expander(f"{r['title']} ({r['source']}) — Score: {r['score']:.3f}"):
                    st.write(f"**Source:** {r['source']} | **Category:** {r['category']} | **Sentiment:** {r['sentiment']}")
                    st.write(r.get("snippet", "")[:300])
                    if r.get("link"):
                        st.markdown(f"[Read more]({r['link']})")
        else:
            st.info("No results. Index articles first via pipeline.")

# --- Tab 11: Ask NewsPulse ---
with tabs[10]:
    st.subheader("Ask NewsPulse")
    question = st.text_input("Your question", placeholder="e.g., 'Show negative news about Tesla in last 7 days'")
    if question:
        with st.spinner("Querying..."):
            results = query_articles(filtered, question)
        if results:
            r = results[0]
            st.info(r["answer"])
            for a in r.get("articles", [])[:10]:
                with st.expander(f"{a['title']} ({a['source']}, {a['sentiment']})"):
                    st.write(f"**Published:** {a.get('published', '')}")
                    st.write(f"**Summary:** {a.get('summary', '')}")
                    st.json(a.get("entities", {}))
                    st.metric("Virality", a.get("virality", "N/A"))

# --- Tab 12: Data ---
with tabs[11]:
    cols = [c for c in filtered.columns if c not in ("text", "full_text", "entities")]
    st.dataframe(filtered[cols].head(100), use_container_width=True)
    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "news_data.csv", "text/csv")
