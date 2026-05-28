import sys, os, json
sys.path.insert(0, ".")
from config.settings import load_config
load_config()
import pandas as pd

df = pd.read_parquet("output/data/news_analyzed.parquet")
print(f"Loaded {len(df)} articles")

from intelligence.cross_domain import cross_domain_pipeline
result = cross_domain_pipeline(df)

print("\n=== SUMMARY ===")
print(json.dumps(result["summary"], indent=2))

print("\n=== TOP 10 CROSS-DOMAIN LINKS ===")
for l in result["cross_domain_links"][:10]:
    src_s = l["source_sector"]
    tgt_s = l["target_sector"]
    print(f"  {l['source_entity']}({src_s}) <-> {l['target_entity']}({tgt_s}): "
          f"strength={l['strength']}, count={l['cooccurrence_count']}, sources={l['source_diversity']}")

print("\n=== TOP 10 IMPACT CHAINS ===")
for c in result["impact_chains"][:10]:
    chain_str = " -> ".join(c["chain"])
    sector_str = " -> ".join(c["sectors"])
    print(f"  {chain_str}")
    print(f"    Sectors: {sector_str} | hops={c['cross_domain_hops']}, weight={c['total_weight']}")
