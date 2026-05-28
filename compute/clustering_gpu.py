import logging
import numpy as np
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


def kmeans_gpu(X: np.ndarray, n_clusters: int, random_state: int = 42, max_iter: int = 300) -> Tuple[np.ndarray, np.ndarray]:
    try:
        import torch
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        X_t = torch.tensor(X, dtype=torch.float32, device=device)
        n_samples, n_features = X_t.shape
        rng = torch.Generator(device=device).manual_seed(random_state)
        idx = torch.randperm(n_samples, generator=rng, device=device)[:n_clusters]
        centroids = X_t[idx].clone()
        prev_labels = torch.zeros(n_samples, dtype=torch.long, device=device)
        for _ in range(max_iter):
            dists = torch.cdist(X_t, centroids)
            labels = torch.argmin(dists, dim=1)
            if torch.equal(labels, prev_labels):
                break
            prev_labels = labels.clone()
            for k in range(n_clusters):
                mask = labels == k
                if mask.sum() > 0:
                    centroids[k] = X_t[mask].mean(dim=0)
        return labels.cpu().numpy(), centroids.cpu().numpy()
    except Exception as e:
        logger.warning("GPU KMeans failed (%s), falling back to sklearn", e)
        from sklearn.cluster import MiniBatchKMeans
        km = MiniBatchKMeans(n_clusters=n_clusters, random_state=random_state, batch_size=256, n_init="auto")
        labels = km.fit_predict(X)
        return labels, km.cluster_centers_
