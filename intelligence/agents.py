"""
Multi-Agent Intelligence Analysis — Phase 4.

A pipeline of specialized AI agents that collaboratively analyze intelligence:
1. Analyst Agent — extracts key findings and patterns
2. Critic Agent — challenges assumptions and identifies gaps
3. Summarizer Agent — produces concise intelligence summaries
"""

import json
import logging
import numpy as np
from collections import Counter
from typing import Dict, List, Optional
from datetime import datetime
from config.settings import get

logger = logging.getLogger(__name__)


def _ollama_generate(prompt: str, system: str = "", model: str = None) -> Optional[str]:
    try:
        import requests
    except ImportError:
        return None
    model = model or get("intelligence.llm_model", "qwen3:14b")
    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "system": system or "",
                "stream": False,
                "options": {"num_predict": 512},
            },
            timeout=60,
        )
        if not resp.ok:
            return None
        return resp.json().get("response", "")
    except Exception as e:
        logger.debug("Ollama call failed: %s", e)
        return None


def analyst_agent(cross_domain_links: List[Dict], impact_chains: List[Dict]) -> Dict:
    logger.info("Analyst Agent running...")
    if not cross_domain_links:
        return {"findings": [], "summary": "No cross-domain links to analyze"}

    top_links = sorted(cross_domain_links, key=lambda x: -x.get("confidence", 0))[:10]
    top_chains = sorted(impact_chains, key=lambda x: -x.get("cross_domain_hops", 0))[:5]

    link_summary = "\n".join(
        f"  - {l['source_entity']} ({l['source_sector']}) <-> "
        f"{l['target_entity']} ({l['target_sector']}) [conf={l.get('confidence', 0):.2f}, "
        f"cooc={l['cooccurrence_count']}]"
        for l in top_links
    )
    chain_summary = "\n".join(
        f"  - {' -> '.join(c['sectors'])} ({c['cross_domain_hops']} hops, weight={c.get('total_weight', 0)})"
        for c in top_chains
    )

    prompt = (
        f"Analyze the following intelligence data and produce key findings.\n\n"
        f"Top Cross-Domain Relationships:\n{link_summary}\n\n"
        f"Top Impact Chains:\n{chain_summary}\n\n"
        f"Provide 3-5 key intelligence findings. For each: name the entities/sectors involved, "
        f"describe the relationship, and rate significance (high/medium/low).\n"
        f"Respond in JSON:\n"
        f'{{"findings": [{{"title": "...", "description": "...", "significance": "high/medium/low", '
        f'"entities": ["entity1", "entity2"], "sectors": ["sector1", "sector2"]}}], '
        f'"overall_assessment": "one sentence summary"}}'
    )

    response = _ollama_generate(prompt)
    if response:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Analyst agent returned unparseable JSON: %s", response[:100])

    return {
        "findings": [
            {
                "title": f"Cross-domain activity: {l['source_sector']}-{l['target_sector']}",
                "description": (
                    f"{l['source_entity']} and {l['target_entity']} show "
                    f"{l['cooccurrence_count']} co-occurrences across "
                    f"{l['source_diversity']} sources."
                ),
                "significance": "high" if l.get("confidence", 0) > 0.7 else "medium",
                "entities": [l["source_entity"], l["target_entity"]],
                "sectors": [l["source_sector"], l["target_sector"]],
            }
            for l in top_links[:3]
        ],
        "overall_assessment": f"Analysis of {len(cross_domain_links)} cross-domain relationships "
                              f"across {len(impact_chains)} impact chains.",
    }


def critic_agent(findings: List[Dict], cross_domain_links: List[Dict]) -> Dict:
    logger.info("Critic Agent running...")
    if not findings:
        return {"critiques": [], "confidence_gaps": [], "overall_quality": "unknown"}

    findings_text = json.dumps(findings, indent=2)
    link_count = len(cross_domain_links)
    verified_count = sum(1 for l in cross_domain_links if l.get("verified"))
    confs = [l.get("confidence", 0) for l in cross_domain_links if l.get("confidence")]
    avg_conf = float(np.mean(confs)) if confs else 0

    prompt = (
        f"Review the following intelligence findings critically.\n"
        f"Dataset has {link_count} relationships ({verified_count} verified, avg confidence {avg_conf:.2f}).\n\n"
        f"Findings:\n{findings_text}\n\n"
        f"Identify: 1) What assumptions are being made? 2) What evidence is missing? "
        f"3) What alternative explanations exist? 4) Rate the overall quality (high/medium/low).\n"
        f"Respond in JSON:\n"
        f'{{"critiques": [{{"finding_index": 0, "issue": "...", "severity": "high/medium/low"}}], '
        f'"confidence_gaps": ["gap1", "gap2"], "overall_quality": "high/medium/low"}}'
    )

    response = _ollama_generate(prompt)
    if response:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Critic agent returned unparseable JSON")

    return {
        "critiques": [{
            "finding_index": i,
            "issue": "Finding based on correlation, not proven causation",
            "severity": "medium",
        } for i in range(len(findings))],
        "confidence_gaps": [f"Only {verified_count}/{link_count} relationships LLM-verified"],
        "overall_quality": "medium" if avg_conf > 0.5 else "low",
    }


def summarizer_agent(findings: List[Dict], critiques: Dict) -> Dict:
    logger.info("Summarizer Agent running...")
    findings_text = json.dumps(findings, indent=2)
    critiques_text = json.dumps(critiques, indent=2)

    prompt = (
        f"Produce a concise intelligence briefing from these findings and critiques.\n\n"
        f"Findings:\n{findings_text}\n\n"
        f"Critiques:\n{critiques_text}\n\n"
        f"Write a 3-paragraph intelligence briefing covering: "
        f"1) Key developments 2) Confidence assessment 3) Watch items.\n"
        f"Respond in JSON:\n"
        f'{{"briefing": "3 paragraph briefing text", '
        f'"key_developments": ["dev1", "dev2", "dev3"], '
        f'"confidence": "high/medium/low", '
        f'"watch_items": ["item1", "item2"]}}'
    )

    response = _ollama_generate(prompt)
    if response:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            logger.warning("Summarizer agent returned unparseable JSON")

    developments = [f.get("title", "Unknown finding") for f in findings[:3]]
    return {
        "briefing": (
            f"Analysis of {len(findings)} intelligence findings. "
            f"Key sectors: {', '.join(set(s for f in findings for s in f.get('sectors', [])))}. "
            f"Confidence quality: {critiques.get('overall_quality', 'medium')}."
        ),
        "key_developments": developments,
        "confidence": critiques.get("overall_quality", "medium"),
        "watch_items": critiques.get("confidence_gaps", [])[:2],
    }


def multi_agent_pipeline(cross_domain_links: List[Dict], impact_chains: List[Dict]) -> Dict:
    logger.info("=" * 60)
    logger.info("PHASE 4 — MULTI-AGENT INTELLIGENCE ANALYSIS")
    logger.info("(Analyst → Critic → Summarizer)")
    logger.info("=" * 60)

    findings_result = analyst_agent(cross_domain_links, impact_chains)
    findings = findings_result.get("findings", [])

    logger.info("Analyst: %d findings produced", len(findings))

    critiques_result = critic_agent(findings, cross_domain_links)
    logger.info("Critic: %d critiques, quality=%s",
                len(critiques_result.get("critiques", [])),
                critiques_result.get("overall_quality", "unknown"))

    summary_result = summarizer_agent(findings, critiques_result)
    logger.info("Summarizer: briefing produced")

    result = {
        "analyst": findings_result,
        "critic": critiques_result,
        "summarizer": summary_result,
        "generated_at": datetime.now().isoformat(),
        "model": get("intelligence.llm_model", "qwen3:14b"),
    }

    return result
