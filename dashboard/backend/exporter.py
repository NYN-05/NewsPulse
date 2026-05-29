"""
Intelligence Export Engine — Phase 5.

Exports intelligence data in multiple formats:
- JSON: full structured data
- CSV: tabular relationship summaries
- PDF: formatted intelligence report
- Markdown: readable briefing document
"""

import csv
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from config.settings import get, atomic_read_json, path_for

logger = logging.getLogger("exporter")


def export_json(output_path: str) -> str:
    """Aggregate all intelligence outputs into a single JSON export."""
    base = path_for("output_dir")
    files = {
        "cross_domain_links": "cross_domain_links.json",
        "impact_chains": "impact_chains.json",
        "sector_map": "sector_map.json",
        "alerts": "alerts.json",
        "multi_agent_analysis": "multi_agent_analysis.json",
        "temporal_patterns": "temporal_patterns.json",
        "intelligence_briefing": "intelligence_briefing.json",
        "causal_analysis": "causal_analysis.json",
        "narrative_evolution": "narrative_evolution.json",
    }

    export = {
        "exported_at": datetime.now().isoformat(),
        "version": "2.0",
    }

    for key, filename in files.items():
        path = os.path.join(base, filename)
        data = atomic_read_json(path)
        if data is not None:
            export[key] = data

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(export, f, indent=2)
    logger.info("JSON export written to %s", output_path)
    return output_path


def export_csv(output_path: str) -> str:
    """Export cross-domain relationships as CSV."""
    base = path_for("output_dir")
    links = atomic_read_json(os.path.join(base, "cross_domain_links.json"))
    if not isinstance(links, list):
        links = []

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Source Entity", "Source Sector", "Target Entity", "Target Sector",
            "Co-occurrences", "Source Diversity", "Strength", "Confidence",
            "Verified", "Causal Direction", "Impact Prediction",
        ])
        for l in links:
            writer.writerow([
                l.get("source_entity", ""),
                l.get("source_sector", ""),
                l.get("target_entity", ""),
                l.get("target_sector", ""),
                l.get("cooccurrence_count", 0),
                l.get("source_diversity", 0),
                l.get("strength", 0),
                l.get("confidence", ""),
                l.get("verified", ""),
                l.get("causal_direction", ""),
                l.get("impact_prediction", ""),
            ])
    logger.info("CSV export written to %s (%d rows)", output_path, len(links))
    return output_path


def export_markdown(output_path: str) -> str:
    """Export intelligence briefing as Markdown."""
    base = path_for("output_dir")
    briefing = atomic_read_json(os.path.join(base, "intelligence_briefing.json"))
    if not briefing:
        briefing = {}

    lines = []
    lines.append(f"# {briefing.get('title', 'Intelligence Briefing')}")
    lines.append(f"*Generated: {briefing.get('generated_at', '')}*")
    lines.append(f"**Overall Confidence: {briefing.get('overall_confidence', 'N/A')}**")
    lines.append("")

    summary = briefing.get("executive_summary", "")
    if summary:
        lines.append("## Executive Summary")
        lines.append(summary)
        lines.append("")

    stats = briefing.get("statistics", {})
    if stats:
        lines.append("## Statistics")
        for k, v in stats.items():
            lines.append(f"- **{k}**: {v}")
        lines.append("")

    sectors = briefing.get("sector_situations", [])
    if sectors:
        lines.append("## Sector Situations")
        for s in sectors:
            lines.append(f"### {s['sector'].title()}")
            lines.append(f"- Status: {s['status']}")
            lines.append(f"- Active Entities: {s['active_entities']}")
            lines.append(f"- Cross-Domain Links: {s['cross_domain_links']}")
            lines.append(f"- Avg Confidence: {s['avg_confidence']}")
            lines.append("")

    connections = briefing.get("key_connections", [])
    if connections:
        lines.append("## Key Connections")
        for c in connections:
            lines.append(f"- **{c['source']}** ({c['source_sector']}) ↔ "
                         f"**{c['target']}** ({c['target_sector']}) — "
                         f"Confidence: {c.get('confidence', 0):.2f}")
            if c.get("causal_mechanism"):
                lines.append(f"  - Causal: {c['causal_mechanism']}")
        lines.append("")

    watch = briefing.get("watch_items", [])
    if watch:
        lines.append("## Watch Items")
        for w in watch:
            lines.append(f"- [{w['priority'].upper()}] {w['description']}")
        lines.append("")

    predictions = briefing.get("predictions", [])
    if predictions:
        lines.append("## Predictions")
        for p in predictions:
            lines.append(f"- **{p.get('prediction', '')}** "
                         f"(Likelihood: {p.get('likelihood', 0):.0%}, "
                         f"Timeframe: {p.get('timeframe', 'medium')})")
        lines.append("")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(lines))
    logger.info("Markdown briefing written to %s", output_path)
    return output_path
