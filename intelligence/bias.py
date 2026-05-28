import re
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict

logger = logging.getLogger(__name__)

LEFT_LEANING_TERMS = {
    "progressive", "social justice", "equity", "systemic racism", "marginalized",
    "underserved", "climate crisis", "living wage", "universal healthcare",
    "reparations", "defund", "diversity", "inclusion", "privilege",
    "intersectionality", "ally", "cisgender", "nonbinary", "gender identity",
    "white privilege", "critical race", "police brutality", "racial justice",
    "reproductive justice", "environmental justice",
}

RIGHT_LEANING_TERMS = {
    "patriot", "freedom", "constitutional", "traditional values", "small government",
    "tax cuts", "deregulation", "religious freedom", "second amendment",
    "border security", "law and order", "family values", "sovereignty",
    "limited government", "free market", "individual liberty", "nationalism",
    "america first", "drain the swamp", "deep state", "cancel culture",
    "woke agenda", "political correctness", "illegal aliens",
}

EMOTIONALLY_CHARGED = {
    "outrage", "disgusting", "appalling", "shameful", "travesty", "disgrace",
    "heroic", "brave", "courageous", "treason", "traitor", "evil", "corrupt",
    "hypocrite", "fraud", "scandal", "cover-up", "conspiracy", "tyranny",
    "oppression", "injustice", "betrayal", "savage", "devastating",
    "catastrophic", "unprecedented", "historic",
}

CLICKBAIT_PATTERNS = [
    r"you won't believe",
    r"shocked to see",
    r"what happens next",
    r"will blow your mind",
    r"the truth about",
    r"they don't want you to know",
    r"here's why",
    r"this is why",
    r"number \d+ will",
    r"must see",
    r"can't handle the truth",
    r"one weird trick",
    r"doctors hate",
    r"what happened next",
    r"left speechless",
    r"in tears after",
    r"absolutely terrified",
]


def analyze_bias(text: str) -> Dict:
    if not isinstance(text, str) or not text.strip():
        return {"political_leaning": "neutral", "emotional_score": 0.0, "clickbait_score": 0.0}

    lower = text.lower()
    words = set(re.findall(r"\w+", lower))

    left_count = sum(1 for term in LEFT_LEANING_TERMS if term in lower)
    right_count = sum(1 for term in RIGHT_LEANING_TERMS if term in lower)
    emotional_count = sum(1 for term in EMOTIONALLY_CHARGED if term in lower)

    total_words = max(len(words), 1)
    left_score = left_count / total_words
    right_score = right_count / total_words
    emotional_score = emotional_count / total_words

    if left_score > right_score * 2:
        leaning = "left"
    elif right_score > left_score * 2:
        leaning = "right"
    else:
        leaning = "neutral"

    clickbait_matches = 0
    for pat in CLICKBAIT_PATTERNS:
        if re.search(pat, lower):
            clickbait_matches += 1
    clickbait_score = min(clickbait_matches / 5, 1.0)

    return {
        "political_leaning": leaning,
        "left_score": round(left_score, 4),
        "right_score": round(right_score, 4),
        "emotional_score": round(emotional_score, 4),
        "clickbait_score": round(clickbait_score, 4),
        "bias_intensity": round(max(left_score, right_score) * 100, 2),
    }


def compute_source_reliability(df: pd.DataFrame) -> Dict:
    if df.empty or "source" not in df.columns:
        return {}

    source_stats = {}
    for source, group in df.groupby("source"):
        group = group.reset_index(drop=True)
        total = len(group)
        if total < 2:
            continue

        sens_mean = group["sensationalism_score"].mean() if "sensationalism_score" in group.columns else 0
        clickbait_mean = 0
        emotional_mean = 0
        bias_scores = []

        if "text" in group.columns:
            for text in group["text"].fillna(""):
                bias = analyze_bias(text)
                clickbait_mean += bias["clickbait_score"]
                emotional_mean += bias["emotional_score"]
                bias_scores.append(bias["bias_intensity"])

            clickbait_mean /= max(total, 1)
            emotional_mean /= max(total, 1)

        reliability = max(0, 100 - (sens_mean * 200) - (clickbait_mean * 100) - (emotional_mean * 50))
        reliability = round(min(reliability, 100), 1)

        source_stats[source] = {
            "total_articles": total,
            "reliability_score": reliability,
            "sensationalism_mean": round(sens_mean, 4),
            "clickbait_mean": round(clickbait_mean, 4),
            "emotional_mean": round(emotional_mean, 4),
            "avg_bias_intensity": round(np.mean(bias_scores), 2) if bias_scores else 0,
        }

    return dict(sorted(source_stats.items(), key=lambda x: -x[1]["reliability_score"]))
