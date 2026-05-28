import os
import logging
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import MiniBatchKMeans
from sklearn.decomposition import PCA
from config.settings import get, path_for
from compute.gpu_manager import is_cuda, has_sentence_transformers
from compute.embeddings import encode_texts
from compute.clustering_gpu import kmeans_gpu

logger = logging.getLogger(__name__)


def cluster_articles(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "text" not in df.columns:
        logger.warning("No text data for clustering")
        return df

    texts = df["text"].fillna("").tolist()
    if len(texts) < 5:
        logger.warning("Too few articles for clustering (< 5)")
        return df

    models_dir = path_for("models_dir")
    os.makedirs(models_dir, exist_ok=True)

    n_clusters = min(
        get("clustering.n_clusters", 8),
        max(get("clustering.min_clusters", 2), len(texts) // get("clustering.articles_per_cluster", 5)),
    )

    gpu_embeddings = None
    if is_cuda() and has_sentence_transformers():
        logger.info("Using GPU sentence-transformers embeddings")
        gpu_embeddings = encode_texts(texts)

    if gpu_embeddings is not None:
        logger.info("Using GPU KMeans on dense embeddings")
        clusters, centroids = kmeans_gpu(gpu_embeddings, n_clusters, random_state=get("clustering.random_state", 42))
        df["cluster"] = clusters
        terms = [f"dim_{i}" for i in range(gpu_embeddings.shape[1])]
        cluster_labels = {}
        for i in range(n_clusters):
            mask = clusters == i
            if mask.sum() > 0:
                center = gpu_embeddings[mask].mean(axis=0)
                top_idx = np.argsort(center)[-5:][::-1]
                cluster_labels[i] = ", ".join(terms[j] for j in top_idx)
            else:
                cluster_labels[i] = "empty"
        df["cluster_label"] = df["cluster"].map(cluster_labels)
        logger.info("GPU clustered %d articles into %d groups", len(df), n_clusters)
        _plot_clusters_dense(gpu_embeddings, clusters, n_clusters)
        return df

    vec_path = os.path.join(models_dir, "tfidf_vectorizer.joblib")
    km_path = os.path.join(models_dir, "kmeans_model.joblib")

    if os.path.exists(vec_path) and os.path.exists(km_path):
        logger.info("Loading pre-trained vectorizer and model")
        vec = joblib.load(vec_path)
        X = vec.transform(texts)
        km = joblib.load(km_path)
    else:
        logger.info("Training new TF-IDF vectorizer and MiniBatchKMeans (CPU)")
        vec = TfidfVectorizer(
            max_features=get("clustering.max_features", 500),
            stop_words="english",
        )
        X = vec.fit_transform(texts)
        km = MiniBatchKMeans(
            n_clusters=n_clusters,
            random_state=get("clustering.random_state", 42),
            batch_size=256,
            n_init="auto",
        )
        km.fit(X)
        joblib.dump(vec, vec_path)
        joblib.dump(km, km_path)

    clusters = km.predict(X)
    df["cluster"] = clusters
    terms = vec.get_feature_names_out()
    cluster_labels = {}
    for i in range(km.n_clusters):
        centroid = km.cluster_centers_[i]
        top_idx = centroid.argsort()[-5:][::-1]
        cluster_labels[i] = ", ".join(terms[j] for j in top_idx)
    df["cluster_label"] = df["cluster"].map(cluster_labels)
    logger.info("Clustered %d articles into %d groups", len(df), km.n_clusters)
    _plot_clusters_sparse(X, clusters, km.n_clusters)
    return df


def _plot_clusters_dense(embeddings, clusters, n_clusters, title="Article Clusters (GPU embeddings)"):
    try:
        from sklearn.decomposition import PCA
        pca = PCA(n_components=2, random_state=get("clustering.random_state", 42))
        coords = pca.fit_transform(embeddings)
        plt.figure(figsize=(10, 6))
        scatter = plt.scatter(coords[:, 0], coords[:, 1], c=clusters, cmap="tab10", alpha=0.7)
        plt.colorbar(scatter, label="Cluster")
        plt.title(title)
        plt.tight_layout()
        out_path = os.path.join(path_for("plots_dir"), "clusters.png")
        plt.savefig(out_path, dpi=120)
        plt.close()
        logger.info("Saved cluster plot to %s", out_path)
    except Exception as e:
        logger.warning("Failed to generate cluster plot: %s", e)


def _plot_clusters_sparse(X, clusters, n_clusters):
    try:
        pca = PCA(n_components=2, random_state=get("clustering.random_state", 42))
        coords = pca.fit_transform(X.toarray() if hasattr(X, "toarray") else X)
        plt.figure(figsize=(10, 6))
        scatter = plt.scatter(coords[:, 0], coords[:, 1], c=clusters, cmap="tab10", alpha=0.7)
        plt.colorbar(scatter, label="Cluster")
        plt.title("Article Clusters (PCA projection)")
        plt.tight_layout()
        out_path = os.path.join(path_for("plots_dir"), "clusters.png")
        plt.savefig(out_path, dpi=120)
        plt.close()
        logger.info("Saved cluster plot to %s", out_path)
    except Exception as e:
        logger.warning("Failed to generate cluster plot: %s", e)
