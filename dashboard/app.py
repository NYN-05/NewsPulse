import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from storage.manager import DataManager
from config.settings import load_config, get

load_config()
plt.rcParams["figure.dpi"] = 120

st.set_page_config(page_title=get("dashboard.title", "News Pipeline Dashboard"), layout="wide")
st.title(get("dashboard.title", "News Pipeline Dashboard"))

data_mgr = DataManager()
df = data_mgr.load_analyzed()

if df.empty:
    st.error("Run the analysis pipeline first!")
    st.stop()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Articles", len(df))
col2.metric("Avg Sentiment", f"{df['compound'].mean():.3f}")
col3.metric("Avg Sensationalism", f"{df['sensationalism_score'].mean():.3f}")
col4.metric("Avg Subjectivity", f"{df['subjectivity'].mean():.3f}")

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Sentiment", "Categories", "Sensationalism", "Clusters", "Data"])

with tab1:
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    df["sentiment"].value_counts().plot(kind="pie", ax=ax1, autopct="%1.1f%%", ylabel="")
    ax1.set_title("Sentiment Distribution")
    df["compound"].hist(bins=20, ax=ax2, edgecolor="black")
    ax2.set_title("Compound Score Distribution")
    ax2.set_xlabel("Compound Score")
    st.pyplot(fig)

with tab2:
    if "category" in df.columns:
        cats = df["category"].fillna("Uncategorized").value_counts().head(20)
        fig, ax = plt.subplots(figsize=(10, 5))
        cats.plot(kind="barh", ax=ax)
        ax.set_title("Top Categories")
        ax.set_xlabel("Count")
        st.pyplot(fig)
    else:
        st.info("No category data")

with tab3:
    top = df.nlargest(20, "sensationalism_score")
    fig, ax = plt.subplots(figsize=(10, 5))
    titles = [t[:50] for t in (top.get("clean_title") if "clean_title" in top.columns else top["title"])]
    colors = ["red" if s == "negative" else "green" if s == "positive" else "gray" for s in top["sentiment"]]
    ax.barh(range(len(top)), top["sensationalism_score"], color=colors)
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(titles, fontsize=8)
    ax.set_xlabel("Sensationalism Score")
    ax.set_title("Most Sensational Headlines")
    st.pyplot(fig)

with tab4:
    if "cluster" in df.columns and "cluster_label" in df.columns:
        clusters = df.groupby("cluster_label").size().sort_values(ascending=False)
        fig, ax = plt.subplots(figsize=(10, 4))
        clusters.plot(kind="bar", ax=ax)
        ax.set_title("Article Clusters")
        ax.set_xlabel("")
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig)
    else:
        st.info("Run clustering first")

with tab5:
    cols = [c for c in df.columns if c not in ("text", "full_text", "entities")]
    st.dataframe(df[cols].head(100), use_container_width=True)
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("Download CSV", csv, "news_data.csv", "text/csv")
