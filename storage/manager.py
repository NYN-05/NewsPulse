import os
import pandas as pd
import logging
from typing import Optional
from config.settings import path_for, get

logger = logging.getLogger(__name__)


class DataManager:
    def __init__(self):
        self._df_raw: Optional[pd.DataFrame] = None
        self._df_analyzed: Optional[pd.DataFrame] = None
        self._analyzed_path = path_for("analyzed_parquet")
        self._analyzed_csv_fallback = path_for("analyzed_csv")
        self._raw_csv = path_for("news_csv")

    def load_raw(self, force_reload: bool = False) -> pd.DataFrame:
        if self._df_raw is not None and not force_reload:
            return self._df_raw
        path = self._raw_csv
        if os.path.exists(path):
            logger.info("Loading raw data from %s", path)
            self._df_raw = pd.read_csv(path)
        else:
            logger.warning("Raw data file not found: %s", path)
            self._df_raw = pd.DataFrame()
        return self._df_raw

    def save_raw(self, df: pd.DataFrame):
        path = self._raw_csv
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        df.to_csv(path, index=False)
        self._df_raw = df
        logger.info("Saved %d rows to %s", len(df), path)

    def load_analyzed(self, force_reload: bool = False) -> pd.DataFrame:
        if self._df_analyzed is not None and not force_reload:
            return self._df_analyzed
        parquet_path = self._analyzed_path
        csv_path = self._analyzed_csv_fallback

        if os.path.exists(parquet_path):
            logger.info("Loading analyzed data from %s", parquet_path)
            self._df_analyzed = pd.read_parquet(parquet_path)
        elif os.path.exists(csv_path):
            logger.info("Loading analyzed data from %s (CSV fallback)", csv_path)
            self._df_analyzed = pd.read_csv(csv_path)
        else:
            logger.warning("No analyzed data file found")
            self._df_analyzed = pd.DataFrame()
        return self._df_analyzed

    def save_analyzed(self, df: pd.DataFrame):
        parquet_path = self._analyzed_path
        csv_path = self._analyzed_csv_fallback

        os.makedirs(os.path.dirname(parquet_path) or ".", exist_ok=True)
        try:
            df.to_parquet(parquet_path, index=False)
            logger.info("Saved %d rows to %s", len(df), parquet_path)
        except Exception as e:
            logger.warning("Parquet save failed (%s), falling back to CSV", e)
            df.to_csv(csv_path, index=False)
            logger.info("Saved %d rows to %s", len(df), csv_path)
        self._df_analyzed = df

    def merge_new_articles(self, new_articles: list) -> pd.DataFrame:
        df_new = pd.DataFrame(new_articles)
        if df_new.empty:
            return self.load_raw()

        df_old = self.load_raw()
        if df_old.empty:
            self.save_raw(df_new)
            return df_new

        existing_keys = set()
        if not df_old.empty:
            titles = df_old["title"].fillna("").astype(str).str.strip().str.lower()
            sources = df_old["source"].fillna("").astype(str).str.strip()
            links = df_old["link"].fillna("").astype(str).str.strip()
            existing_keys = set(zip(titles, sources, links))

        cols = df_new.columns.tolist()
        rows = []
        for a in df_new.itertuples():
            key = (
                str(getattr(a, "title", "")).strip().lower(),
                str(getattr(a, "source", "")).strip(),
                str(getattr(a, "link", "")).strip(),
            )
            if key not in existing_keys:
                existing_keys.add(key)
                rows.append({col: getattr(a, col, None) for col in cols})

        if not rows:
            logger.info("No new articles to add")
            return df_old

        df_combined = pd.concat([df_old, pd.DataFrame(rows)], ignore_index=True)
        self.save_raw(df_combined)
        return df_combined

    def drop_redundant_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        cols_to_drop = []
        keep_cols = get("storage.keep_columns", [])
        if keep_cols is None:
            keep_cols = []
        for col in df.columns:
            if col not in keep_cols and col.endswith("_tmp"):
                cols_to_drop.append(col)
        if cols_to_drop:
            df = df.drop(columns=cols_to_drop)
        for col in df.select_dtypes(include=["object"]).columns:
            if df[col].nunique() / max(len(df), 1) < 0.05 and df[col].nunique() < 50:
                df[col] = df[col].astype("category")
        return df

    def get_existing_keys(self, df: pd.DataFrame) -> set:
        if df.empty:
            return set()
        titles = df["title"].fillna("").astype(str).str.strip().str.lower()
        links = df["link"].fillna("").astype(str).str.strip()
        sources = df["source"].fillna("").astype(str).str.strip() if "source" in df.columns else ""
        return set(zip(titles, links, sources))
