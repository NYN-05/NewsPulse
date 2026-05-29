"""
Automated Intelligence Briefing Generator — Phase 4.

Produces structured intelligence briefings from pipeline outputs:
- Executive summaries with key cross-domain developments
- Sector-by-sector situation reports
- Forward-looking watch items and predictions
- Configurable briefing format (daily/weekly/alert-triggered)
"""

import json
import logging
import numpy as np
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from config.settings import get, atomic_write_json, path_for

logger = logging.getLogger(__name__)


def _build_sector_situation(sector: str, links: List[Dict], sector_map: Dict) -> Dict:
    sector_entities = {k: v for k, v in sector_map.items() if v.get("sector") == sector}
    relevant_links = [l for l in links
                      if l["source_sector"] == sector or l["target_sector"] == sector]
    if not relevant_links:
        return {"sector": sector, "active_entities": len(sector_entities), "status": "stable"}

    avg_conf = float(np.mean([l.get("confidence", 0) for l in relevant_links])) if relevant_links else 0
    total_cooc = sum(l["cooccurrence_count"] for l in relevant_links)
    high_conf = sum(1 for l in relevant_links if l.get("confidence", 0) >= 0.7)

    tgt_sectors = Counter()
    for l in relevant_links:
        other = l["target_sector"] if l["source_sector"] == sector else l["source_sector"]
        tgt_sectors[other] += 1

    status = "active" if avg_conf > 0.6 or high_conf > 3 else "monitoring"

    return {
        "sector": sector,
        "active_entities": len(sector_entities),
        "cross_domain_links": len(relevant_links),
        "avg_confidence": round(avg_conf, 3),
        "high_confidence_links": high_conf,
        "total_cooccurrences": total_cooc,
        "primary_cross_domain_targets": [{"sector": s, "link_count": c}
                                          for s, c in tgt_sectors.most_common(3)],
        "status": status,
    }


def _build_executive_summary(sector_maps: List[Dict], links: List[Dict],
                              agent_result: Dict) -> str:
    active_sectors = [s for s in sector_maps if s.get("status") == "active"]
    total_high_conf = sum(1 for l in links if l.get("confidence", 0) >= 0.7)
    total_verified = sum(1 for l in links if l.get("verified"))
    total_links = len(links)

    briefing = agent_result.get("summarizer", {}).get("briefing", "")
    if briefing:
        return briefing

    return (
        f"Intelligence assessment covering {len(links)} cross-domain relationships "
        f"across {len(active_sectors)} active sectors. "
        f"{total_high_conf} high-confidence connections identified, "
        f"{total_verified} LLM-verified. "
        f"Primary intelligence activity detected in: "
        f"{', '.join(s['sector'] for s in active_sectors[:4])}."
    )


def _build_watch_items(links: List[Dict], anomalies: List[Dict],
                       transitions: List[Dict]) -> List[Dict]:
    watch_items = []

    emerging_links = [l for l in links
                      if l.get("confidence", 0) < 0.5 and l["cooccurrence_count"] >= 3]
    for l in emerging_links[:5]:
        watch_items.append({
            "type": "emerging_connection",
            "description": f"{l['source_entity']} ({l['source_sector']}) <-> "
                           f"{l['target_entity']} ({l['target_sector']})",
            "priority": "medium",
        })

    for a in anomalies[:5]:
        watch_items.append({
            "type": "velocity_anomaly",
            "description": f"{a['entity']} exhibiting {a['anomaly_type']} "
                           f"(z-score: {a.get('z_score', '?')})",
            "priority": "high",
        })

    for t in transitions[:5]:
        watch_items.append({
            "type": "phase_transition",
            "description": f"{t['entity']}: {t['current_phase']} -> {t['predicted_phase']}",
            "priority": "high" if t.get("confidence", 0) > 0.7 else "medium",
        })

    watch_items.sort(key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x["priority"], 3))
    return watch_items[:20]


def _build_predictions(links: List[Dict], transitions: List[Dict]) -> List[Dict]:
    predictions = []

    for l in links:
        if l.get("impact_prediction") and l.get("impact", {}).get("likelihood", 0) > 0.5:
            predictions.append({
                "entity_pair": f"{l['source_entity']} <-> {l['target_entity']}",
                "prediction": l.get("impact_prediction", "Unknown impact"),
                "likelihood": l.get("impact", {}).get("likelihood", 0),
                "timeframe": l.get("impact", {}).get("timeframe", "medium"),
                "sectors": [l["source_sector"], l["target_sector"]],
            })

    for t in transitions[:5]:
        predictions.append({
            "entity": t["entity"],
            "prediction": f"Transition from {t['current_phase']} to {t['predicted_phase']}",
            "likelihood": t.get("confidence", 0),
            "timeframe": "short",
            "reason": t.get("reason", ""),
        })

    predictions.sort(key=lambda x: -x["likelihood"])
    return predictions[:20]


def generate_briefing(
    cross_domain_links: List[Dict],
    sector_map: Dict,
    impact_chains: List[Dict],
    agent_result: Dict,
    anomalies: List[Dict] = None,
    transitions: List[Dict] = None,
    narrative_summary: Dict = None,
    brief_type: str = "standard",
) -> Dict:
    logger.info("Generating intelligence briefing (type=%s)...", brief_type)

    sectors_list = list(set(
        [l["source_sector"] for l in cross_domain_links] +
        [l["target_sector"] for l in cross_domain_links]
    ))
    sector_situations = [_build_sector_situation(s, cross_domain_links, sector_map)
                         for s in sectors_list]
    sector_situations.sort(key=lambda x: -x.get("cross_domain_links", 0))

    executive_summary = _build_executive_summary(sector_situations, cross_domain_links, agent_result)
    watch_items = _build_watch_items(cross_domain_links, anomalies or [], transitions or [])
    predictions = _build_predictions(cross_domain_links, transitions or [])

    top_links = sorted(cross_domain_links, key=lambda x: -x.get("confidence", 0))[:5]
    key_connections = [
        {
            "source": l["source_entity"],
            "target": l["target_entity"],
            "source_sector": l["source_sector"],
            "target_sector": l["target_sector"],
            "confidence": l.get("confidence", 0),
            "causal_mechanism": l.get("causal_mechanism", ""),
            "impact": l.get("impact", {}).get("predicted_effect", ""),
        }
        for l in top_links
    ]

    total_confidence = float(np.mean([l.get("confidence", 0)
                                       for l in cross_domain_links])) if cross_domain_links else 0
    overall_confidence = (
        "high" if total_confidence >= 0.6 else
        "medium" if total_confidence >= 0.4 else "low"
    )

    briefing = {
        "title": f"Cross-Domain Intelligence Briefing — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "type": brief_type,
        "generated_at": datetime.now().isoformat(),
        "executive_summary": executive_summary,
        "overall_confidence": overall_confidence,
        "sector_situations": sector_situations,
        "key_connections": key_connections,
        "watch_items": watch_items,
        "predictions": predictions,
        "statistics": {
            "total_links": len(cross_domain_links),
            "total_chains": len(impact_chains),
            "active_sectors": len([s for s in sector_situations if s["status"] == "active"]),
            "high_confidence_links": sum(1 for l in cross_domain_links
                                         if l.get("confidence", 0) >= 0.7),
            "llm_verified_links": sum(1 for l in cross_domain_links if l.get("verified")),
            "watch_items_count": len(watch_items),
            "predictions_count": len(predictions),
        },
        "analyst_findings": agent_result.get("analyst", {}).get("findings", []),
        "agent_assessment": agent_result.get("critic", {}).get("overall_quality", "unknown"),
    }

    import os
    atomic_write_json(os.path.join(path_for("output_dir"), "intelligence_briefing.json"), briefing)
    logger.info("Saved: intelligence_briefing.json")
    return briefing
